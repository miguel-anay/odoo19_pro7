/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class ConsultaRucWidget extends Component {
    static template = "l10n_pe_partner_consulta_dni_ruc.ConsultaRucWidget";
    static props = { record: Object, readonly: { type: Boolean, optional: true } };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async onClick() {
        const record = this.props.record;
        const vat = record.data.vat;

        if (!vat) {
            this.notification.add("Ingrese el número de documento", { type: "warning" });
            return;
        }

        // Determinar tipo por longitud: 8 = DNI, 11 = RUC
        let docType;
        if (vat.length === 8) {
            docType = "1"; // DNI
        } else if (vat.length === 11) {
            docType = "6"; // RUC
        } else {
            this.notification.add(
                "DNI debe tener 8 dígitos, RUC debe tener 11 dígitos",
                { type: "warning" }
            );
            return;
        }

        try {
            const result = await this.orm.call(
                "res.partner",
                "get_apiperu_data_for_button",
                [vat, docType],
                {}
            );

            if (result && Object.keys(result).length > 0) {
                await record.update(result);
                this.notification.add("Datos cargados correctamente", { type: "success" });
            } else {
                this.notification.add(
                    "No se encontraron datos. Verifique el número de documento.",
                    { type: "warning" }
                );
            }
        } catch (e) {
            this.notification.add(
                "Error al consultar: " + (e.data?.message || e.message || "sin conexión"),
                { type: "danger" }
            );
        }
    }
}

registry.category("view_widgets").add("consulta_ruc", {
    component: ConsultaRucWidget,
});
