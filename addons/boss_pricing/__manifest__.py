{
    "name": "BOSS Pricing",
    "summary": "Supplier tariffs with document, validity and approval; one engine to price a service",
    "version": "20.0.1.9.0",
    "category": "Sales/Sales",
    "author": "BiDATiA",
    "license": "LGPL-3",
    "depends": ["boss_services", "mail"],
    "data": [
        "security/boss_pricing_security.xml",
        "security/ir.access.csv",
        "data/boss_port_data.xml",
        "data/boss_container_type_data.xml",
        "views/boss_port_views.xml",
        "views/boss_tariff_views.xml",
        "views/workspace_views.xml",
    ],
    "installable": True,
}
