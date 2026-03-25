odoo.define('facturaloperu_odoo_pos.DB', function (require) {
    "use strict";

    var core = require('web.core');
    var CrashManager = require('web.CrashManager');
    var DB = require('point_of_sale.DB');

    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    DB.include({
        set_currency: function(currency) {
            this.currency = currency;
            this.save('currency', currency || null);
        },
        get_currency: function() {
            return this.load('currency');
        }
    });

});

