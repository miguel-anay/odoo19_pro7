# FacturadorPeru Pro7 — Odoo 19

Sistema de facturación electrónica peruana integrado con **Odoo 19**, con emisión de comprobantes a través de la API **FacturaloPeru Pro V5** y cumplimiento total con los requisitos de la **SUNAT**.

---

## ¿Qué hace este proyecto?

- Emite facturas, boletas, notas de crédito/débito y guías de remisión electrónicas a SUNAT
- Integra el punto de venta (POS) con facturación electrónica
- Consulta DNI y RUC en línea directamente desde Odoo y el POS
- Genera reportes PLE (Libros Electrónicos) y kardex de inventario
- Localización peruana completa: ubigeos, tipos de documento, moneda, impuestos IGV

## Stack tecnológico

| Componente | Versión |
|---|---|
| Odoo | 19.0 |
| PostgreSQL | 16 |
| Python | 3.12+ |
| Docker Compose | 3 |

---

## Módulos incluidos

### Core — Facturación electrónica
| Módulo | Descripción |
|---|---|
| `facturaloperu_odoo_facturacion` | Emisión de comprobantes a SUNAT vía API |
| `facturaloperu_odoo_pos` | Integración POS con facturación electrónica |
| `facturaloperu_api_pos` | API FacturaloPeru desde el POS |
| `facturaloperu_odoo_guias` | Guías de remisión electrónicas |
| `facturaloperu_odoo_reportes` | Reportes PLE (Libros Electrónicos) |
| `facturaloperu_odoo_kardex` | Kardex de inventario |

### Base — Localización peruana
| Módulo | Descripción |
|---|---|
| `odoope_einvoice_base` | Base de facturación electrónica |
| `odoope_account` | Configuración contable PE |
| `odoope_product` | Productos con atributos SUNAT |
| `odoope_stock` | Inventario localizado |
| `odoope_toponyms` | Ubigeos (departamentos, provincias, distritos) |
| `odoope_currency` | Tipos de cambio SUNAT |
| `l10n_pe_partner_consulta_dni_ruc` | Consulta DNI/RUC desde contactos |
| `l10n_pe_pos_consulta_dni_ruc` | Consulta DNI/RUC desde el POS |
| `l10n_pe_sunat_data` | Catálogos SUNAT |

### Soporte
| Módulo | Descripción |
|---|---|
| `report_xlsx` | Exportación a Excel |
| `date_range` | Rangos de fechas para reportes |
| `stock_picking_invoice_link` | Enlace transferencias ↔ facturas |
| `web_responsive` | UI responsiva |
| `pos_stock_quantity` | Stock en tiempo real en POS |
| `pos_ticket` | Tickets personalizados POS |
| `enterprise_theme` | Tema visual enterprise |

---

## Instalación

### Prerrequisitos

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- Git
- Puerto **8069** libre

### Instalación automática (recomendada en Linux/macOS)

```bash
git clone <url-del-repo> odoo_pro7
cd odoo_pro7
chmod +x install.sh
./install.sh
```

El script levanta los contenedores, instala dependencias Python y todos los módulos en el orden correcto. Al terminar, Odoo estará disponible en http://localhost:8069.

### Instalación manual (paso a paso)

### 1. Clonar el repositorio

```bash
git clone <url-del-repo> odoo_pro7
cd odoo_pro7
```

### 2. Levantar los contenedores

```bash
docker-compose up -d
```

Esperar ~15 segundos a que PostgreSQL inicialice antes de continuar.

### 3. Instalar dependencias Python

```bash
docker-compose exec -T web pip3 install xlsxwriter phonenumbers xlrd
```

### 4. Instalar los módulos en orden

> **Windows (Git Bash / MSYS2):** agregar `MSYS_NO_PATHCONV=1` al inicio de cada comando.

#### Batch 1 — Base (sin dependencias custom)
```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i odoope_einvoice_base,odoope_account,odoope_product,odoope_stock,odoope_toponyms,odoope_currency \
  --stop-after-init
```

#### Batch 2 — Soporte OCA
```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i report_xlsx,date_range,stock_picking_invoice_link \
  --stop-after-init
```

#### Batch 3 — Core Facturación
```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i facturaloperu_odoo_facturacion \
  --stop-after-init
```

#### Batch 4 — Localización DNI/RUC y SUNAT
```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i l10n_pe_partner_consulta_dni_ruc,l10n_pe_sunat_data \
  --stop-after-init
```

#### Batch 5 — POS
```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i facturaloperu_odoo_pos,facturaloperu_api_pos,l10n_pe_pos_consulta_dni_ruc \
  --stop-after-init
```

#### Batch 6 — Guías de Remisión
```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i facturaloperu_odoo_guias \
  --stop-after-init
```

#### Batch 7 — Reportes y Kardex
```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i facturaloperu_odoo_reportes,facturaloperu_odoo_kardex \
  --stop-after-init
```

#### Batch 8 — UI y POS extras
```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i web_responsive,pos_stock_quantity,pos_ticket,enterprise_theme \
  --stop-after-init
```

### 5. Configurar la contabilidad base

> **Este paso es obligatorio.** Configura el plan de cuentas peruano, los diarios de efectivo/banco y los impuestos IGV necesarios para emitir comprobantes.

```bash
python3 setup_base_contabilidad.py
```

Ver guía completa: [SETUP_CONTABILIDAD.md](SETUP_CONTABILIDAD.md)

### 6. Reiniciar Odoo

```bash
docker restart fp_odoo
```

### 7. Configurar la API FacturaloPeru

Copia el archivo de ejemplo y completa tus credenciales:

```bash
cp setup_facturalo.env.example setup_facturalo.env
```

Edita `setup_facturalo.env` con los datos de tu empresa y la API:

```env
ODOO_URL=http://localhost:8069
ODOO_DB=fp_bd
ODOO_USER=admin
ODOO_PASSWORD=admin

API_URL=https://yiwu.qhipa.org.pe
API_TOKEN=tu_token_aqui

COMPANY_NAME=Mi Empresa S.A.C.
COMPANY_VAT=20123456789
COMPANY_STREET=Av. Principal 123
COMPANY_CITY=Lima
COMPANY_PHONE=01-1234567
COMPANY_EMAIL=facturacion@miempresa.com

WAREHOUSE_ESTABLISHMENT_CODE=0000
```

Luego ejecuta el script de configuración:

```bash
python3 setup_facturalo.py
```

Esto configura automáticamente la empresa, el POS, el almacén y los parámetros de API en Odoo. Alternativamente puedes hacerlo de forma manual en **Ajustes → Compañía → FacturaloPeru**.

---

## Acceso inicial

| Campo | Valor |
|---|---|
| URL | http://localhost:8069 |
| Usuario | `admin` |
| Contraseña | `admin` |

---

## Comandos útiles

```bash
docker-compose up -d              # Iniciar el stack
docker restart fp_odoo            # Reiniciar solo Odoo
docker logs --tail 100 fp_odoo   # Ver logs de Odoo
docker-compose down               # Detener (preserva datos)
docker-compose down -v            # Detener y borrar volúmenes (borra BD)

# Actualizar un módulo ya instalado:
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd -u <modulo> --stop-after-init
```

---

## Notas importantes

- El frontend JS del POS (OWL 2) está pendiente de reescritura; el backend funciona correctamente
- La base de datos `fp_bd` se crea automáticamente en el primer arranque
- Para la configuración completa post-instalación (empresa, series, impuestos, clientes, errores), ver [`CONFIGURACION_INICIAL.md`](CONFIGURACION_INICIAL.md)

---

Autor: [Miguel Anay](https://portfolio.miguel-anay.nom.pe/)
