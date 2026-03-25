# Copyright (C) 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.web.controllers.report import ReportController as WebReportController
from odoo.http import content_disposition, route, request

import json


class ReportController(WebReportController):
    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == 'xlsx':
            report_obj = request.env['ir.actions.report']._get_report_from_name(
                reportname)
            context = dict(request.env.context)
            if docids:
                docids = [int(i) for i in docids.split(',')]
            if data.get('options'):
                data.update(json.loads(data.pop('options')))
            if data.get('context'):
                data['context'] = json.loads(data['context'])
                if data['context'].get('lang'):
                    del data['context']['lang']
                context.update(data['context'])
            xlsx = request.env['ir.actions.report'].with_context(**context)._render_xlsx(
                reportname, docids, data=data
            )[0]
            xlsxhttpheaders = [
                ('Content-Type', 'application/vnd.openxmlformats-'
                                 'officedocument.spreadsheetml.sheet'),
                ('Content-Length', len(xlsx)),
                (
                    'Content-Disposition',
                    content_disposition(report_obj.report_file + '.xlsx')
                )
            ]
            return request.make_response(xlsx, headers=xlsxhttpheaders)
        return super(ReportController, self).report_routes(
            reportname, docids, converter, **data
        )
