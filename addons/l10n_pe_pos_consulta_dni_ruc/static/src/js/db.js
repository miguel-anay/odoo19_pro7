odoo.define('l10n_pe_pos_consulta_dni_ruc.db', function (require) {
    "use strict";

    var core = require('web.core');
    var db = require('point_of_sale.DB');
    var _t      = core._t;

    db.include({
        _partner_search_string: function(partner){
            var str =  partner.name;
            if(partner.barcode){
                str += '|' + partner.barcode;
            }
            if(partner.address){
                str += '|' + partner.address;
            }
            if(partner.phone){
                str += '|' + partner.phone.split(' ').join('');
            }
            if(partner.mobile){
                str += '|' + partner.mobile.split(' ').join('');
            }
            if(partner.email){
                str += '|' + partner.email;
            }
            if(partner.vat){
                str += '|' + partner.vat;
            }
            str = '' + partner.id + ':' + str.replace(':','') + '\n';
            return str;
        },
    });
});

