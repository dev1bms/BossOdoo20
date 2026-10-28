"""The shipment block printed on every BOSS document (ADR-011): three short columns (Route · Transport · Cargo) built
from the file when the document has one, otherwise from the shipment data of the quotation. One builder for both,
so the invoice, the quotation and the purchase order always say the same thing. Only operational data: never a
cost, a margin, a supplier price or an internal note."""
from collections import Counter

from odoo.tools.misc import formatLang


def _label(record, field_name):
    """Translated label of a selection value (empty when unset)."""
    value = record[field_name]
    if not value:
        return ""
    field = record._fields[field_name]
    return dict(field._description_selection(record.env)).get(value, value)


def _place(country, port, place):
    """«Shanghái (CNSHA), China»: the port with its code (or the place typed), then the country."""
    parts = []
    if port:
        parts.append(f"{port.name} ({port.code})")
    elif place:
        parts.append(place)
    if country:
        parts.append(country.name)
    seen, out = set(), []  # keep the order, drop repeats
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return ", ".join(out)


def containers_summary(rows, with_numbers=False):
    """«2 × 40' HC, 1 × 20' DV» (+ the container numbers of a file when known)."""
    counts = Counter()
    numbers = []
    for row in rows:
        qty = int(getattr(row, "quantity", 1) or 1)
        counts[(row.size, row.container_type_id.code)] += qty
        if with_numbers and getattr(row, "number", False):
            numbers.append(row.number)
    text = ", ".join(f"{qty} × {size}' {code}" for (size, code), qty in counts.items())
    if numbers:
        text += " — " + ", ".join(numbers)
    return text


def _address(address):
    """«Almacén Zaragoza, Zaragoza»: the name of the pickup or delivery address and its city."""
    parts = [address.name or address.commercial_partner_id.name, address.city]
    return ", ".join(p for p in parts if p)


def _number(env, value, digits):
    """A number in the language of the document (es: 9.850 · 58,400)."""
    return formatLang(env, value, digits=digits)


def shipment_rows(src, prefix="", file=None):
    """Three columns of (label, value) rows. `src` is the record holding the shipment data (a sale.order with
    prefix «boss_», or a boss.expediente with no prefix); `file` adds the operational references when the
    document belongs to a file."""
    env = src.env
    _ = env._

    def g(name):
        return src[prefix + name] if (prefix + name) in src._fields else False

    # ---- route
    route = []
    direction = _label(src, prefix + "direction") if (prefix + "direction") in src._fields else ""
    mode = _label(src, prefix + "transport_mode") if (prefix + "transport_mode") in src._fields else ""
    load = _label(src, prefix + "load_type") if (prefix + "load_type") in src._fields else ""
    traffic = " · ".join(p for p in (direction, mode, load) if p)
    if traffic:
        route.append((_("Traffic"), traffic))
    origin = _place(g("origin_country_id"), g("origin_port_id"), g("origin_place"))
    destination = _place(g("destination_country_id"), g("destination_port_id"), g("destination_place"))
    if origin:
        route.append((_("From"), origin))
    if g("pickup_address_id"):
        route.append((_("Pickup"), _address(g("pickup_address_id"))))
    if destination:
        route.append((_("To"), destination))
    if g("delivery_address_id"):
        route.append((_("Delivery"), _address(g("delivery_address_id"))))
    incoterm = src["incoterm_id"] if "incoterm_id" in src._fields else (src["incoterm"] if "incoterm" in src._fields else False)
    if incoterm:
        location = src["incoterm_location"] if "incoterm_location" in src._fields else ""
        route.append((_("Incoterm"), f"{incoterm.code} {location}".strip()))
    shipper, consignee = g("shipper_id"), g("consignee_id")
    if shipper:
        route.append((_("Shipper"), shipper.commercial_partner_id.name or shipper.name))
    if consignee:
        route.append((_("Consignee"), consignee.commercial_partner_id.name or consignee.name))

    # ---- transport
    transport = []
    carrier = g("carrier_id")
    if carrier:
        transport.append((_("Carrier"), carrier.name))
    if file:
        if file.vessel:
            transport.append((_("Vessel / voyage"), " ".join(p for p in (file.vessel, file.voyage) if p)))
        if file.mbl_ref or file.hbl_ref:
            transport.append((_("B/L (master / house)"), " / ".join(p or "—" for p in (file.mbl_ref, file.hbl_ref))))
        if file.mawb_ref or file.hawb_ref:
            transport.append((_("AWB (master / house)"), " / ".join(p or "—" for p in (file.mawb_ref, file.hawb_ref))))
        if file.booking_ref:
            transport.append((_("Booking"), file.booking_ref))
        if file.customs_ref:
            transport.append((_("Customs reference"), file.customs_ref))
    etd, eta = g("etd"), g("eta")
    atd = file.atd if file else False
    ata = file.ata if file else False
    fmt = env["ir.qweb.field.date"].value_to_html
    if atd:
        transport.append((_("Departed"), fmt(atd, {})))
    elif etd:
        transport.append((_("ETD"), fmt(etd, {})))
    if ata:
        transport.append((_("Arrived"), fmt(ata, {})))
    elif eta:
        transport.append((_("ETA"), fmt(eta, {})))
    delivery_date = file.delivery_date if file else False
    if delivery_date:
        transport.append((_("Delivered"), fmt(delivery_date, {})))

    # ---- cargo
    cargo = []
    containers = file.container_ids if file else g("container_ids")
    if containers:
        cargo.append((_("Containers"), containers_summary(containers, with_numbers=bool(file))))
    packages, package_type = g("packages"), (_label(src, prefix + "package_type") if (prefix + "package_type") in src._fields else "")
    if packages:
        cargo.append((_("Packages"), f"{packages:g} {package_type}".strip()))
    elif package_type:
        cargo.append((_("Type of unit"), package_type))
    pallets = g("pallets")
    if pallets:
        cargo.append((_("Pallets"), f"{pallets:g}"))
    gross, volume, chargeable = g("gross_kg"), g("volume_m3"), g("chargeable_kg")
    if gross:
        cargo.append((_("Gross weight"), _number(env, gross, 0) + " kg"))
    if volume:
        cargo.append((_("Volume"), _number(env, volume, 3) + " m³"))
    if chargeable and (mode and "FCL" not in load):
        cargo.append((_("Chargeable weight"), _number(env, chargeable, 0) + " kg"))
    goods = g("goods_description")
    if goods:
        cargo.append((_("Goods"), goods))
    hs = g("hs_code")
    if hs:
        cargo.append((_("HS code"), hs))
    return {"route": route, "transport": transport, "cargo": cargo}


def scope_sentence(src, prefix=""):
    """«Services of BOSS: pickup, customs at origin, main carriage, delivery» from the five scope flags."""
    names = [("scope_pickup", "pickup"), ("scope_origin_customs", "customs at origin"), ("scope_main", "main carriage"),
             ("scope_destination_customs", "customs at destination"), ("scope_delivery", "delivery")]
    _ = src.env._
    labels = {"pickup": _("pickup"), "customs at origin": _("customs at origin"), "main carriage": _("main carriage"),
              "customs at destination": _("customs at destination"), "delivery": _("delivery")}
    done = [labels[key] for field, key in names if (prefix + field) in src._fields and src[prefix + field]]
    return ", ".join(done)
