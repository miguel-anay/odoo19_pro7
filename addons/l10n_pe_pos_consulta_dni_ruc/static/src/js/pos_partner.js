odoo.define('l10n_pe_pos_consulta_dni_ruc.pos_bus_restaurant', ["web.core", 'point_of_sale.screens', "web.session", 'point_of_sale.gui', "web.rpc"], function(require) {
    "use strict";
    let session = require("web.session");
    let core = require('web.core');
    let screens = require('point_of_sale.screens');
    let gui = require('point_of_sale.gui');
    //let Model = require('web.Model');
    let rpc = require("web.rpc");
    let _t = core._t;

    screens.ClientListScreenWidget.include({
        rucValido: function(ruc) {
            let ex_regular_ruc;
            ex_regular_ruc = /^\d{11}(?:[-\s]\d{4})?$/;
            if (ex_regular_ruc.test(ruc)) {
                return true
            }
            return false;
        },
        dniValido: function(dni) {
            let ex_regular_dni;
            ex_regular_dni = /^\d{8}(?:[-\s]\d{4})?$/;
            if (ex_regular_dni.test(dni)) {
                return true
            }
            return false;
        },
        saved_client_details2: function(partner_id) {
            let self = this;

            self.reload_partners().then(
                function() {
                    let partner = self.pos.db.get_partner_by_id(partner_id);
                    if (partner) {
                        console.log("Show")
                        self.new_client = partner;
                        self.toggle_save_button();
                        self.display_client_details('show', partner);
                    } else {
                        console.log("Hide");
                        // should never happen, because create_from_ui must return the id of the partner it
                        // has created, and reload_partner() must have loaded the newly created partner. 
                        self.display_client_details('hide');
                    }
                },
                function(err, event) {
                    let partner = self.pos.db.get_partner_by_id(partner_id);
                    console.log(partner)
                    if (partner) {
                        console.log(err);
                        console.log("Hide");
                        self.new_client = partner;
                        self.toggle_save_button();
                        self.display_client_details('show', partner);
                    }

                });
        },
        close: function() {
            this._super();
            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.hide();
            }
        },
        save_client_details: function(partner) {
            let self = this;

            let fields = {};
            this.$('.client-details-contents .detail').each(function(idx, el) {
                fields[el.name] = el.value || false;
            });

            if (!fields.name) {
                this.gui.show_popup('error', _t('A Customer Name Is Required'));
                return;
            }

            if (!fields.zip) {
                this.gui.show_popup('error', _t('Debe agregar ubigeo'));
                return;
            }

            if (!fields.catalog_06_id) {
                this.gui.show_popup('error', _t('Debe agregar tipo de documento'));
                return;
            }

            if (this.uploaded_picture) {
                fields.image = this.uploaded_picture;
            }

            fields.id = partner.id || false;
            fields.country_id = fields.country_id || false;
            /* Tipo de Documento
                2: DNI
                4: RUC
            */

            fields.tipo_doc = fields.catalog_06_id;
            console.log(fields.catalog_06_id);
            console.log(fields.tipo_doc);
            console.log(fields);

            // fields.catalog_06_id = fields.tipo_doc == '2' ? 2 : (fields.tipo_doc == '4' ? 4 : 7);

            if (fields.tipo_doc == '2') {
                fields.company_type = "person"
                // fields.catalog_06_id = 2
                if (fields.vat) {
                    if (!self.dniValido(fields.vat)) {
                        self.gui.show_popup('error', {
                            'title': 'Error',
                            'body': "El DNI ingresado es incorrecto",
                        });
                    }
                } else {
                    self.gui.show_popup('error', {
                        'title': 'Error',
                        'body': "Si coloca que el tipo de documento es DNI, ústed debe completar el campo Documento con el DNI del Cliente.",
                    });
                }
            } else if (fields.tipo_doc == '4') {
                fields.company_type = "company"
                // fields.catalog_06_id = 4
                if (fields.vat) {
                    if (!self.rucValido(fields.vat)) {
                        self.gui.show_popup('error', {
                            'title': 'Error',
                            'body': "El RUC ingresado es incorrecto",
                        });
                    }
                } else {
                    self.gui.show_popup('error', {
                        'title': 'Error',
                        'body': "Si coloca que el tipo de documento es RUC, ústed debe completar el campo Documento con el DNI del Cliente.",
                    });
                }
            }
            rpc.query({
                    model: "res.partner",
                    method: "create_from_ui",
                    args: [fields]
                })
                .then(function(partner_id) {
                    self.saved_client_details2(partner_id);
                }, function(err, event) {
                    self.gui.show_popup('error', {
                        'title': _t('Error: Could not Save Changes'),
                        'body': _t('Your Internet connection is probably down.'),
                    });
                });
        },

        get_datos: function(partner, contents) {
            let self = this;
            let tipo_doc = $('.detail.client-document-types').val();
            console.log(tipo_doc);
            // Si es otro tipo de doc. que no sea dni o ruc ya no consulta.
            if (tipo_doc != '-') {
                let fields = {};
                let contents = this.$('.client-details-contents');

                this.$('.detail.vat').each(function(idx, el) {
                    fields[el.name] = el.value || false;
                });
                if (!fields.vat) {
                    this.gui.show_popup('error', {
                        'title': 'Alerta!',
                        'body': 'Ingrese nro. documento',
                    });
                    return;
                };
                fields.tipo_doc = tipo_doc;
                let context = {}
                rpc.query({
                    model: "res.partner",
                    method: "consulta_datos",
                    args: [tipo_doc == "2" ? "dni" : "ruc", fields.vat],
                    context: _.extend(context, session.user_context || {})
                }).then(function(datos) {
                    if (datos.error) {
                        self.gui.show_popup('error', {
                            'title': 'Alerta!',
                            'body': datos.message,
                        });
                    } else if (datos.data) {
                        if (tipo_doc === '2') {
                            contents.find('input[name="name"]').val(datos.data.nombres + " " + datos.data.ape_paterno + " " + datos.data.ape_materno)
                        } else if (tipo_doc === '4') {
                            contents.find('input[name="name"]').val(datos.data.nombre)
                            contents.find('input[name="zip"]').val(datos.data.ubigeo)
                            contents.find('input[name="ubigeo"]').val(datos.data.ubigeo)
                            contents.find('input[name="street"]').val(datos.data.domicilio_fiscal + "," + datos.data.distrito)
                            contents.find('input[name="city"]').val(datos.data.provincia)
                        }
                    }
                });
            }
        },
        display_client_details: function(visibility, partner, clickpos) {
            this._super(visibility, partner, clickpos);
            let self = this
            let contents = this.$('.client-details-contents');
            contents.off('click', '.button.consulta-datos');
            contents.on('click', '.button.consulta-datos', function() { self.get_datos(partner, contents); });
        },
    });
});