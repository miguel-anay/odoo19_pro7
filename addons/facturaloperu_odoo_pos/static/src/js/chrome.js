odoo.define('facturaloperu_odoo_pos.chrome', function (require) {
    "use strict";

    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var chrome = require("point_of_sale.chrome");
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var gui = require('point_of_sale.gui');
    var CrashManager = require('web.CrashManager');

    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    chrome.SynchNotificationWidget = chrome.SynchNotificationWidget.include({
        start: function(){
            var self = this;
            this.pos.bind('change:synch', function(pos,synch){
                self.set_status(synch.state, synch.pending);
            });
            this.$el.click(function(){
                self.pos.push_and_invoice_order(null,{'show_error':true});
            });
        },
    });

    var CurrencyWidget = PosBaseWidget.extend({
        template: 'CurrencyWidget',
        init: function(parent, options){
            options = options || {};
            this._super(parent,options);
        },
        renderElement: function(){
            var self = this;
            this._super();

            this.$el.click(function(){
                self.click_currency();
            });
        },
        click_currency: function(){
            var self = this;
            this.gui.select_currency({
                'security':     true,
                'current_currency': this.pos.get_currency(),
                'title': 'Cambiar moneda',
            }).then(function(currency){
                currency.decimals = 2
                self.pos.db.set_currency(currency);
                self.pos.currency = currency ;
                self.renderElement();
                var order = self.pos.get_order();
                order.l10n_pe_currency_id = currency.id
            });
        },
        get_name: function(){
            var currency = this.pos.get_currency();
            if(currency){
                return currency.name;
            }else{
                return "";
            }
        },
    });

   chrome.Chrome.prototype.widgets.push({
     'name':   'currency',
     'widget': CurrencyWidget,
     'replace':  '.placeholder-CurrencyWidget',
   });

});
