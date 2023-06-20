# -*- coding: utf-8 -*-
import time
import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.tools import float_is_zero
from odoo.tools import date_utils
import io
import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    landed_cost_factor = fields.Float()
    base_pricing_factor = fields.Float()
    pricing_preference = fields.Selection(
        [
            ("strict", "Strict"),
            ("high", "Prefer higher Price"),
            ("low", "Prefer Lower Price"),
        ]
    )
    costing_ids = fields.One2many("purchase.costing", "order_id")
    cost_item_ids = fields.One2many("purchase.costing.item.lines", "order_id")
    cost_items_amount_total = fields.Float(compute="_compute_cost_items_totals")
    cost_base_amount = fields.Float(compute="_compute_cost_items_totals")
    cost_base_amount_lcy = fields.Float(compute="_compute_cost_items_totals")
    currency_factor = fields.Float(string="Currency Rate", default=1)
    landed_costs = fields.One2many("purchase.landed.cost", "purchase_id")

    def print_xlsx_report(self):
        datas = {
            "ids": self.ids,
            "model": "purchase.order",
            "options": json.dumps(
                {
                    "start_date": self.date_order.date(),
                    "end_date": self.date_order.date(),
                    "id": self.id,
                },
                default=date_utils.json_default,
            ),
            "output_format": "xlsx",
            "report_name": "Excel Report",
            "form": self.read()[0],
        }

        return {
            "type": "ir.actions.report",
            "report_name": "purchase_order_xlsx",
            "data": datas,
            "name": "Purchase Order",
            "file": "Purchase Order.xlsx",
            "report_type": "xlsx",
        }

    def get_xlsx_report(self, data, response):
        po = self.env["purchase.order"].search([("id", "=", data["id"])])

        from_date = data["start_date"]
        to_date = data["end_date"]
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet()
        header = workbook.add_format(
            {"font_size": 16, "align": "center", "bg_color": "#D3D3D3", "bold": True}
        )
        bold = workbook.add_format({"font_size": 10, "bold": True})
        normal = workbook.add_format({"font_size": 10})
        currency = workbook.add_format({"font_size": 10, "num_format": "#,##0.00"})
        currency_bold = workbook.add_format(
            {"font_size": 10, "num_format": "#,##0.00", "bold": True}
        )

        sheet.merge_range("B1:K1", "Purchase Order: %s" % po.name, header)
        sheet.merge_range("B2:C2", "Supplier:", bold)
        sheet.merge_range("D2:E2", po.partner_id.name, normal)
        sheet.merge_range("B3:C3", "Order Date:", bold)
        sheet.merge_range("D3:E3", po.date_order, normal)
        sheet.merge_range("B4:C4", "Currency:", bold)
        sheet.merge_range("D4:E4", po.currency_id.name, normal)

        # Adjust height: top row
        sheet.set_row(0, 20)

        # Adjust column sizes
        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 5)
        sheet.set_column(4, 4, 10)
        sheet.set_column(6, 6, 12)

        # Table Headers
        row = 4
        sheet.write(row, 0, "No.", bold)
        sheet.write(row, 1, "Product Sequence", bold)
        sheet.write(row, 2, "Automan ID", bold)
        sheet.write(row, 3, "Supplier Product Code", bold)
        sheet.write(row, 4, "Product Code", bold)
        sheet.write(row, 5, "Product Description", bold)
        sheet.write(row, 6, "Qty", bold)
        sheet.write(row, 7, "FoB", bold)
        sheet.write(row, 8, "Units", bold)
        sheet.write(row, 9, "Measurements", bold)
        sheet.write(row, 10, "Sub-total", bold)

        # Table data
        index = 1
        row += 1
        for line in po.order_line:
            product_code = line.product_id.default_code
            supplier_code = ""
            supplier = line.product_id.seller_ids.filtered(
                lambda s: s.partner_id.id == po.partner_id.id
            )
            if supplier:
                supplier_code = supplier[0].product_code
            sheet.write(row, 0, index, normal)
            sheet.write(row, 1, line.product_id.sequence, normal)
            sheet.write(row, 2, line.product_id.id or "", normal)
            sheet.write(row, 3, supplier_code or "N\A", normal)
            sheet.write(row, 4, product_code or "N\A", normal)
            sheet.write(row, 5, line.product_id.name, normal)
            sheet.write(row, 6, line.product_qty, normal)
            sheet.write(row, 7, line.price_unit, currency)
            sheet.write(row, 8, line.product_uom_qty, normal)
            sheet.write(row, 9, line.product_uom.name or "", normal)
            sheet.write(row, 10, line.price_subtotal, currency)

            row += 1
            index += 1

        # write sub-totals
        row += 1
        sheet.write(row, 9, "Taxes:", bold)
        sheet.write(row, 10, po.amount_tax, currency_bold)
        row += 1
        sheet.write(row, 9, "Totals:", bold)
        sheet.write(row, 10, po.amount_total, currency_bold)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def compute_costing_lines(self):
        self.costing_ids.unlink()
        lines = []
        for record in self:
            for line in record.order_line:
                val = {}
                val["product_id"] = line.product_id.id
                val["old_cost"] = line.product_id.standard_price
                landed_cost = (
                    self.landed_cost_factor
                    * (self.currency_factor or 1)
                    * line.price_unit
                    if self.landed_cost_factor > 0
                    else line.product_id.standard_price
                )
                val["new_cost"] = landed_cost
                val["old_price"] = line.product_id.lst_price
                price = (
                    self.base_pricing_factor * landed_cost
                    if self.base_pricing_factor > 0
                    else line.product_id.lst_price
                )

                val["computed_price"] = price

                if self.pricing_preference == "high":
                    val["new_price"] = round(
                        price
                        if price > line.product_id.lst_price
                        else line.product_id.lst_price
                    )
                elif self.pricing_preference == "low":
                    val["new_price"] = round(
                        price
                        if price < line.product_id.lst_price
                        else line.product_id.lst_price
                    )
                else:
                    val["new_price"] = round(price)

                val["new_price"] = (
                    round(float(val["new_price"]) / 10) * 10
                )  # round to nearest 10. Make sure price is a float for correct computation
                val["old_margin"] = (
                    line.product_id.lst_price - line.product_id.standard_price
                )
                val["new_margin"] = val["new_price"] - val["new_cost"]

                val["cost_difference"] = val["new_cost"] - val["old_cost"]
                val["price_difference"] = val["new_price"] - val["old_price"]

                lines.append((0, 0, val))

        self.costing_ids = lines

    def adjust_costing(self):
        for record in self:
            for line in record.costing_ids:
                line.product_id.lst_price = line.new_price
                line.product_id.standard_price = line.new_cost

    def revert_costing(self):
        for record in self:
            for line in record.costing_ids:
                line.product_id.lst_price = line.old_price
                line.product_id.standard_price = line.old_cost

    def update_supplier_pricelist(self):
        for product in self.order_line:
            supplier_pricelist = product.product_id.seller_ids.filtered(
                lambda x: x.id == self.partner_id.id
            )
            if len(supplier_pricelist) > 0:
                for pricelist in supplier_pricelist:
                    pricelist.purchase_id = self.id
                    for line in pricelist.pricelist_ids:
                        line.price = product.price_unit

    @api.depends("amount_total", "cost_item_ids.amount", "currency_factor")
    def _compute_cost_items_totals(self):
        for order in self:
            order.cost_items_amount_total = sum(
                cost_item.amount for cost_item in order.cost_item_ids
            )
            order.cost_base_amount = order.amount_total
            order.cost_base_amount_lcy = (
                order.amount_total * order.currency_factor
                if order.currency_factor > 0
                else order.amount_total
            )

    def btn_compute_landed_cost_factor(self):
        self.ensure_one()
        self.landed_cost_factor = (
            1 + self.cost_items_amount_total / self.cost_base_amount_lcy
        )


class PurchaseCosting(models.Model):
    _name = "purchase.costing"

    order_id = fields.Many2one("purchase.order")
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    old_cost = fields.Float(string="Old Cost", readonly=True)
    new_cost = fields.Float(string="New Cost", readonly=True)
    old_price = fields.Float(string="Old Price", readonly=True)
    computed_price = fields.Float(string="Computed Price", readonly=True)
    new_price = fields.Float(string="New Price")
    old_margin = fields.Float(string="Old Margin", readonly=True)
    new_margin = fields.Float(string="New Margin", readonly=True)
    cost_difference = fields.Float(string="Cost Difference", readonly=True)
    price_difference = fields.Float(string="Price Difference", readonly=True)

    @api.onchange("new_price")
    def _recompute_price_and_margin(self):
        self.new_margin = self.new_price - self.new_cost
        self.price_difference = self.new_price - self.old_price


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    purchase_id = fields.Many2one(
        "purchase.order", string="Last updated By PO", readonly=True
    )


class PurchaseCostingItem(models.Model):
    _name = "purchase.costing.item"

    name = fields.Char()


class PurchaseCostingItemLines(models.Model):
    _name = "purchase.costing.item.lines"

    costing_item_id = fields.Many2one("purchase.costing.item", string="Cost Item")
    amount = fields.Float()
    order_id = fields.Many2one("purchase.order")
