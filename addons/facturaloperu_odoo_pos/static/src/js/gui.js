odoo.define('facturaloperu_odoo_pos.gui', function (require) {
    "use strict";

    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var session = require('web.session');
    var gui = require('point_of_sale.gui');

    var _t = core._t;

    gui.Gui.include({
        select_currency: function(options){
            options = options || {};
            var self = this;
            var def  = new $.Deferred();

            var list = [];
            for (var i = 0; i < this.pos.currencies.length; i++) {
                var currency = this.pos.currencies[i];
                list.push({
                    'label': currency.name,
                    'item':  currency,
                });
            }

            this.show_popup('selection',{
                title: options.title || 'Seleccionar moneda',
                list: list,
                confirm: function(currency){ def.resolve(currency); },
                cancel: function(){ def.reject(); },
                is_selected: function(currency){ return currency === self.pos.get_currency(); },
            });

            return def.then(function(currency){ return currency; });
        },
    });
});
