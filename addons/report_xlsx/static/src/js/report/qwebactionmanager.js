/** @odoo-module **/
// © 2017 Creu Blanca
// License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";

async function xlsxReportHandler(action, options, env) {
    if (action.report_type === "xlsx") {
        const reportUrl = `/report/xlsx/${action.report_name}`;
        let url = reportUrl;
        if (action.context && action.context.active_ids) {
            url += `/${action.context.active_ids.join(",")}`;
        }
        env.services.ui.block();
        try {
            await download({
                url: "/report/xlsx/" + action.report_name,
                data: {
                    data: JSON.stringify([url, action.report_type]),
                    context: JSON.stringify(action.context),
                },
            });
        } finally {
            env.services.ui.unblock();
        }
        const onClose = options.onClose;
        if (action.close_on_report_download) {
            env.services.action.doAction(
                { type: "ir.actions.act_window_close" },
                { onClose }
            );
            return true;
        } else if (onClose) {
            onClose();
        }
        return true;
    }
    return false;
}

registry
    .category("ir.actions.report handlers")
    .add("xlsx_handler", xlsxReportHandler);
