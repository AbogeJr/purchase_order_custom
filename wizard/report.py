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


class ExcelWizard(models.TransientModel):
    _name = "purchase.xlsx.wizard"
    start_date = fields.Datetime(
        string="Start Date", default=time.strftime("%Y-%m-01"), required=True
    )
    end_date = fields.Datetime(
        string="End Date", default=datetime.datetime.now(), required=True
    )

    def print_xlsx(self):
        print("\n\n Print XLSX \n\n")
        if self.start_date > self.end_date:
            raise ValidationError("Start Date must be less than End Date")
        data = {
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
        return {
            "type": "ir.actions.report",
            "data": {
                "model": "purchase.order",
                "options": json.dumps(data, default=date_utils.json_default),
                "output_format": "xlsx",
                "report_name": "Excel Report",
            },
            "report_type": "xlsx",
        }
