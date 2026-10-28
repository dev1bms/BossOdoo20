{
    "name": "BOSS Documents",
    "summary": "Customer and supplier documents of BOSS Continental (invoice, credit note, quotation, order, purchase order): "
               "BOSS layout on the standard Odoo document template, one shipment block (file, route, transport, cargo) on "
               "every document, charge bases always printed, no shipping-address duplicates (ADR-011)",
    "version": "20.0.1.0.4",
    "category": "Accounting/Accounting",
    "author": "BiDATiA",
    "license": "LGPL-3",
    "depends": ["boss_expediente"],
    "data": [
        "report/shipment_block_templates.xml",
        "report/invoice_templates.xml",
        "report/sale_templates.xml",
        "report/purchase_templates.xml",
    ],
    "post_init_hook": "_boss_post_init",
    "installable": True,
}
