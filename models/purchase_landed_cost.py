from odoo import fields, models


class PurchaseLandedCost(models.Model):
    _name = "purchase.landed.cost"
    _description = "Relation for Purchase Landed Costs"

    vendor_id = fields.Many2one("res.partner", string="Vendor")
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Integer()
    price = fields.Float()
    taxes = fields.Many2many("account.tax")
