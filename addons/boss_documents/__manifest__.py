{
    "name": "BOSS Documents",
    "summary": "Customer and supplier documents of BOSS Continental (invoice, credit note, quotation, order, purchase order): "
               "BOSS layout on the standard Odoo document template, one shipment block (file, route, transport, cargo) on "
               "every document, charge bases always printed, no shipping-address duplicates (ADR-011)",
    "version": "20.0.1.4.0",
    "category": "Accounting/Accounting",
    "author": "BiDATiA",
    "license": "LGPL-3",
    "depends": ["boss_expediente"],
    "data": [
        "security/ir.access.csv",
        "report/shipment_block_templates.xml",
        "report/invoice_templates.xml",
        "report/sale_templates.xml",
        "report/purchase_templates.xml",
        "report/transport_order_templates.xml",
        "report/house_document_templates.xml",
        "views/boss_expediente_views.xml",
        "views/house_doc_reissue_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "post_init_hook": "_boss_post_init",
    "installable": True,
}
