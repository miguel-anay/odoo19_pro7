#!/bin/bash
# FacturadorPeru Pro7 — Instalación automatizada en Odoo 19
# Uso: ./install.sh
# Requisitos: Docker + Docker Compose instalados, puerto 8069 libre

set -e

# Leer ODOO_DB desde setup_facturalo.env si existe, sino usar default
if [ -f setup_facturalo.env ]; then
  export $(grep -E '^ODOO_DB=' setup_facturalo.env | xargs)
fi
ODOO_DB=${ODOO_DB:-fp_bd}

ODOO_CONF="-c /etc/odoo/odoo.conf -d $ODOO_DB"
ODOO="docker-compose exec -T web odoo $ODOO_CONF"

echo ""
echo "======================================"
echo "  FacturadorPeru Pro7 — Odoo 19"
echo "======================================"
echo ""

# 1. Levantar contenedores
echo "[1/6] Levantando contenedores..."
docker-compose up -d

echo "      Esperando que PostgreSQL inicialice..."
sleep 15

# 2. Dependencias Python
echo "[2/6] Instalando dependencias Python..."
docker-compose exec -T web pip3 install xlsxwriter phonenumbers xlrd

# 3. Módulos base
echo "[3/6] Instalando módulos base..."
$ODOO -i odoope_einvoice_base,odoope_account,odoope_product,odoope_stock,odoope_toponyms,odoope_currency --stop-after-init
$ODOO -i report_xlsx,date_range,stock_picking_invoice_link --stop-after-init

# 4. Core facturación y localización
echo "[4/6] Instalando core de facturación..."
$ODOO -i facturaloperu_odoo_facturacion --stop-after-init
$ODOO -i l10n_pe_partner_consulta_dni_ruc,l10n_pe_sunat_data --stop-after-init

# 5. POS, guías, reportes y UI
echo "[5/6] Instalando POS, guías, reportes y UI..."
$ODOO -i facturaloperu_odoo_pos,facturaloperu_api_pos,l10n_pe_pos_consulta_dni_ruc --stop-after-init
$ODOO -i facturaloperu_odoo_guias --stop-after-init
$ODOO -i facturaloperu_odoo_reportes,facturaloperu_odoo_kardex --stop-after-init
$ODOO -i web_responsive,pos_stock_quantity,pos_ticket,enterprise_theme --stop-after-init

# 6. Contabilidad base (plan de cuentas + diarios)
echo "[6/6] Configurando contabilidad base..."
python3 setup_base_contabilidad.py

# Reiniciar Odoo
docker restart fp_odoo

echo ""
echo "======================================"
echo "  Instalación completada"
echo "  Acceder en: http://localhost:8069"
echo "  Usuario: admin  |  Contraseña: admin"
echo "======================================"
echo ""
echo "Siguiente paso obligatorio: configurar la API FacturaloPeru"
echo ""
echo "  1. Copia el archivo de credenciales:"
echo "     cp setup_facturalo.env.example setup_facturalo.env"
echo ""
echo "  2. Edita setup_facturalo.env con tu API_URL, API_TOKEN y datos de empresa"
echo ""
echo "  3. Ejecuta:"
echo "     python3 setup_facturalo.py"
echo ""
