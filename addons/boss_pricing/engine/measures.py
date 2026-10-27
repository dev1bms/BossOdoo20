"""Quantities a supplier price is computed on, taken from the raw shipment inputs.

A supplier document says what it charges on (containers of a size, chargeable kg with ITS volumetric
factor, tonnes or fraction, W/M...). That reading is tariff data (params), never a constant here.
"""
import math

from .methods_base import MissingInput, dec

TEU = {"20": 1, "40": 2, "45": 2}


def _containers(inputs):
    """Containers matching the line filter (size / type); the filter is part of the inputs."""
    size, ctype = inputs.get("container_size"), inputs.get("container_type_id")
    rows = inputs.get("containers")
    if not rows:
        raise MissingInput("containers")
    return [c for c in rows if (not size or c["size"] == size) and (not ctype or c["type_id"] == ctype)]


def _required(inputs, name):
    value = inputs.get(name)
    if value in (None, False, ""):
        raise MissingInput(name)
    return dec(value)


def raw_measure(basis, inputs, params):
    """Value of `basis` before unit size and rounding."""
    if basis == "line":
        return _required(inputs, "line_qty")
    if basis == "containers":
        return dec(sum(c["quantity"] for c in _containers(inputs)))
    if basis == "teu":
        return dec(sum(c["quantity"] * TEU[c["size"]] for c in _containers(inputs)))
    if basis == "gross_kg":
        return _required(inputs, "gross_kg")
    if basis == "gross_ton":
        return _required(inputs, "gross_kg") / 1000
    if basis == "volume_m3":
        return _required(inputs, "volume_m3")
    if basis == "wm":
        return max(_required(inputs, "gross_kg") / 1000, _required(inputs, "volume_m3"))
    if basis == "chargeable_kg":
        factor = params.get("volumetric_factor")
        if not factor:
            # no factor stated by the document: the chargeable weight of the shipment, computed with the factor
            # of its transport mode (air 167, road 333, sea 1000 kg/m³; Ángel 27/10/2026)
            return _required(inputs, "chargeable_kg")
        return max(_required(inputs, "gross_kg"), _required(inputs, "volume_m3") * dec(factor))
    if basis == "awb_kg":
        return _required(inputs, "awb_kg")
    if basis in ("pallets", "goods_value", "duties_amount", "km"):
        return _required(inputs, basis)
    raise ValueError(f"unknown quantity basis {basis}")


def measure(basis, inputs, params, prefix=""):
    """Quantity in priced units: raw measure / unit size, rounded up when the document says
    'or fraction' (e.g. per 100 kg or fraction: unit_size 100, round_up)."""
    value = raw_measure(basis, inputs, params)
    unit_size = dec(params.get(prefix + "unit_size") or 1)
    quantity = value / unit_size
    if params.get(prefix + "round_up"):
        quantity = dec(math.ceil(quantity))
    return quantity, value
