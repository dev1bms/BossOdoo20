{
    "name": "BOSS Web: chatter below the form",
    "summary": "The chatter (messages, log notes, activities) always goes below the form, never beside it: BOSS forms "
               "(quotation, file, tariff) need the full width of the screen",
    "version": "20.0.1.0.0",
    "category": "Hidden/Tools",
    "author": "BiDATiA",
    "license": "LGPL-3",
    "depends": ["mail"],
    "assets": {
        "web.assets_backend": [
            "boss_web/static/src/**/*",
        ],
    },
    "installable": True,
}
