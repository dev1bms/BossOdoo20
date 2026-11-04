from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .shipment_block import scope_sentence, shipment_rows


# Freight prepaid / collect comes from the incoterm (its field «Freight», shared with the margin rules); editable on the
# file (Odoo 17: field «Freight» of the B/L, chosen by hand).


class ResCompany(models.Model):
    _inherit = "res.company"

    # Settings study of 04/11/2026: what the house documents print, as values (docs/estudio-ajustes.md).
    boss_hbl_originals = fields.Integer("Original house B/Ls issued", default=3,
                                        help="Printed on the house B/L; a sea waybill prints «express», zero.")
    boss_doc_issue_place = fields.Char("Place of issue of the house documents",
                                       help="Empty: the city of the company.")

    @api.constrains("boss_hbl_originals")
    def _check_boss_document_values(self):
        """Settings values that make sense (a zero or negative number would be replaced or printed as such)."""
        for company in self:
            for field, minimum in (("boss_hbl_originals", 1),):
                if company[field] < minimum:
                    raise ValidationError(self.env._("%(setting)s: enter a value of at least %(minimum)s.",
                                                     setting=self._fields[field].get_description(self.env)["string"],
                                                     minimum=minimum))


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    boss_hbl_originals = fields.Integer(related="company_id.boss_hbl_originals", readonly=False)
    boss_doc_issue_place = fields.Char(related="company_id.boss_doc_issue_place", readonly=False)


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
    # An issued document does not change (roadmap item 19): its PDF is kept on the file at issue (report attachment) and
    # every reprint gives that copy; a correction is a new issue, numbered, with its reason in the history.
    house_doc_issue_count = fields.Integer("House document issues", copy=False, readonly=True)

    def _boss_frozen_fields(self):
        return super()._boss_frozen_fields() + ("house_doc_freight", "house_doc_marks", "house_doc_issue_date",
                                                "house_doc_issue_count")

    # Proposed when the file's incoterm is set or changed; editing an incoterm does not rewrite the files (closed ones,
    # issued documents and values chosen by hand stay as they are).
    @api.depends("incoterm_id")
    def _compute_house_doc_freight(self):
        for file in self:
            file.house_doc_freight = file.incoterm_id.boss_freight_payment or file.house_doc_freight

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
            file.write({ref_field: file[ref_field] or file.name})
            file._boss_issue_house_document()
        return self.action_print_house_document()

    def _boss_issue_house_document(self):
        """Date and number the issue, and keep its PDF on the file: reprints give this copy, not today's data."""
        self.ensure_one()
        self.write({"house_doc_issue_date": fields.Date.context_today(self),
                    "house_doc_issue_count": self.house_doc_issue_count + 1})
        self.env["ir.actions.report"]._render_qweb_pdf(self._boss_house_doc_report(), self.ids)

    def _boss_house_doc_report(self):
        kind = self._boss_house_doc_kind()
        return "boss_documents.action_report_house_bl" if kind == "hbl" else "boss_documents.action_report_house_awb"

    def action_reissue_house_document(self):
        """A correction after the issue: a new issue with its reason; the earlier copies stay in the attachments."""
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": self.env._("Re-issue the house document"),
                "res_model": "boss.house.doc.reissue", "view_mode": "form", "target": "new",
                "context": {"default_expediente_id": self.id}}

    def _boss_reissue_house_document(self, reason):
        self.ensure_one()
        if not self.house_doc_issue_date:
            raise UserError(self.env._("%s has no issued house document yet: issue it first.", self.name))
        problems = self._boss_house_doc_problems()
        if problems:
            raise UserError(self.env._("%(file)s cannot issue its house document yet, it lacks: %(problems)s.",
                                       file=self.name, problems=", ".join(problems)))
        self.message_post(body=self.env._("House document re-issued (issue %(number)s): %(reason)s",
                                          number=self.house_doc_issue_count + 1, reason=reason))
        self._boss_issue_house_document()
        return self.action_print_house_document()

    def action_print_house_document(self):
        self.ensure_one()
        kind = self._boss_house_doc_kind()
        if not kind:
            raise UserError(self._boss_house_doc_problems()[0])
        return self.env.ref(self._boss_house_doc_report()).report_action(self)

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
