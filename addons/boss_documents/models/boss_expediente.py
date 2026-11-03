from odoo import api, fields, models
from odoo.exceptions import UserError

from .shipment_block import scope_sentence, shipment_rows


# Incoterms whose main carriage is paid by the seller (C and D terms): the house document says freight «prepaid»; with
# the E and F terms the buyer pays it at destination: «collect». The usual reading of the Incoterms 2020, editable on
# the file (Odoo 17: field «Freight» of the B/L, chosen by hand).
PREPAID_INCOTERMS = ("CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP")
COLLECT_INCOTERMS = ("EXW", "FCA", "FAS", "FOB")


class BossExpediente(models.Model):
    _inherit = "boss.expediente"

    # House documents BOSS issues as NVOCC (F0-C45; Odoo 17: x_bill_of_lading, x_air_waybill and the Cargo Manifest of
    # the file, ADR-014): one per house file (sea: HBL, air: HAWB), the manifest on the master.
    house_doc_freight = fields.Selection(
        [("prepaid", "Prepaid"), ("collect", "Collect")], "Freight payable", compute="_compute_house_doc_freight",
        store=True, readonly=False, tracking=True,
        help="Printed on the house B/L or air waybill and the manifest. Proposed from the incoterm: C and D terms "
             "prepaid (the seller pays the main carriage), E and F terms collect (the buyer pays it).")
    house_doc_marks = fields.Text("Marks and numbers", help="Shipping marks on the packages, printed on the house B/L.")
    house_doc_issue_date = fields.Date(
        "House document issued on", copy=False, tracking=True,
        help="Set by «Issue»: until then the house B/L or air waybill prints as a DRAFT for the shipper to check.")

    def _boss_frozen_fields(self):
        return super()._boss_frozen_fields() + ("house_doc_freight", "house_doc_marks", "house_doc_issue_date")

    @api.depends("incoterm_id")
    def _compute_house_doc_freight(self):
        for file in self:
            code = file.incoterm_id.code
            file.house_doc_freight = ("prepaid" if code in PREPAID_INCOTERMS else "collect" if code in COLLECT_INCOTERMS
                                      else file.house_doc_freight)

    def _boss_document_block(self):
        """Data of the shipment block of a document of this file (ADR-011)."""
        self.ensure_one()
        order = self._boss_document_order()
        return {
            "reference": self.name,
            "customer_reference": order.client_order_ref if order else "",
            "quotation": order.name if order else "",
            "scope": scope_sentence(self),
            "columns": shipment_rows(self, "", file=self),
        }

    def _boss_document_order(self):
        """The accepted quotation of the file (the first one when several)."""
        orders = self.sale_order_ids.filtered(lambda o: o.state == "sale") or self.sale_order_ids
        return orders[:1]

    # --- transport order (OT) to the haulier (roadmap item 5) ----------------------------------------------------

    def _boss_transport_order_problems(self):
        """What stops the transport order: the haulier it goes to, and on a sea import delivered by BOSS the house B/L
        released or a sea waybill (Cristina, «Nuevo Odoo» › OPS- exptes A73: «before delivering, the operator confirms
        that the HBL is released or SWB»)."""
        self.ensure_one()
        _ = self.env._
        problems = [] if self.haulier_id else [_("choose the haulier (References and dates › Other parties)")]
        if (self.direction == "import" and self.transport_mode == "sea" and self.scope_delivery
                and self.hbl_release not in ("released", "swb")):
            problems.append(_("the house B/L is not released nor a sea waybill (References and dates)"))
        return problems

    def action_print_transport_order(self):
        """The transport order PDF for the haulier: the shipment block of the supplier documents (no customer price or
        reference), the containers and the pickup and delivery. Printed, never sent from here."""
        self.ensure_one()
        problems = self._boss_transport_order_problems()
        if problems:
            raise UserError(self.env._("No transport order for %(file)s yet: %(problems)s.", file=self.name,
                                       problems="; ".join(problems)))
        return self.env.ref("boss_documents.action_report_transport_order").report_action(self)

    # --- house B/L (sea) or house air waybill (air), and the cargo manifest (roadmap item 11) --------------------

    def _boss_house_doc_kind(self):
        """«hbl» on a sea file, «hawb» on an air file; none on a master (it travels under the carrier's own document)."""
        self.ensure_one()
        if self.consolidation_role == "master":
            return False
        return {"sea": "hbl", "air": "hawb"}.get(self.transport_mode, False)

    def _boss_house_doc_problems(self):
        """What a house document needs before it is issued: the boxes of the Odoo 17 B/L and air waybill."""
        self.ensure_one()
        _ = self.env._
        kind = self._boss_house_doc_kind()
        if not kind:
            return [_("only a sea or air file that is not a master has a house B/L or air waybill")]
        checks = [
            (self.shipper_id, _("shipper")), (self.consignee_id, _("consignee")),
            (self.origin_port_id, _("origin port or airport")),
            (self.destination_port_id, _("destination port or airport")),
            (self.vessel, _("vessel") if kind == "hbl" else _("flight")),
            (self.packages, _("number of packages")), (self.gross_kg, _("gross weight")),
            (self.goods_description, _("goods")), (self.house_doc_freight, _("freight prepaid or collect")),
        ]
        if kind == "hbl" and self.load_type == "fcl":
            containers = self.container_ids or self.master_id.container_ids  # a house travels in its master's
            checks.append((containers and all(containers.mapped("number")), _("the number of every container")))
        if kind == "hawb":
            checks.append((self.mawb_ref, _("master air waybill")))
        return [label for value, label in checks if not value]

    def action_issue_house_document(self):
        """Issue the house B/L or air waybill: its number is the file's (as Odoo 17 printed the partida's) unless one
        is typed, and the date of issue is today. Until then it prints as a DRAFT."""
        for file in self:
            problems = file._boss_house_doc_problems()
            if problems:
                raise UserError(self.env._("%(file)s cannot issue its house document yet, it lacks: %(problems)s.",
                                           file=file.name, problems=", ".join(problems)))
            ref_field = "hbl_ref" if file._boss_house_doc_kind() == "hbl" else "hawb_ref"
            file.write({ref_field: file[ref_field] or file.name,
                        "house_doc_issue_date": fields.Date.context_today(file)})
        return self.action_print_house_document()

    def action_print_house_document(self):
        self.ensure_one()
        kind = self._boss_house_doc_kind()
        if not kind:
            raise UserError(self._boss_house_doc_problems()[0])
        report = "action_report_house_bl" if kind == "hbl" else "action_report_house_awb"
        return self.env.ref(f"boss_documents.{report}").report_action(self)

    def _boss_manifest_houses(self):
        """The houses a manifest lists: those of a master (not cancelled), or the file itself."""
        self.ensure_one()
        return self.house_ids.filtered(lambda h: h.state != "cancel") or self

    def _boss_manifest_problems(self):
        """Odoo 17 refused the Cargo Manifest without the agent (action 1543); it also names the master document."""
        self.ensure_one()
        _ = self.env._
        problems = [] if self.agent_id else [_("the agent abroad (Who)")]
        if not (self.mbl_ref or self.mawb_ref):
            problems.append(_("the master B/L or air waybill"))
        return problems

    def action_print_cargo_manifest(self):
        self.ensure_one()
        problems = self._boss_manifest_problems()
        if problems:
            raise UserError(self.env._("No cargo manifest for %(file)s yet, it lacks: %(problems)s.", file=self.name,
                                       problems=", ".join(problems)))
        return self.env.ref("boss_documents.action_report_cargo_manifest").report_action(self)

    def _boss_transport_order_block(self):
        """The shipment block as a supplier sees it (purchase order): operational data only."""
        block = self._boss_document_block()
        block.update(customer_reference="", quotation="")
        return block
