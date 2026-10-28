"""Service groups of the file summary and the tariff date of each service, assigned by service code.

The groups are the product categories of Odoo 17 (All / Comercial / Flete, Flete terrestre, Locales, Aduana, Almacén,
Seguro + Courrier, Profit Share; read on production on 28/10/2026): the «Resumen» of a file sums buying and selling
by them (Ángel, meeting of 27/10/2026, part 2). Duties and taxes paid on behalf get their own group, as they are
re-invoiced at cost. A code not listed stays in the root category «BOSS services» (shown as «Other»).

The freight services take the departure (ETD) as tariff date, import or export (Ángel: «ocean freight takes always
the date of departure», also air freight); the rest keep the key date of the shipment.
"""
GROUP_XMLIDS = {
    "freight": "boss_services.product_category_freight",
    "inland": "boss_services.product_category_inland",
    "local": "boss_services.product_category_local",
    "customs": "boss_services.product_category_customs",
    "storage": "boss_services.product_category_storage",
    "insurance": "boss_services.product_category_insurance",
    "profit_share": "boss_services.product_category_profit_share",
    "duties": "boss_services.product_category_duties",
}
GROUP_BY_CODE = {
    **dict.fromkeys(("FMI", "FMI-LCL", "FME", "FME-LCL", "FAI", "FAE", "QBR"), "freight"),
    **dict.fromkeys(("FTT", "TTE-CON", "TTE-FCL", "FS", "PAR", "DAP", "DAP-CON"), "inland"),
    **dict.fromkeys(("THC", "THC-LCL", "GLO", "GLO-CCC", "GLO-LOG", "GLO-FUELEU", "T3", "T3-PAD", "GT3", "BL", "DOC",
                     "CES", "VGM", "COR", "ENS", "DEM", "DET", "OCU", "POT", "HAN", "AWB", "ETX", "X-R", "FUM", "IMO",
                     "INS", "DES", "POS", "ROH", "CSM", "CSA", "CST", "GLL", "EXW", "EXW-AIR", "EXW-FCL", "EXW-LCL",
                     "PFT-AIR", "PFT-FCL", "PFT-LCL"), "local"),
    **dict.fromkeys(("FAD", "DEX", "DVD", "AMS", "CAU", "EUR1", "TRA", "SAD", "SAN", "SOI", "VET", "FAR"), "customs"),
    **dict.fromkeys(("ALM", "OAL-CON", "OAL-PAL", "PAL", "VAC", "GAV"), "storage"),
    **dict.fromkeys(("SEG", "MEN"), "insurance"),
    **dict.fromkeys(("ARA", "IVA", "DUM", "PLA"), "duties"),
}
# Odoo 17 keeps PFT (profit share on ocean freight) in its own category; BOSS sells it as a local charge of the
# freight, so it stays with the local charges until Cristina says otherwise.
FREIGHT_ETD_CODES = ("FMI", "FMI-LCL", "FME", "FME-LCL", "FAI", "FAE")


def assign_service_groups(env):
    """Set the category and the tariff date of every BOSS service from its code (install and upgrade)."""
    Product = env["product.template"].with_context(active_test=False)
    services = Product.search([("default_code", "!=", False), ("boss_pricing_mode", "!=", False)])
    for service in services:
        group = GROUP_BY_CODE.get(service.default_code)
        values = {}
        if group:
            category = env.ref(GROUP_XMLIDS[group], raise_if_not_found=False)
            if category and service.categ_id != category:
                values["categ_id"] = category.id
        tariff_date = "etd" if service.default_code in FREIGHT_ETD_CODES else "key"
        if service.boss_tariff_date != tariff_date:
            values["boss_tariff_date"] = tariff_date
        if values:
            service.write(values)
    return services
