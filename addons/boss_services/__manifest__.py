{
    "name": "BOSS Services",
    "summary": "BOSS service catalogue: services as standard products, charge bases as units",
    "version": "20.0.1.4.0",
    "category": "Sales/Sales",
    "author": "BiDATiA",
    "license": "LGPL-3",
    "depends": ["product", "uom", "account"],
    "data": [
        "data/uom_feature_data.xml",
        "data/uom_data.xml",
        "data/product_data.xml",
        "data/product_category_data.xml",
        "views/product_views.xml",
        "views/uom_views.xml",
    ],
    "post_init_hook": "_boss_post_init",
    "installable": True,
}
