"""Reference examples read from supplier documents, compared with boss.pricing.

The tariffs and the expected results (hand-computed from the documents, independently of this code)
live in a PRIVATE file (real supplier prices, never in Git): /mnt/samples/samples.json, built by
.research/gen_samples.py. Without that file the test is skipped and says so.
"""
import base64
import json
import logging
import os
from datetime import date
from pathlib import Path

from odoo.tests import TransactionCase, new_test_user, tagged

_logger = logging.getLogger(__name__)
SAMPLES = Path(os.environ.get("BOSS_SAMPLES", "/mnt/samples/samples.json"))
TEST_DOCUMENT = base64.b64encode(b"%PDF-1.4 reference test (real document attached by the loader)").decode()


@tagged("post_install", "-at_install", "boss_references")
class TestSupplierReferences(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not SAMPLES.is_file():
            cls.data = None
            return
        cls.data = json.loads(SAMPLES.read_text(encoding="utf-8"))
        cls.env.ref("base.EUR").active = True
        approver = new_test_user(cls.env, "boss_ref_approver", groups="boss_pricing.group_tariff_approver")
        for spec in cls.data["tariffs"]:
            spec["document_b64"] = TEST_DOCUMENT
        tariffs = cls.env["boss.tariff"]._boss_import_tariffs(cls.data)
        tariffs.with_user(approver).action_approve()  # a person approves; here the test plays that role

    def _id(self, model, domain):
        return self.env[model].with_context(active_test=False).search(domain, limit=1).id

    def _inputs(self, raw):
        inputs = {k: raw[k] for k in ("direction", "transport_mode", "load_type", "line_qty", "gross_kg",
                                      "volume_m3", "awb_kg", "storage_days", "container_size", "start_weekday") if k in raw}
        if "carrier" in raw:
            inputs["carrier_id"] = self._id("res.partner", [("name", "=", f"{raw['carrier']} [MUESTRA]")])
        if "country" in raw:
            inputs["country_id"] = self._id("res.country", [("code", "=", raw["country"])])
        if "port" in raw:
            inputs["port_id"] = self._id("boss.port", [("code", "=", raw["port"])])
        if "state" in raw:
            inputs["state_id"] = self._id("res.country.state", [("country_id.code", "=", "ES"), ("code", "=", raw["state"])])
        if "container_type" in raw:
            inputs["container_type_id"] = self._id("boss.container.type", [("code", "=", raw["container_type"])])
        if "containers" in raw:
            inputs["containers"] = [{"size": size, "quantity": qty,
                                     "type_id": self._id("boss.container.type", [("code", "=", ctype)])}
                                    for size, ctype, qty in raw["containers"]]
        if "related" in raw:
            supplier = self._id("res.partner", [("name", "=", "IRENEO [MUESTRA]")])
            inputs["related_costs"] = [{"product_id": self._id("product.product", [("default_code", "=", code)]),
                                        "supplier_id": supplier, "amount": amount, "currency": "EUR"}
                                       for code, amount in raw["related"]]
        return inputs

    def test_reference_examples(self):
        if not self.data:
            self.skipTest(f"Private reference samples not found at {SAMPLES}")
        pricing = self.env["boss.pricing"]
        failures = []
        for ref in self.data["references"]:
            product = self.env["product.product"].search([("default_code", "=", ref["service"])])
            uom = self.env.ref(f"boss_services.uom_{ref['uom']}")
            res = pricing.price_cost(product, uom, self._inputs(ref["inputs"]), date.fromisoformat(ref["date"]))
            got = round(res.amount, 2) if res.status == "ok" else res.status
            expected = ref["expected"] if ref["expected"] is not None else "no price"
            ok = (got == expected) if ref["expected"] is not None else res.status != "ok"
            if not ok:
                failures.append(f"{ref['ref']} {ref['service']} {ref['source']}: expected {expected}, got {got} "
                                f"{res.missing or ''}")
        _logger.info("%s supplier reference examples checked, %s failures", len(self.data["references"]), len(failures))
        self.assertFalse(failures, "\n" + "\n".join(failures))
