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
        "report_xlsx",
        "product",
        "purchase",
    ],
    "data": [
        "report/purchase_order.xml",
        "views/purchase_order.xml",
        "views/purchase_landed_cost.xml",
        "views/product.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
    "auto_install": True,
}
