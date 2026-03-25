odoo.define('facturaloperu_odoo_pos.models', function(require) {
  "use strict";

    var models = require("point_of_sale.models");
    var rpc = require('web.rpc');

    models.load_fields('pos.config', ['print_pdf']);

    var _super_Order = models.Order.prototype;
    var _super_posmodel = models.PosModel.prototype;
    var _super_PosModel = models.PosModel.prototype;

    models.load_models([{
        model: 'account.journal',
        fields: [],
        domain: function (self) {
            return [['id', 'in', self.config.l10n_pe_invoice_journal_ids]];
        },
        loaded: function (self, journals) {
            self.journals = journals;
            self.journal_by_id = {};
            for (var i = 0; i < journals.length; i++) {
                self.journal_by_id[journals[i]['id']] = journals[i];
            }
        }
    },{
        model: 'res.currency',
        fields: ['name','symbol','position','rounding'],
        domain: function (self) {
            return [['id', 'in', self.config.l10n_pe_currency_ids]];
        },
        loaded: function (self, currencies) {
            self.currencies = currencies;
            for(let currency of currencies){
                if(currency.rate == 1){
                    self.set_currency(currency);
                }
            }
        }
    }
    ]);

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var partner_model = _.find(this.models, function (model) {
                return model.model === 'res.partner';
            });
            partner_model.fields.push('vat');
            _super_PosModel.initialize.apply(this, arguments);
        },
        push_and_invoice_pos_order: function (order) {
            var self = this;
            var invoiced = new $.Deferred();

            if (!order.get_client()) {
                invoiced.reject({code: 400, message: 'Missing Customer', data: {}});
                return invoiced;
            }
            var order_id = this.db.add_order(order.export_as_JSON());
            this.flush_mutex.exec(function () {
                var done = new $.Deferred(); // holds the mutex
                var transfer = self._flush_orders([self.db.get_order(order_id)], {timeout: 30000, to_invoice: true});
                transfer.fail(function (error) {
                    invoiced.reject(error);
                    done.reject();
                });
                transfer.pipe(function (order_server_id) {
                    invoiced.resolve();
                    done.resolve();
                });
                return done;
            });
            return invoiced;
        },
        push_and_invoice_order: function () {
            var self = this;
            return self.push_and_invoice_pos_order.apply(this, arguments).then(function () {
                var order = self.get_order();
                self.order = order;
                if (order.is_to_invoice()) {
                    return rpc.query({
                        model: 'pos.order',
                        method: 'search_read',
                        domain: [['pos_reference', '=', order['name']]],
                        fields: ['invoice_id'],
                    }).then(function (orders) {
                        if (orders.length >= 1) {
                            var invoice = orders[0]['invoice_id'];
                            return rpc.query({
                                model: 'account.invoice',
                                method: 'search_read',
                                domain: [['id', '=', invoice[0]]],
                                fields: ['number', 'journal_id'],
                            }).then(function (invoices) {
                                if (invoices.length >= 1) {
                                    self.order.invoice_number = invoices[0]['number'].toUpperCase();
                                    return rpc.query({
                                        model: 'account.journal',
                                        method: 'search_read',
                                        domain: [['id', '=', invoices[0]['journal_id'][0]]],
                                        fields: ['name','sequence_number_next'],
                                    }).then(function (journals) {
                                        self.order.l10n_pe_invoice_journal_id = journals[0]['l10n_pe_invoice_journal_id'];
                                        self.order.journal_number_next = journals[0]['sequence_number_next'];
                                        self.order.journal_name = journals[0]['name'].toUpperCase();
                                    }).fail(function (error) {
                                    })
                                }
                            }).fail(function (error) {
                                console.log(error);
                            })
                        }
                    }).fail(function (error) {
                        console.log(error);
                    })

                    console.log('aqui', order);
                }
            });
        },
        get_currency: function(){
            return this.db.get_currency() || this.get('currency');
        },
        // changes the current cashier
        set_currency: function(currency){
            this.set('currency', currency);
            this.db.set_currency(currency);
        },
    });
});
