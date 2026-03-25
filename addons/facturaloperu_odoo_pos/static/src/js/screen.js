odoo.define('facturaloperu_odoo_pos.pos_screens', function(require) {
  "use strict";

  var core = require('web.core');
  var screens = require('point_of_sale.screens');
  var models = require('point_of_sale.models');
  var PaymentScreenWidget = screens.PaymentScreenWidget;
  var ClientListScreenWidget = screens.ClientListScreenWidget;
  var ReceiptScreenWidget = screens.ReceiptScreenWidget;


  var Qweb = core.qweb;
  var _t = core._t;
  var _super_order = models.Order.prototype;

  models.PosModel.prototype.models.some(function (model) {
    if (model.model !== 'res.company') {
      return false;
    }
    ['street','city', 'state_id', 'province_id', 'district_id', 'ubigeo'].forEach(function (field) {
      if (model.fields.indexOf(field) == -1) {
        model.fields.push(field);
      }
    });
    return true;
  });

  models.PosModel.prototype.models.push({
    model: 'einvoice.catalog.06',
    fields: [
      'name',
      'code'
    ],
    domain:  function(self){
      return [];
    },
    context: function(self){
      return {};
    },
    loaded: function(self, doc_types){
      self.doc_types = doc_types;
    },
  });

  models.PosModel.prototype.models.push({
    model: 'pos.order.document.type',
    fields: [
      'name',
      'number',
    ],
    domain:  function(self){
      return [];
    },
    context: function(self){
      return {};
    },
    loaded: function(self, pos_doc_types){
      self.pos_doc_types = pos_doc_types;
    },
  });

  models.PosModel.prototype.models.push({
    model: 'account.journal',
    fields: [
      'name',
      'sequence_number_next',
      'code',
      'company_id',
    ],
    domain:  function(self){
      return [];
    },
    context: function(self){
      return {};
    },
    loaded: function(self, pos_account_journal){
      self.pos_account_journal = pos_account_journal;
    },
  });

  models.PosModel.prototype.models.push({
    model: 'pos.order.serial.number',
    fields: [
    'name',
    'document_type_id',
    'document_type_name',
    'document_type_number',
  ],
    domain:  function(self){
      return [];
    },
    context: function(self){
      return {};
    },
    loaded: function(self, serial_numbers){
      self.serial_numbers = serial_numbers;
    },
  });

  models.PosModel.prototype.models.push({
    model: 'stock.warehouse',
    fields: [
    'name',
    'code',
    'establishment_code',
  ],
    domain:  function(self){
      return [];
    },
    context: function(self){
      return {};
    },
    loaded: function(self, warehouses){
      self.warehouses = warehouses;
    },
  });

  models.load_fields('res.partner', ['doc_number', 'catalog_06_id', 'state', 'ubigeo'])
  models.load_fields('pos.order', ['api_external_id', 'api_number_feapi', 'api_link_cdr', 'api_link_pdf', 'api_link_xml','el_numero'])

  models.Order = models.Order.extend({
    initialize: function() {
      _super_order.initialize.apply(this, arguments);
      var order = this.pos.get_order();
      this.api_number_feapi = this.api_number_feapi || '';
      this.api_external_id = this.api_external_id || '';
      this.api_link_cdr = this.api_link_cdr || '';
      this.api_link_xml = this.api_link_xml || '';
      this.api_link_pdf = this.api_link_pdf || '';
      this.api_code_json = this.api_code_json || '';
      this.api_qr = this.api_qr || '';
      this.serial_number = this.serial_number || '';
      this.document_type_number = this.document_type_number || '';
      this.l10n_pe_pos_auto_invoice = this.l10n_pe_pos_auto_invoice || '';
      this.save_to_db();
      if (this.pos.config.l10n_pe_pos_auto_invoice) {
        this.to_invoice = true;
      }
      return this
    },
    init_from_JSON: function (json) {
        var res = _super_order.init_from_JSON.apply(this, arguments);
        if (json.to_invoice) {
            this.to_invoice = json.to_invoice;
        }
        if (json.l10n_pe_invoice_journal_id) {
            this.l10n_pe_invoice_journal_id = json.l10n_pe_invoice_journal_id;
        }
        if (json.l10n_pe_currency_id) {
            this.l10n_pe_currency_id = json.l10n_pe_currency_id;
        }
        return res;
    },
    export_as_JSON: function() {
      var json = _super_order.export_as_JSON.apply(this,arguments);
      json.api_external_id = this.api_external_id;
      json.api_number_feapi = this.api_number_feapi;
      json.api_link_cdr = this.api_link_cdr;
      json.api_link_xml = this.api_link_xml;
      json.api_link_pdf = this.api_link_pdf;
      json.api_code_json = this.api_code_json;
      json.api_qr = this.api_qr;
      if (this.l10n_pe_invoice_journal_id) {
        json.l10n_pe_invoice_journal_id = this.l10n_pe_invoice_journal_id;
      }
      if (this.l10n_pe_currency_id) {
        json.l10n_pe_currency_id = this.l10n_pe_currency_id;
      }
      return json;
    },
    set_l10n_pe_invoice_journal: function(l10n_pe_invoice_journal_id){
        this.assert_editable();
        this.set('l10n_pe_invoice_journal_id', l10n_pe_invoice_journal_id);
    },
    get_l10n_pe_invoice_journal: function(){
        return this.get('l10n_pe_invoice_journal_id');
    },
    set_l10n_pe_currency: function(l10n_pe_currency_id){
        this.assert_editable();
        this.set('l10n_pe_currency_id', l10n_pe_currency_id);
    },
    get_l10n_pe_currency: function(){
        return this.get('l10n_pe_currency_id');
    },
  });

  ClientListScreenWidget.include({
    save_client_details: function(partner) {
      var self = this;
      var fields = {};
      this.$('.client-details-contents .detail').each(function(idx,el){
        fields[el.name] = el.value || false;
      });

      if (fields.vat) {
        fields.doc_number = fields.vat;
      }

      if (!fields.doc_number || !fields.catalog_06_id || !fields.vat) {
        this.gui.show_popup(
          'error',
          'Debe llenar los campos de Tipo de Documento y Número de Documento en el formulario del cliente.'
        );
        return;
      }
      this._super(partner);
    },
  });

  PaymentScreenWidget.include({
    get_document_type_number: function(serial_number_selected) {
      var document_type_number = ''
      for (var i = 0; i < this.pos.serial_numbers.length; i++) {
        var serial_number = this.pos.serial_numbers[i];
        if (serial_number.name == serial_number_selected) {
          document_type_number = serial_number.document_type_number;
          break;
        }
      }
      return document_type_number;
    },
    click_invoice_journal: function (journal) {
        var order = this.pos.get_order();
        order.l10n_pe_invoice_journal_id = journal.data('id');
        $('.journal').removeClass('highlight');
        $('.journal').addClass('lowlight');
        var $journal_selected = $("[data-id='" +  order.l10n_pe_invoice_journal_id  + "']");
        $journal_selected.addClass('highlight');
    },
    render_invoice_journals: function () {
        var self = this;
        var methods = $(Qweb.render('journal_list', {widget: this}));
        methods.on('click', '.journal', function () {
            self.click_invoice_journal($(this));
        });
        return methods;
    },
    renderElement: function() {
      var self = this;
      this._super();
      if (this.pos.config.l10n_pe_invoice_journal_ids && this.pos.config.l10n_pe_invoice_journal_ids.length > 0 && this.pos.journals) {
        var methods = this.render_invoice_journals();
        methods.appendTo(this.$('.invoice_journals'));
      }
    },
    show_alert: function(title, message) {
      var self = this;
      self.gui.show_popup('confirm', {
        title: title,
        body:  message,
        confirm: function(){
          self.gui.show_screen('clientlist');
        },
      });
    },
    order_is_valid: function(force_validation) {
      var self = this;
      var sup = this._super(force_validation);
      var order = this.pos.get_order();

      if (!sup) {
        return false;
      }

      var journal_list = self.pos.journals;
      var journal_id_active = order.l10n_pe_invoice_journal_id;
      var journal_active = '';
      journal_list.forEach(function (journal) {
        if (journal.id == journal_id_active){
          order.journal_active = journal;
        };
      });

      // Validations

      var client = order.get_client();
      var client_doc_type = this.pos.doc_types.filter(function(doc_type) {
        return doc_type.id == client.catalog_06_id[0]
      })[0].code
      if (!client) {
        //no hay cliente
        this.show_alert('Error en cliente','Debe seleccionar un cliente para avanzar con la venta.');
        return false;
      }
      if (!client_doc_type) {
        //no tiene tipo de documento
        this.show_alert('Error en datos del cliente','El cliente seleccionado no tiene el tipo de documento registrado, por favor actualice la información del cliente.');
        return false;
      }
      if (!client.doc_number) {
        //no tiene numero de documento
        this.show_alert('Error en datos del cliente','El cliente seleccionado no tiene el número de documento registrado, por favor actualice la información del cliente.');
        return false;
      }

      if (!order.journal_active) {
        //si no selecciona metodo de facturacion
        self.gui.show_popup('error', {
          title: 'Error',
          body:  'Debe seleccionar una opción de método de facturación.'
        });
        return false;
      };

      if (order.journal_active.l10n_pe_sunat_code == '03' && order.get_total_with_tax() > '700') {
        //si es boleta y monto es mayor a 700
        if (client_doc_type == '0' || client_doc_type == '6' || client_doc_type == '-') {
          //si tipo de documento es no.trib o ruc o varios
          this.show_alert('Error en datos del cliente','El tipo de documento seleccionado no puede ser procesado, por favor actualice la información del cliente.');
          return false;
        };
      };
      if (order.journal_active.l10n_pe_sunat_code == '01') {
        //si es factura
        if (client_doc_type != '6') {
          //si tipo de documento no es ruc
          this.show_alert('Error en datos del cliente','El tipo de documento seleccionado debe ser RUC, por favor actualice la información del cliente.');
          return false;
        };
      };

      if (!this.pos.config.is_facturalo_api || this.pos.config.facturalo_endpoint_state != 'success'){
        //si no configuro endpoint
        self.gui.show_popup('error', {
          title: 'Error',
          body:  'No se encuentra conectado al API'
        });
        return false;
      };

      return true
    },
  });

  ReceiptScreenWidget.include({
    send_facturalo_request: function(url, token, data) {
      var request = $.ajax({
        url: url,
        method: "POST",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(data),
        cache: false,
        beforeSend: function(xhr) {
          xhr.setRequestHeader(
            "Authorization",
            'Bearer ' + token
          );
          xhr.setRequestHeader("Access-Control-Allow-Origin", "*");
        },
      })
      return $.when(
        request
      )
    },
    json_generate: function() {
      var self = this;
      var order = this.pos.get_order();


      var send_mail = self.pos.config.iface_api_send_email;

      var stock_location = self.pos.config.stock_location_id;
      var code_stock_location = '0000';
      for (var i = self.pos.warehouses.length - 1; i >= 0; i--) {
        if (stock_location[1].includes(self.pos.warehouses[i].code)) {
          code_stock_location = self.pos.warehouses[i].establishment_code;
        }
      }

      var company = self.pos.company;
      var currency = self.pos.currency;
      var orderLines = order.get_orderlines();

      var now = moment();
      var order_date_formatted = now.format('YYYY-MM-DD');
      var order_time = now.format('HH:mm:ss');

      var amount_with_tax = order.get_total_with_tax();
      var total_without_tax = order.get_total_without_tax();
      var amount_tax = order.get_total_tax();

      var items = [];
      var totals_discount = 0;
      var totals_igv = 0;

      var total_gratuito = 0;
      var total_gratuito_gravado = 0;

      var client = order.get_client();
      var client_doc_type = this.pos.doc_types.filter(function(doc_type) {
        return doc_type.id == client.catalog_06_id[0]
      })[0].code

      var doc_number = order.invoice_number.substring(5,order.invoice_number.length)

      for (var i = 0; i < orderLines.length; i++) {

        //linea
        var line = orderLines[i];
        var product = line.get_product();
        var product_quantity = line.get_quantity();

        // detalles de impuesto
        var taxDetails = line.get_tax_details();
        var product_taxes_total = 0.0;
        for(var id in taxDetails){
          product_taxes_total += taxDetails[id]; //monto total del igv
        }

        // precio de linea / original o asignado
        var price = '';
        if(line.price_manually_set == true){
          price = line.price;
        }else {
          price = product.list_price;
        }

        // monto del descuento basado en porcentaje
        var monto_descuento_unidad = (price * line.discount) / 100;
        // precio por unidad
        var precio_unidad = price - monto_descuento_unidad;
        // cantidad de porcentaje de linea
        var monto_descuento_linea = monto_descuento_unidad * product_quantity;

        // total linea
        var monto_total_linea = precio_unidad * product_quantity;
        // valor unidad sin igv
        var igv_unidad = line.get_tax() / product_quantity;
        var valor_unidad = price - igv_unidad;

        // totales->total_descuentos
        totals_discount = totals_discount + monto_descuento_linea;

        totals_igv = totals_igv + line.get_tax();
        var monto_base = price * product_quantity


        var unidades = this.pos.units;
        var uni = product.uom_id[1];
        var unidad = unidades.find(function(element) {
          return element.display_name == uni;
        });
        var product_uom = unidad.code;

        var total_sin_impuesto = monto_total_linea - line.get_tax();

        items.push({
          "codigo_interno": product.default_code,
          "descripcion": product.display_name,
          "codigo_producto_de_sunat": "",
          "unidad_de_medida": product_uom,
          "cantidad": product_quantity,
          "valor_unitario": valor_unidad.toFixed(2),
          "codigo_tipo_precio": "01",
          "precio_unitario": price.toFixed(2),
          "codigo_tipo_afectacion_igv": "10",
          "descuentos":[
            {
              "codigo": "00",
              "descripcion": "Descuento",
              "factor": line.discount,
              "monto": monto_descuento_linea.toFixed(2),
              "base": monto_base.toFixed(2)
            }
          ],
          "total_base_igv": total_sin_impuesto.toFixed(2),
          "porcentaje_igv": line.get_taxes()[0].amount,
          "total_igv": line.get_tax().toFixed(2),
          "total_impuestos": line.get_tax().toFixed(2),
          "total_valor_item": total_sin_impuesto.toFixed(2),
          "total_item": monto_total_linea.toFixed(2)
        });

        if (line.get_taxes()[0].name == "Gratuito") {
          var precio_line = price / 1.18;
          total_gratuito_gravado = total_gratuito_gravado + total_sin_impuesto.toFixed(2);
          total_gratuito = total_gratuito + monto_total_linea.toFixed(2);
          items[i]['codigo_tipo_afectacion_igv'] = 16;
          items[i]['porcentaje_igv'] = 18;
          items[i]['total_base_igv'] = precio_line;
          items[i]['total_base_isc'] = precio_line;
          items[i]['total_igv'] = price - (precio_line);
          items[i]['codigo_tipo_precio'] = "02";
          items[i]['total_valor_item'] = 0;
          items[i]['total_item'] = 0;
          items[i]['valor_unitario'] = 0;
        }
      }

      //forma de pago
      var payment = order.get_paymentlines()[0].name;
      var method_payment = payment.replace("(","").replace(")","").replace("PEN","").replace("USD","");

      var data = {
        "serie_documento": order.journal_active.code,
        "numero_documento": parseInt(doc_number),
        "fecha_de_emision": order_date_formatted,
        "hora_de_emision": order_time,
        "codigo_tipo_operacion": "0101",
        "codigo_tipo_documento": order.journal_active.l10n_pe_sunat_code,
        "codigo_tipo_moneda": currency.name,
        "factor_tipo_de_cambio": "3.35",
        "fecha_de_vencimiento": order_date_formatted,
        "numero_orden_de_compra": "-",
        "datos_del_emisor": {
          "codigo_del_domicilio_fiscal": code_stock_location
        },
        "datos_del_cliente_o_receptor": {
          "codigo_tipo_documento_identidad": client_doc_type,
          "numero_documento": client.vat,
          "apellidos_y_nombres_o_razon_social": (client.registration_name == false) ? client.registration_name : client.name,
          "codigo_pais": "PE",
          "ubigeo": client.zip,
          "direccion": client.address,
          "correo_electronico": client.email,
        },
        "totales": {
          "total_descuentos": totals_discount,
          "total_operaciones_gravadas": total_without_tax.toFixed(2) - total_gratuito,
          "total_operaciones_inafectas": "0.00",
          "total_operaciones_exoneradas": "0.00",
          "total_operaciones_gratuitas": total_gratuito,
          "total_igv": totals_igv.toFixed(2),
          "total_impuestos": totals_igv.toFixed(2),
          "total_valor": total_without_tax.toFixed(2) - total_gratuito,
          "total_venta": amount_with_tax.toFixed(2) - total_gratuito_gravado,
        },
        "items": items,
        "acciones": {
            "enviar_email": send_mail,
        },
        "leyendas": [],
        "informacion_adicional": "Forma de pago: "+method_payment
      };

      return data;
    },
    get_receipt_render_env: function() {
      var self = this;
      var order = this.pos.get_order();

      console.log('ReceiptScreenWidget', order);

      var url = self.pos.config.iface_facturalo_url_endpoint;
      var token = self.pos.config.iface_facturalo_token;
      var def = $.Deferred();

      order.url_search = url.replace("api/documents", "search");

      var data = this.json_generate();
      console.log('Json', data);
      var code_json = JSON.stringify(data, null, ' ');

      this.send_facturalo_request(url, token, data)
        .done(function(data) {
          let ticket_html = $('.pos-receipt-container')[0].innerHTML;
          var data_response = {
            api_number_feapi: data['data']['number'],
            api_external_id: data['data']['external_id'],
            api_link_cdr: data['links']['cdr'],
            api_link_xml: data['links']['xml'],
            api_link_pdf: data['links']['pdf'],
            api_code_json: code_json,
          }
          var data_to_invoice = {
            number_feapi: data['data']['number'],
            api_number_to_letter: data['data']['number_to_letter'],
            external_id: data['data']['external_id'],
            link_cdr: data['links']['cdr'],
            link_xml: data['links']['xml'],
            link_pdf: data['links']['pdf'],
            api_qr: data['data']['qr'],
            state_api: 'success',
            ticket_html: ticket_html
          }


          var domain = [['pos_reference', '=', order.name], ['session_id', '=', self.pos.pos_session.id]];
          setTimeout(function() {
            // busca la orden
            self._rpc({
              model: 'pos.order',
              method: 'search_read',
              domain: domain,
              fields: ['id','invoice_id'],
            }).done(function(o) {


              // si ya se ha creado la factura se busca para guardar los datos aqui
              var search = [['id', '=', o[0].invoice_id[0]]];
              self._rpc({
                model: 'account.invoice',
                method: 'search_read',
                domain: search,
                fields: ['id'],
              }).done(function(res) {
                // guarda los datos extras en la factura
                self._rpc({
                  model: 'account.invoice',
                  method: 'write',
                  args: [[res[0].id], data_to_invoice],
                }).done(function() {
                  console.log('Se guardaron los datos extras en account.invoice');
                }).fail(function(err) {
                  console.log('No se guardaron los datos extras en account.invoice');
                })
              }).fail(function(err) {
                console.log('no se encontro la factura');
              })


              // si no hay respuesta
              if (o.length == 0) {
                def.reject()
              } else {
                // guarda los datos extras en la orden
                self._rpc({
                  model: 'pos.order',
                  method: 'write',
                  args: [[o[0].id], data_response],
                }).done(function() {
                  def.resolve()
                }).fail(function(err) {
                  new Noty({
                    theme: 'bootstrap-v4',
                    type: 'warning',
                    timeout: 10000,
                    layout: 'bottomRight',
                    text: 'No se guardaron los datos de la api en el pedido'
                  }).show();
                  def.reject()
                })
              }

            }).fail(function(err) {

              new Noty({
                theme: 'bootstrap-v4',
                type: 'warning',
                timeout: 10000,
                layout: 'bottomRight',
                text: 'No se encontró el pedido'
              }).show();
              def.reject()
            })

          }, 3000);

          $('#number-to-letter').append(data['data']['number_to_letter']);
          $('#hash').append(data['data']['hash']);
          $('#qr').html(
            '<img style="margin-top:15px;" class="qr_code" src="data:image/png;base64, ' + data['data']['qr'] + '" />'
          );

          new Noty({
            theme: 'bootstrap-v4',
            type: 'success',
            timeout: 3000,
            layout: 'bottomRight',
            text: '<h3>La operación ha finalizado.</h3>'
          }).show();

        }).fail(function(xhr, status, error) {
          def.reject()
          // console.log(status)
          if (xhr.responseText != '') {
            var err = eval("(" + xhr.responseText + ")");
            self.gui.show_popup('error', {
              title: 'ERROR: Ha ocurrido un error en el envío',
              body: err.message,
            });
            return false;
          } else {
            self.gui.show_popup('error', {
              title: 'ERROR: Ha ocurrido un error en el envío',
              body: 'No se ha obtenido respuesta del servidor',
            });
            return false;
          }
        })

        return {
            widget: this,
            pos: this.pos,
            order: order,
            receipt: order.export_for_printing(),
            orderlines: order.get_orderlines(),
            paymentlines: order.get_paymentlines(),
        };
    },
  });
});
