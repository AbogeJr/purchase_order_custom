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
        # "stock",
        "web",
        "product",
        "purchase",
        "account",
        "stock",
        "stock_landed_costs",
    ],
    "data": [
        "views/stock_landed_cost.xml",
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
