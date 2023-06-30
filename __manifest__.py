# -*- coding: utf-8 -*-
{
    "name": "Purchase Order Autolamps",
    "summary": """
        Adds xlsx report to Purchase Orders
        """,
    "author": "Auraska Infotech",
    "website": "https://auraska.ke",
    "version": "8.0.1.0.1",
    "category": "Purchases",
    "license": "AGPL-3",
    "depends": [
        "web",
        "product",
        "stock",
        "purchase",
        "account",
    ],
    "data": [
        "views/purchase_order.xml",
        "views/purchase_landed_cost.xml",
        "views/product.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "purchase_order_autolamps/static/src/js/action_manager.js",
        ]
    },
    "installable": True,
    "application": True,
    "auto_install": True,
}
