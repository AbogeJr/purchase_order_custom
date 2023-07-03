from odoo import fields, models, api


class PurchaseLandedCost(models.Model):
    _name = "purchase.landed.cost"
    _description = "Relation for Purchase Landed Costs"

    SPLIT_METHOD = [
        ("equal", "Equal"),
        ("by_quantity", "By Quantity"),
        ("by_current_cost_price", "By Current Cost"),
        ("by_weight", "By Weight"),
        ("by_volume", "By Volume"),
    ]

    name = fields.Char("Description")
    vendor_id = fields.Many2one("res.partner", string="Vendor")
    product_id = fields.Many2one(
        "product.product", string="Product", domain=[("landed_cost_ok", "=", True)]
    )
    price_unit = fields.Monetary("Cost", required=True)
    split_method = fields.Selection(
        SPLIT_METHOD,
        string="Split Method",
        required=True,
    )
    account_id = fields.Many2one(
        "account.account", "Account", domain=[("deprecated", "=", False)]
    )
    date = fields.Date(
        "Date",
        default=fields.Date.context_today,
        copy=False,
        required=True,
        states={"done": [("readonly", True)]},
        tracking=True,
    )
    purchase_id = fields.Many2one(
        "purchase.order",
        "Purchase Order",
        domain=[("state", "=", "purchase")],
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id, readonly=True
    )
