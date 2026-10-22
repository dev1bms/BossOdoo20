"""Import supplier tariffs from a JSON description (reference samples, future bulk loads).

Idempotent: each tariff has a key kept in ir.model.data (module `boss_tariff_import`); an existing
record is never rewritten (user edits win). Imported tariffs are sent for approval when their supplier
document is provided, and are NEVER approved here: approval stays a human click (ADR-002).
"""
import base64
from pathlib import Path

from odoo import api, models
from odoo.exceptions import UserError

XMLID_MODULE = "boss_tariff_import"
TARIFF_REQUIRED = ("key", "name", "supplier", "valid_from", "lines")
LINE_REQUIRED = ("service", "uom")
LINE_KEYS = ("container_size", "method", "basis", "volumetric_factor", "unit_size", "round_up", "unit_price",
             "basis_2", "unit_price_2", "b2_unit_size", "b2_round_up", "floor_previous", "per_container",
             "percent_base", "rate", "free_days", "free_hours", "free_mode", "tier_mode", "friday_extra_day",
             "saturday_until_monday", "min_amount", "max_amount", "on_request", "note")


class BossTariff(models.Model):
    _inherit = "boss.tariff"

    @api.model
    def _boss_import_ref(self, model, domain, label):
        record = self.env[model].with_context(active_test=False).search(domain, limit=1)
        if not record:
            raise UserError(self.env._("Import: %(label)s not found (%(domain)s).", label=label, domain=domain))
        return record

    @api.model
    def _boss_import_check(self, spec, required, label):
        """A clear message for an incomplete file instead of a KeyError deep in the import."""
        missing = [key for key in required if spec.get(key) in (None, "", [], {})]
        if missing:
            raise UserError(self.env._("Import: %(label)s lacks %(keys)s.", label=label, keys=", ".join(missing)))

    @api.model
    def _boss_import_service(self, code):
        return self._boss_import_ref("product.product", [("default_code", "=", code)], code)

    @api.model
    def _boss_import_partner(self, name):
        Partner = self.env["res.partner"]
        return Partner.search([("name", "=", name)], limit=1) or Partner.create({"name": name, "is_company": True})

    @api.model
    def _boss_import_document(self, spec):
        if spec.get("document_b64"):
            return spec["document_b64"]
        path = Path(spec.get("document_path") or "")
        if path.is_file():
            return base64.b64encode(path.read_bytes()).decode()
        return False

    @api.model
    def _boss_import_line(self, spec, label="line"):
        self._boss_import_check(spec, LINE_REQUIRED, label)
        product = self._boss_import_service(spec["service"])
        uom = self.env.ref(f"boss_services.uom_{spec['uom']}", raise_if_not_found=False)
        if not uom:
            raise UserError(self.env._("Import: %(label)s has an unknown charge basis '%(uom)s'.", label=label,
                                       uom=spec["uom"]))
        vals = {key: spec[key] for key in LINE_KEYS if key in spec}
        vals.update({
            "product_id": product.id,
            "uom_id": uom.id,
            "document_page": spec.get("page"),
            "container_type_ids": [(6, 0, [self._boss_import_ref("boss.container.type", [("code", "=", c)], c).id
                                           for c in spec.get("container_types", [])])],
            "base_product_ids": [(6, 0, [self._boss_import_service(c).id for c in spec.get("base_services", [])])],
            "bracket_ids": [(0, 0, {"up_to": b["up_to"] or 0.0, "fixed_amount": b.get("fixed_amount") or 0.0,
                                    "unit_price": b.get("unit_price") or 0.0}) for b in spec.get("brackets", [])],
        })
        return vals

    @api.model
    def _boss_import_tariffs(self, data, submit=True):
        """Create the tariffs of `data["tariffs"]` that do not exist yet. Returns the created tariffs."""
        created = self.browse()
        IMD = self.env["ir.model.data"]
        for index, spec in enumerate(data.get("tariffs", []), start=1):
            label = self.env._("tariff %(index)s (%(key)s)", index=index, key=spec.get("key") or spec.get("name") or "?")
            self._boss_import_check(spec, TARIFF_REQUIRED, label)
            existing = IMD.search([("module", "=", XMLID_MODULE), ("name", "=", spec["key"])], limit=1)
            if existing and self.browse(existing.res_id).exists():
                continue
            supplier = self._boss_import_partner(spec["supplier"])
            scope = spec.get("scope") or {}
            vals = {
                "name": spec["name"], "partner_id": supplier.id, "valid_from": spec["valid_from"],
                "valid_to": spec.get("valid_to") or False, "document_reference": spec.get("document_reference"),
                "currency_id": self._boss_import_ref("res.currency", [("name", "=", spec.get("currency", "EUR"))],
                                                     spec.get("currency")).id,
                "carrier_id": supplier.id if spec.get("carrier") else False, "note": spec.get("note"),
                "direction": scope.get("direction") or False, "transport_mode": scope.get("transport_mode") or False,
                "load_type": scope.get("load_type") or False,
                "country_ids": [(6, 0, [self._boss_import_ref("res.country", [("code", "=", c)], c).id
                                        for c in spec.get("countries", [])])],
                "port_ids": [(6, 0, [self._boss_import_ref("boss.port", [("code", "=", c)], c).id
                                     for c in spec.get("ports", [])])],
                "state_ids": [(6, 0, [self._boss_import_ref(
                    "res.country.state", [("country_id.code", "=", "ES"), ("code", "=", c)], c).id
                    for c in spec.get("states", [])])],
                # the structured file states the scope explicitly (empty = any, on purpose): reviewed
                "scope_confirmed": True,
                "line_ids": [(0, 0, self._boss_import_line(line, f"{label}, line {n}"))
                             for n, line in enumerate(spec["lines"], start=1)],
            }
            document = self._boss_import_document(spec)
            if document:
                vals.update(document=document, document_name=Path(spec.get("document_path") or "document.pdf").name)
            tariff = self.create(vals)
            if existing:
                existing.res_id = tariff.id
            else:
                IMD.create({"module": XMLID_MODULE, "name": spec["key"], "model": self._name, "res_id": tariff.id,
                            "noupdate": True})
            if submit and document:
                tariff.action_submit()
            created |= tariff
        return created
