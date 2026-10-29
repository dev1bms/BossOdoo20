"""Load Odoo 17 contacts into boss20 from a JSON export (phase F2, plan «expediente completo»).

Input: /tmp/boss/<file>.json (mounted by dev/server_shell_wip.sh or dev/server_shell.sh), a list of res.partner records
as read from Odoo 17 (many2one as [id, name], x2many as lists of ids), parents and children in any order.
Rules (Belal, 28/10/2026):
  * Link: Odoo's external ids, module «o17_partner», name «res_partner_<odoo17 id>». Independent of `ref` and of the
    commercial codes, which are never overwritten. A second run finds the same target through that link.
  * Existing boss20 contacts (carriers, suppliers, customers) are matched, never duplicated: a company by its normalised
    VAT, else by its exact normalised name among companies without a VAT; a child by parent + type + normalised name.
    Only EMPTY fields of a matched record are filled; differences are reported, nothing is overwritten.
  * No automatic exclusion by city name, postcode or missing phone/e-mail. No automatic merge: two source records with
    the same VAT are both loaded and listed for review.
  * An archived source record is loaded archived (active = False).
  * Every discarded piece of information is reported with its reason.
Nothing is committed here: the caller decides (dry run = rollback).
    env["ir.module.module"]  # runs inside an odoo shell: `env` is given
"""
import json
import os
import re
import unicodedata

from odoo import Command
from odoo.exceptions import ValidationError

MODULE = "o17_partner"
DATA_FILE = os.environ.get("BOSS_FILES", "").split("|")[0] or "o17_partners.json"
TYPE_MAP = {  # x_studio_type → (customer_rank, supplier_rank, roles); roles depend on F0-C02 (proposal, not approved)
    "Cliente": (1, 0, []), "Cliente + Proveedor": (1, 1, []), "Proveedor": (0, 1, []), "Acreedor": (0, 1, []),
    "Agente": (0, 0, ["agent"]), "Expedidor/destinatario extranjero": (0, 0, ["shipper", "consignee"]),
    "Expedidor/destinatario español": (0, 0, ["shipper", "consignee"]), "PENDIENTE": (0, 0, []),
    "Shipper/Consignee Extranjero": (0, 0, ["shipper", "consignee"]),  # labels as stored in Odoo 17
    "Shipper/Consignee Español": (0, 0, ["shipper", "consignee"]),
}
FLAG_ROLES = {"x_studio_is_carrier": ["carrier"], "x_studio_is_airline": ["carrier"],
              "x_studio_is_customs_agent": ["customs_broker"], "x_studio_is_trucker": ["haulier"],
              "x_studio_is_shipperconsignee": ["shipper", "consignee"], "x_studio_is_agent": ["agent"]}
FLAG_SUPPLIER = ("x_studio_is_provider", "x_studio_is_carrier", "x_studio_is_airline", "x_studio_is_customs_agent",
                 "x_studio_is_trucker")
MSC_FAMILY = {23762, 23022, 23493, 23733, 54705}  # F0-B05 (decided): the five MSC legal entities form one family


def norm(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def norm_vat(vat):
    return re.sub(r"[^A-Z0-9]", "", (vat or "").upper()) or False


def vat_keys(vat, country_code=False):
    """Comparable forms of a VAT: with and without its country prefix (boss20 stores «ESB…», Odoo 17 «B…»)."""
    v = norm_vat(vat)
    if not v:
        return set()
    keys = {v}
    if country_code and not v.startswith(country_code):
        keys.add(country_code + v)
    if len(v) > 2 and v[:2].isalpha() and v[:2] in COUNTRY_CODES:
        keys.add(v[2:])
    return keys


COUNTRY_CODES = set()  # filled from res.country when the loader starts
COUNTRY_ALIASES = {"Turkey": "Türkiye"}  # Odoo 17 name → Odoo 20 name


def m2o_name(value):
    return value[1] if isinstance(value, (list, tuple)) and len(value) > 1 else (value or False)


def m2o_id(value):
    return value[0] if isinstance(value, (list, tuple)) and value else False


class Loader:
    def __init__(self, env, records):
        self.env = env
        self.records = {r["id"]: r for r in records}
        self.Partner = env["res.partner"]
        self.IMD = env["ir.model.data"]
        self.log = {"created": [], "linked_existing": [], "already_linked": [], "filled": [], "differs": [],
                    "discarded": [], "source_vat_duplicates": {}, "unmatched_payment_terms": set(),
                    "unmatched_country_state": [], "pending_decisions": set()}
        self.roles = {r.code: r.id for r in env["boss.partner.role"].search([])}
        COUNTRY_CODES.update(c for c in env["res.country"].search([]).mapped("code") if c)
        # BOSS's own company contacts and internal users' contacts: linked if they match, never written, no children added
        self.protected = set(env["res.company"].search([]).partner_id.ids) | set(
            env["res.users"].with_context(active_test=False).search([("share", "=", False)]).partner_id.ids)
        self.log["protected"] = []
        self.log["skipped"] = []
        self.terms = {norm(t.name): t.id for t in env["account.payment.term"].with_context(lang="es_ES").search([])}
        self.terms.update({norm(t.name): t.id for t in env["account.payment.term"].with_context(lang="en_US").search([])})

    # ---- lookup -------------------------------------------------------------------------------------------------------
    def xmlid_target(self, o17_id):
        imd = self.IMD.search([("module", "=", MODULE), ("name", "=", f"res_partner_{o17_id}")], limit=1)
        return self.Partner.browse(imd.res_id).exists() if imd else self.Partner

    def linked_targets(self):
        return set(self.IMD.search([("module", "=", MODULE), ("model", "=", "res.partner")]).mapped("res_id"))

    def link(self, o17_id, partner):
        self.IMD.create({"module": MODULE, "name": f"res_partner_{o17_id}", "model": "res.partner",
                         "res_id": partner.id, "noupdate": True})

    def country(self, rec):
        name = m2o_name(rec.get("country_id"))
        if not name:
            return False
        name = COUNTRY_ALIASES.get(name, name)
        for lang in ("es_ES", "en_US"):
            c = self.env["res.country"].with_context(lang=lang).search([("name", "=ilike", name)], limit=1)
            if c:
                return c
        self.log["unmatched_country_state"].append((rec["id"], "country", name))
        return False

    def state(self, rec, country):
        name = m2o_name(rec.get("state_id"))
        if not name:
            return False
        base = re.sub(r"(\s*\([A-Z]{2}\))+$", "", name)
        domain = [("name", "=ilike", base)] + ([("country_id", "=", country.id)] if country else [])
        s = self.env["res.country.state"].search(domain, limit=1)
        if not s and country:  # accent-insensitive: «Tokyo» = «Tōkyō»
            s = self.env["res.country.state"].search([("country_id", "=", country.id)]).filtered(
                lambda st: norm(st.name) == norm(base))[:1]
        if not s:
            self.log["unmatched_country_state"].append((rec["id"], "state", name))
        return s or False

    def payment_term(self, rec, field):
        name = m2o_name(rec.get(field))
        if not name:
            return False
        key = norm(name)
        if key in self.terms:
            return self.terms[key]
        days = re.search(r"(\d+)\s*(DIAS|DAYS)", key)
        if days:
            for k, tid in self.terms.items():
                if re.fullmatch(rf"{days.group(1)} (DIAS|DAYS)", k):
                    return tid
        self.log["unmatched_payment_terms"].add(name)
        return False

    # ---- values -------------------------------------------------------------------------------------------------------
    def values(self, rec, parent):
        country = self.country(rec)
        vals = {
            "name": rec.get("name"), "is_company": bool(rec.get("is_company")), "type": rec.get("type") or "contact",
            "street": rec.get("street") or False, "street2": rec.get("street2") or False, "zip": rec.get("zip") or False,
            "city": rec.get("city") or False, "country_id": country.id if country else False,
            "state_id": (self.state(rec, country) or self.Partner.browse()).id or False,
            "email": rec.get("email") or False, "phone": rec.get("phone") or False,
            "boss_mobile": rec.get("mobile") or False,  # Odoo 20 has no mobile field: kept apart, not merged into phone
            "website": rec.get("website") or False, "lang": rec.get("lang") or False,
            "comment": rec.get("comment") or False, "company_registry": rec.get("company_registry") or False,
            "vat": norm_vat(rec.get("vat")) if not parent else False,  # a child inherits its parent's VAT in Odoo
            "parent_id": parent.id if parent else False,
            "property_payment_term_id": self.payment_term(rec, "property_payment_term_id"),
            "property_supplier_payment_term_id": self.payment_term(rec, "property_supplier_payment_term_id"),
        }
        types = dict(self.Partner._fields["type"]._description_selection(self.env))
        if vals["type"] not in types:  # e.g. Odoo 17 «followup»: Odoo 20 sends reminders to the invoice address
            self.log["discarded"].append((rec["id"], "type", vals["type"], "type not in Odoo 20: loaded as «other»"))
            self.log["pending_decisions"].add(f"address type {vals['type']!r} loaded as «other» (follow-up contacts: "
                                              "decide whether they become invoice addresses)")
            vals["type"] = "other"
        if rec.get("lang") and rec["lang"] not in [c for c, _n in self.env["res.lang"].get_installed()]:
            self.log["discarded"].append((rec["id"], "lang", rec["lang"], "language not installed in boss20"))
            vals["lang"] = False
        # roles and ranks: proposal (F0-C02, not approved) — applied in the dry run and flagged
        if rec.get("x_studio_type") and rec["x_studio_type"] not in TYPE_MAP:
            self.log["pending_decisions"].add(f"unknown x_studio_type {rec['x_studio_type']!r}: no rank or role given")
        cust, supp, roles = TYPE_MAP.get(rec.get("x_studio_type") or "", (0, 0, []))
        roles = list(roles)
        for flag, codes in FLAG_ROLES.items():
            if rec.get(flag):
                roles += codes
        if any(rec.get(f) for f in FLAG_SUPPLIER):
            supp = 1
        if rec.get("x_studio_type") in (False, None, "", "PENDIENTE") and not roles:
            self.log["pending_decisions"].add("type PENDIENTE/empty without role: classified by use later (F0-C02)")
        vals["_customer_rank"], vals["_supplier_rank"] = cust, supp
        vals["_roles"] = sorted(set(self.roles[c] for c in roles if c in self.roles))
        vals["_code"] = rec.get("x_studio_code") or False
        return vals

    # ---- apply --------------------------------------------------------------------------------------------------------
    def match_existing(self, rec, vals, parent):
        taken = self.linked_targets()
        # 1. a link made earlier by hand in boss20: ref «O17:<id>» (the commercial code itself is never used to match)
        cands = self.Partner.with_context(active_test=False).search([("ref", "=", f"O17:{rec['id']}")])
        cands = cands.filtered(lambda p: p.id not in taken)
        if cands:
            return cands[:1]
        if parent:
            cands = self.Partner.with_context(active_test=False).search(
                [("parent_id", "=", parent.id), ("type", "=", vals["type"])])
            cands = cands.filtered(lambda p: p.id not in taken and norm(p.name) == norm(vals["name"]))
            return cands[:1]
        if vals["vat"]:
            country = self.env["res.country"].browse(vals["country_id"]).code if vals["country_id"] else False
            keys = vat_keys(vals["vat"], country)
            cands = self.Partner.with_context(active_test=False).search(
                [("is_company", "=", True), ("parent_id", "=", False), ("vat", "!=", False)])
            cands = cands.filtered(lambda p: p.id not in taken and vat_keys(p.vat, p.country_id.code) & keys)
            if cands:
                return cands[:1]
        cands = self.Partner.with_context(active_test=False).search(
            [("is_company", "=", True), ("parent_id", "=", False), ("vat", "=", False)])
        cands = cands.filtered(lambda p: p.id not in taken and norm(p.name) == norm(vals["name"]))
        return cands[:1]

    def apply(self, o17_id):
        rec = self.records[o17_id]
        parent_src = m2o_id(rec.get("parent_id"))
        parent = self.Partner
        if parent_src:
            parent = self.xmlid_target(parent_src)
            if not parent:
                if parent_src in self.records:
                    parent = self.apply(parent_src)
                else:
                    self.log["discarded"].append((o17_id, "parent_id", parent_src, "parent not in the export"))
        if parent and parent.id in self.protected and not self.xmlid_target(o17_id):
            self.log["skipped"].append((o17_id, parent.id, "parent is BOSS's own company or a user: needs decision"))
            return self.Partner
        vals = self.values(rec, parent)
        extra = {k: vals.pop(k) for k in ("_customer_rank", "_supplier_rank", "_roles", "_code")}
        target = self.xmlid_target(o17_id)
        if target:
            self.log["already_linked"].append(o17_id)
        else:
            target = self.match_existing(rec, vals, parent)
            if target:
                self.link(o17_id, target)
                self.log["linked_existing"].append((o17_id, target.id, target.name))
                if target.id in self.protected:
                    self.log["protected"].append((o17_id, target.id, "BOSS's own company or a user: linked, nothing written"))
            else:
                create_vals = {k: v for k, v in vals.items() if v not in (False, None, "")}
                create_vals["name"] = vals["name"]
                try:
                    with self.env.cr.savepoint():
                        target = self.Partner.create(create_vals)
                except ValidationError as err:  # e.g. a VAT Odoo rejects: loaded without it, reported for decision
                    if not create_vals.get("vat"):
                        raise
                    self.log["discarded"].append((o17_id, "vat", rec.get("vat"), f"rejected by Odoo: {err}"))
                    create_vals.pop("vat")
                    vals["vat"] = False
                    target = self.Partner.create(create_vals)
                if not rec.get("active", True):
                    target.active = False
                self.link(o17_id, target)
                self.log["created"].append((o17_id, target.id))
                vals = {}  # everything already written
        if target.id in self.protected:
            return target
        # fill empty fields only; report differences
        fill = {}
        for field, value in vals.items():
            if value in (False, None, ""):
                continue
            current = target[field]
            current = current.id if hasattr(current, "id") else current
            if current in (False, None, ""):
                fill[field] = value
            elif field == "vat" and vat_keys(target.vat, target.country_id.code) & vat_keys(value, target.country_id.code):
                continue
            elif current != value and field not in ("parent_id",):
                self.log["differs"].append((o17_id, target.id, field, current, value))
        if fill:
            try:
                with self.env.cr.savepoint():
                    target.write(fill)
            except ValidationError as err:  # a VAT Odoo rejects (already reported when the contact was created)
                if "vat" not in fill:
                    raise
                if not any(d[0] == o17_id and d[1] == "vat" for d in self.log["discarded"]):
                    self.log["discarded"].append((o17_id, "vat", fill["vat"], f"rejected by Odoo: {err}"))
                fill.pop("vat")
                if fill:
                    target.write(fill)
            if fill:
                self.log["filled"].append((o17_id, target.id, sorted(fill)))
        # ranks, roles, commercial code
        if extra["_customer_rank"] and not target.customer_rank:
            target.customer_rank = 1
        if extra["_supplier_rank"] and not target.supplier_rank:
            target.supplier_rank = 1
        new_roles = set(extra["_roles"]) - set(target.boss_role_ids.ids)
        if new_roles:
            target.boss_role_ids = [Command.link(r) for r in new_roles]
        if extra["_code"]:
            if not target.ref:
                target.ref = extra["_code"]
            elif target.ref != extra["_code"]:
                self.log["discarded"].append((o17_id, "x_studio_code", extra["_code"], f"target ref kept: {target.ref}"))
        return target

    def families(self):
        """F0-B05: the MSC legal entities point to one family head (created once, under its own external id)."""
        head = self.xmlid_target("family_msc")
        if not head:
            head = self.Partner.create({"name": "Mediterranean Shipping Company (MSC)", "is_company": True,
                                        "comment": "Family head of the MSC legal entities (migration F2, F0-B05)."})
            self.link("family_msc", head)
        for o17_id in MSC_FAMILY:
            entity = self.xmlid_target(o17_id)
            if entity and not entity.boss_carrier_group_id:
                entity.boss_carrier_group_id = head
            elif entity and entity.boss_carrier_group_id != head:
                self.log["differs"].append((o17_id, entity.id, "boss_carrier_group_id", entity.boss_carrier_group_id.id, head.id))

    def run(self):
        by_vat = {}
        for rec in self.records.values():
            if rec.get("is_company") and not m2o_id(rec.get("parent_id")) and norm_vat(rec.get("vat")):
                by_vat.setdefault(norm_vat(rec["vat"]), []).append(rec["id"])
        self.log["source_vat_duplicates"] = {v: ids for v, ids in by_vat.items() if len(ids) > 1}
        for o17_id in sorted(self.records):
            if not self.xmlid_target(o17_id) or o17_id not in self.log["already_linked"]:
                self.apply(o17_id)
        self.families()
        return self.log


def load(env, path):
    with open(path, encoding="utf-8") as fp:
        records = json.load(fp)
    if isinstance(records, dict):
        records = records["records"]
    return Loader(env, records).run()


if __name__ != "lib" and "env" in globals():  # the sample check imports this file as «lib»
    log = load(env, f"/tmp/boss/{DATA_FILE}")  # noqa: F821
    summary = {k: (len(v) if isinstance(v, (list, set, dict)) else v) for k, v in log.items()}
    print("MIGRATION", json.dumps(summary, ensure_ascii=False))
    for key in ("linked_existing", "differs", "discarded", "unmatched_country_state"):
        for item in log[key][:40]:
            print(f"  {key}: {item}")
    if log["unmatched_payment_terms"]:
        print("  unmatched_payment_terms:", sorted(log["unmatched_payment_terms"]))
    if log["source_vat_duplicates"]:
        print("  source_vat_duplicates:", {k: v for k, v in list(log["source_vat_duplicates"].items())[:20]})
    print("  pending_decisions:", sorted(log["pending_decisions"]))
