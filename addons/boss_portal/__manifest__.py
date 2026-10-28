{
    "name": "BOSS Customer Portal",
    "summary": "Customer portal on the standard Odoo portal: roles granted by BOSS (tracking, commercial, authorised "
               "representative), quotations and invoices of the customer's own legal entity, rate quotations without "
               "totals, booking requests reviewed by BOSS, My Shipments with published events and documents, and a "
               "revocable tracking link. BOSS costs and margins never reach the customer (ADR-010).",
    "version": "20.0.1.0.2",
    "category": "Website/Website",
    "author": "BiDATiA",
    "license": "LGPL-3",
    "depends": ["boss_expediente", "portal", "sale", "account"],
    "data": [
        "security/ir.access.csv",
        "data/portal_entry_data.xml",
        "data/mail_template_data.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/boss_expediente_views.xml",
        "views/portal_sale_templates.xml",
        "views/portal_shipment_templates.xml",
    ],
    "installable": True,
}
