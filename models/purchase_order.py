# -*- coding: utf-8 -*-
import time
import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.tools import date_utils, groupby, float_is_zero
from odoo.exceptions import UserError
import io
import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    landed_costs = fields.One2many("purchase.landed.cost", "purchase_id")

    def print_xlsx_report(self):
        datas = {
            "ids": self.ids,
            "model": "purchase.order",
            "options": json.dumps(
                {
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

    def create_landed_cost(self):
        print("\n\nCREATE LANDED COST\n\n")

        for record in self:
            if not record.landed_costs:
                raise UserError("No landed cost to create.")

            landed_costs_per_vendor = {}

            for line in record.landed_costs:
                if line.vendor_id.id not in landed_costs_per_vendor:
                    landed_costs_per_vendor[line.vendor_id.id] = []
                landed_costs_per_vendor[line.vendor_id.id].append(line)

            print(landed_costs_per_vendor)
            # ceate vendor bill for everyb landed cost per vendor
            AccountMove = self.env["account.move"]
            AccountMoveLine = self.env["account.move.line"]

            for vendor_id, landed_costs in landed_costs_per_vendor.items():
                print(vendor_id, landed_costs)
                invoice = AccountMove.create(
                    {
                        "move_type": "in_invoice",
                        "partner_id": vendor_id,  # Set the customer/partner for the invoice
                        "invoice_date": record.date_approve,  # Set the invoice date
                        "ref": record.name,  # Set the invoice reference
                    }
                )
                for item in landed_costs:
                    # Create the first invoice line
                    if item.state == "done" or item.state == "cancel":
                        continue
                    line = AccountMoveLine.create(
                        {
                            "name": item.name,
                            "product_id": item.product_id.id,
                            "tax_ids": [(6, 0, item.product_id.taxes_id.ids)],
                            "price_unit": item.product_id.list_price,
                            "is_landed_costs_line": True,
                            "purchase_order_id": record.id,
                            "move_id": invoice.id,
                        }
                    )
                    # Create Landed Costs
                    landed_cost = self.env["stock.landed.cost"].create(
                        {
                            "vendor_bill_id": invoice.id,
                            "picking_ids": [(6, 0, record.picking_ids.ids)],
                            "cost_lines": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_id": item.product_id.id,
                                        "name": item.product_id.name,
                                        "account_id": item.account_id.id,
                                        "price_unit": item.price_unit,
                                        "split_method": item.split_method or "equal",
                                    },
                                )
                            ],
                        }
                    )
                    item.state = "done"
                # Set the invoice lines on the invoice
                invoice.write(
                    {
                        "invoice_line_ids": [
                            (4, line.id),
                        ]
                    }
                )

                print("\n\n====vendor bill created====")
                print(invoice.ref)
                print(invoice.name)
            print("=====PICKING ID=====")
            print(record.picking_ids.name)
            print(record.picking_ids.purchase_id)
        return invoice


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    purchase_id = fields.Many2one(
        "purchase.order", string="Last updated By PO", readonly=True
    )
