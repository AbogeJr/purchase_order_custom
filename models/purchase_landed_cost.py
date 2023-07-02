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

    def create_vendor_bill(self):
        AccountMove = self.env["account.move"]
        AccountMoveLine = self.env["account.move.line"]
        for record in self:
            # Create an empty invoice
            invoice = AccountMove.create(
                {
                    "move_type": "in_invoice",
                    "partner_id": record.vendor_id.id,  # Set the customer/partner for the invoice
                    # "invoice_date": record.date_approve,  # Set the invoice date
                    "ref": record.purchase_id.name,  # Set the invoice reference
                }
            )
            # Calculate invoice lines
            # quantity = record.quantity
            price = record.price
            taxes = record.taxes
            product = record.product_id
            purchase = record.purchase_id

            # Create the first invoice line
            line1 = AccountMoveLine.create(
                {
                    "name": product.name,
                    "product_id": product.id,
                    "tax_ids": [(6, 0, taxes.ids)],
                    "price_unit": price,
                    "is_landed_costs_line": True,
                    "purchase_order_id": purchase.id,
                    # "quantity": quantity,
                    "move_id": invoice.id,
                }
            )

            # Set the invoice lines on the invoice
            invoice.write(
                {
                    "invoice_line_ids": [
                        (4, line1.id),
                    ]
                }
            )

            # Post the invoice
            invoice.state = "posted"

            # Set the created invoice on the property
            record.vendor_bill_id = invoice.id

    def create_landed_cost(self):
        LandedCost = self.env["stock.landed.cost"]
        for record in self:
            # Create an empty landed cost
            if record.vendor_bill_id:
                landed_cost = LandedCost.create(
                    {
                        "vendor_bill_id": record.vendor_bill_id.id,
                        "account_journal_id": record.purchase_id.journal_id.id,
                        "cost_lines": [
                            (
                                0,
                                0,
                                {
                                    "product_id": record.product_id.id,
                                    "name": record.product_id.name,
                                    "split_method": "equal",
                                    "price_unit": record.price,
                                },
                            )
                        ],
                    }
                )
                # Compute the landed cost
                landed_cost.compute_landed_cost()
