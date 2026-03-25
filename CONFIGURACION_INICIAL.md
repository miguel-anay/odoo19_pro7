# Guía de Configuración Inicial — Odoo 19 FacturadorPeru

Guía completa para dejar el sistema listo desde cero: instalación Docker, módulos, empresa, API, series, clientes y primer comprobante.

---

## Índice

1. [Prerrequisitos y Docker](#1-prerrequisitos-y-docker)
2. [Instalar módulos](#2-instalar-módulos)
3. [Plan de cuentas y diarios contables](#3-plan-de-cuentas-y-diarios-contables)
4. [Configurar datos de la empresa](#4-configurar-datos-de-la-empresa)
5. [Configurar la API FacturaloPeru](#5-configurar-la-api-facturalo-peru)
6. [Crear series de facturación (Diarios SUNAT)](#6-crear-series-de-facturación-diarios-sunat)
7. [Configurar impuestos (IGV)](#7-configurar-impuestos-igv)
8. [Configurar unidades de medida](#8-configurar-unidades-de-medida)
9. [Configurar cuentas bancarias de la empresa](#9-configurar-cuentas-bancarias-de-la-empresa)
10. [Configurar clientes / contactos](#10-configurar-clientes--contactos)
11. [Primer flujo de facturación](#11-primer-flujo-de-facturación)
12. [Reportes PDF disponibles](#12-reportes-pdf-disponibles)
13. [Configuración del Punto de Venta (POS)](#13-configuración-del-punto-de-venta-pos)
14. [Errores comunes y soluciones](#14-errores-comunes-y-soluciones)

---

## 1. Prerrequisitos y Docker

### Requisitos del servidor

- Docker Engine + Docker Compose instalados
- Puerto `8069` libre
- Git instalado
- 2 GB RAM mínimo (4 GB recomendado)

### Clonar y levantar

```bash
git clone <url-del-repo> odoo_pro7
cd odoo_pro7
docker-compose up -d
```

Esperar ~15 segundos hasta que Postgres esté listo. Verificar:

```bash
docker logs --tail 30 fp_odoo
# Debe mostrar: "Modules loaded." sin errores críticos
```

### Instalar dependencias Python adicionales

```bash
docker-compose exec -T web pip3 install xlsxwriter phonenumbers xlrd
```

### Comandos útiles Docker

```bash
docker-compose up -d              # Iniciar stack
docker restart fp_odoo            # Reiniciar solo Odoo (tras cambios de código)
docker logs --tail 100 fp_odoo   # Ver logs en tiempo real
docker-compose down               # Parar (preserva datos)
docker-compose down -v            # Parar y borrar BD (reset total)
```

---

## 2. Instalar módulos

> **Nota Windows (Git Bash/MSYS2):** anteponer `MSYS_NO_PATHCONV=1` a cada comando.

Instalar en este orden. Cada batch debe completarse antes de iniciar el siguiente.

### Batch 1 — Base peruana

```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i odoope_einvoice_base,odoope_account,odoope_product,odoope_stock,odoope_toponyms,odoope_currency \
  --stop-after-init
```

### Batch 2 — Módulos OCA de soporte

```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i report_xlsx,date_range,stock_picking_invoice_link \
  --stop-after-init
```

### Batch 3 — Core Facturación SUNAT

```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i facturaloperu_odoo_facturacion \
  --stop-after-init
```

### Batch 4 — Consulta DNI/RUC (SUNAT)

```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i l10n_pe_partner_consulta_dni_ruc,l10n_pe_sunat_data \
  --stop-after-init
```

### Batch 5 — Punto de Venta

```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i facturaloperu_odoo_pos,facturaloperu_api_pos,l10n_pe_pos_consulta_dni_ruc \
  --stop-after-init
```

### Batch 6 — Guías de Remisión

```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i facturaloperu_odoo_guias \
  --stop-after-init
```

### Batch 7 — Reportes y Kardex

```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i facturaloperu_odoo_reportes,facturaloperu_odoo_kardex \
  --stop-after-init
```

### Batch 8 — UI y extras POS

```bash
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -d fp_bd \
  -i web_responsive,pos_stock_quantity,pos_ticket,enterprise_theme \
  --stop-after-init
```

### Reiniciar

```bash
docker restart fp_odoo
```

Ingresar a `http://localhost:8069` — usuario `admin`, contraseña `admin`.

---

## 3. Plan de cuentas y diarios contables

Obligatorio antes de usar Contabilidad o POS.

### Opción A — Script automático (recomendado)

```bash
python3 setup_base_contabilidad.py
```

### Opción B — Por UI

#### Paso 3.1 — Activar modo desarrollador

`Ajustes → General → Activar el modo desarrollador`
O: abrir `http://localhost:8069/web?debug=1`

#### Paso 3.2 — Instalar plan de cuentas peruano (PCGE)

`Ajustes → sección Contabilidad → Paquete de localización fiscal`

Seleccionar: **Perú - Plan de Cuentas (PCGE)** → Guardar.

Verificar en `Contabilidad → Contabilidad → Plan de cuentas` (debe haber cuentas del 1 al 9).

#### Paso 3.3 — Crear diario de Efectivo

`Contabilidad → Configuración → Diarios → Nuevo`

| Campo   | Valor      |
|---------|-----------|
| Nombre  | Efectivo   |
| Tipo    | Efectivo   |
| Código  | CASH       |
| Moneda  | PEN        |

#### Paso 3.4 — Crear diario de Banco (opcional)

| Campo            | Valor                              |
|------------------|------------------------------------|
| Nombre           | Banco                              |
| Tipo             | Banco                              |
| Código           | BNK                                |
| Moneda           | PEN                                |
| Número de cuenta | N° de cuenta bancaria de la empresa|

> **Importante:** estos diarios (Efectivo, Banco) son para contabilidad general y métodos de pago en POS. Son **distintos** a los diarios de facturación SUNAT (F002, B002) que se crean en el paso 6.

---

## 4. Configurar datos de la empresa

`Ajustes → Usuarios y Empresas → Empresas → (tu empresa)`

### Pestaña "Información General"

| Campo               | Descripción                                  | Ejemplo                         |
|---------------------|----------------------------------------------|---------------------------------|
| Nombre de la empresa| Razón social completa                        | YIWU IMPORT CORPORATION E.I.R.L.|
| RUC                 | Campo `NIF / CIF` — 11 dígitos               | 20610448578                     |
| Calle               | Dirección fiscal completa                    | JR. UCAYALI 553                 |
| Ciudad              | Distrito                                     | LIMA                            |
| Estado              | Departamento                                 | Lima                            |
| País                | País                                         | Perú                            |
| Teléfono            | Teléfono principal                           | 992011852                       |
| Correo electrónico  | Email de facturación                         | admin@empresa.com               |
| Sitio web           | Aparece en los reportes PDF                  | empresa.pe                      |

> **Nota:** el RUC va en el campo "NIF / CIF" (Tax ID). El sistema lo muestra como "RUC" en los reportes por ser Perú.

### Pestaña "API" (FacturaloPeru)

| Campo        | Descripción                                       |
|--------------|---------------------------------------------------|
| URL          | URL base del Facturador PRO (sin `/documents`)    |
| API Token    | Token Bearer obtenido desde el Facturador PRO     |
| Envío email  | Activar para enviar el PDF al cliente automáticamente |

Ejemplo de URL: `https://mi-empresa.qhipa.org.pe/api`

---

## 5. Configurar la API FacturaloPeru

### 5.1 Token y URL en la empresa

Ver paso 4 — pestaña "API".

### 5.2 Parámetro del sistema (modo desarrollador)

`Ajustes → Técnico → Parámetros → Parámetros del sistema`

Buscar o crear:

| Clave                                      | Valor                                  |
|--------------------------------------------|----------------------------------------|
| `facturaloperu_odoo_facturacion.api_url`   | `https://mi-empresa.qhipa.org.pe/api/documents` |

> Este parámetro es el que usan los módulos internamente para llamar a la API.

### 5.3 Verificar conectividad

Crear una factura de prueba → botón **"Json generado"** → si no hay errores de conexión, la API está configurada correctamente.

---

## 6. Crear series de facturación (Diarios SUNAT)

Cada serie de SUNAT (F001, F002, B001, B002…) es un **Diario** en Odoo con configuración especial.

`Contabilidad → Configuración → Diarios → Nuevo`

### Campos obligatorios

| Campo                    | Factura          | Boleta            |
|--------------------------|------------------|-------------------|
| Nombre                   | Facturas F002    | Boletas B002      |
| Tipo                     | Ventas           | Ventas            |
| **Código** ⚠️             | `F002`           | `B002`            |
| Tipo de documento (SUNAT)| (01) Factura     | (03) Boleta de Venta |
| Moneda                   | PEN              | PEN               |

> **El Código es crítico.** Este valor se usa como `serie_documento` al enviar a SUNAT. Debe coincidir exactamente con la serie registrada en FacturaloPeru PRO.

### Por qué el código importa

Cuando se crea la factura `F 00000046` en Odoo, el sistema toma:
- **Serie**: `journal.code` → `F002`
- **Correlativo**: número del `l10n_latam_document_number` → `46`
- **Número SUNAT**: `F002-00000046` (se muestra en verde en la factura)

El Facturador PRO mantiene su propia secuencia por serie. Si creas una nueva serie `F003` el día de mañana, el correlativo en SUNAT comenzará en 1 independientemente del correlativo interno de Odoo.

### Tipo de documento por serie

| Serie | Código SUNAT | Tipo                    |
|-------|-------------|-------------------------|
| F001  | 01          | FACTURA                 |
| F002  | 01          | FACTURA                 |
| B001  | 03          | BOLETA DE VENTA         |
| B002  | 03          | BOLETA DE VENTA         |
| FC01  | 07          | NOTA DE CRÉDITO         |
| FD01  | 08          | NOTA DE DÉBITO          |
| T001  | 09          | GUÍA DE REMISIÓN        |

### Cambiar el correlativo interno de Odoo

Si necesitas que el correlativo de Odoo empiece en un número específico (ej. para sincronizar con SUNAT):

`Contabilidad → Configuración → Diarios → (seleccionar diario) → pestaña Asientos → Secuencia`

O desde: `Ajustes → Técnico → Secuencias` (buscar la secuencia del diario).

> La secuencia de Odoo y la de FacturaloPeru son **independientes**. Odoo lleva el control interno (`F 00000046`), FacturaloPeru lleva el registro ante SUNAT (`F002-46`). Ambos números aparecen en la factura para evitar confusiones.

---

## 7. Configurar impuestos (IGV)

`Contabilidad → Configuración → Impuestos`

Para cada impuesto activo, hacer clic → pestaña **"Opciones avanzadas"**:

| Impuesto          | Campo SUNAT          | Valor   |
|-------------------|---------------------|---------|
| IGV 18%           | Tipo según SUNAT     | `1000`  |
| IGV Exonerado     | Tipo según SUNAT     | `9997`  |
| IGV Inafecto      | Tipo según SUNAT     | `9998`  |
| IGV Gratuito      | Tipo según SUNAT     | `9996`  |

### Incluir impuesto en el precio

Para boletas (precio con IGV incluido):

`Contabilidad → Configuración → Impuestos → IGV 18% → Opciones avanzadas`
→ Activar **"Incluir en el precio"**

> **Importante:** las boletas de venta en Perú siempre deben mostrar precios con IGV incluido. Las facturas pueden mostrar precio sin IGV.

---

## 8. Configurar unidades de medida

`Facturación → Configuración → Unidades de Medida`
(o `Inventario → Configuración → Unidades de Medida`)

Cada unidad usada en productos debe tener su **código SUNAT**:

| Unidad    | Código SUNAT |
|-----------|-------------|
| Unidades  | `NIU`       |
| Kilogramos| `KGM`       |
| Litros    | `LTR`       |
| Metro     | `MTR`       |
| Servicio  | `ZZ`        |
| Caja      | `BX`        |

`Editar → campo "Código SUNAT"` → Guardar.

> Sin el código SUNAT, la API rechaza el comprobante con error de unidad de medida.

---

## 9. Configurar cuentas bancarias de la empresa

Las cuentas bancarias aparecen automáticamente en los reportes **PDF-A4** y **PDF Ticket 80ml**.

`Contabilidad → Configuración → Diarios → Banco → Cuenta bancaria`

O directamente desde la empresa:
`Ajustes → Usuarios y Empresas → Empresas → (tu empresa) → pestaña "Información General" → sección "Cuentas bancarias"`

| Campo             | Descripción                         |
|-------------------|-------------------------------------|
| Número de cuenta  | Número de cuenta bancaria           |
| Banco             | Entidad bancaria (Interbank, BCP…)  |
| CCI               | Campo `Número de compensación`      |
| Moneda            | PEN o USD según la cuenta           |

> El CCI (Código de Cuenta Interbancario) se guarda en el campo **"Número de compensación"** (`clearing_number`) del registro de cuenta bancaria.

---

## 10. Configurar clientes / contactos

Una configuración incorrecta del cliente causa rechazo por parte de SUNAT.

`Contactos → (seleccionar cliente) → Editar`

### Campos obligatorios para SUNAT

| Campo                  | Dónde configurar              | Ejemplo                          |
|------------------------|-------------------------------|----------------------------------|
| Razón social           | Nombre del contacto           | SODEXO PERU S.A.C.               |
| **Tipo de documento**  | Campo `Tipo de documento SUNAT` | (6) RUC / (1) DNI              |
| **Número de documento**| Campo `NIF / CIF`             | 20414766308                      |
| Calle                  | Dirección                     | JR. DOMENICO MORELLI NRO 110     |
| Ciudad                 | Ciudad                        | LIMA                             |
| Estado/Provincia       | Departamento                  | Lima                             |
| País                   | País                          | Perú                             |
| Código postal (ubigeo) | Código postal                 | 150101                           |

### Tipos de documento frecuentes

| Código | Tipo                              | Uso                      |
|--------|-----------------------------------|--------------------------|
| 6      | RUC                               | Empresas → Facturas      |
| 1      | DNI                               | Personas → Boletas       |
| 0      | Otros tipos de documentos         | Extranjeros → Boletas    |
| 7      | Pasaporte                         | Extranjeros              |
| 4      | Carnet de Extranjería             | Extranjeros              |

> **Error común:** si el cliente no tiene dirección completa (calle, ciudad, departamento) o el ubigeo está vacío, la API de FacturaloPeru rechaza el comprobante con error de integridad en los datos de ubicación.

### Clientes sin RUC (boletas)

Para clientes que no dan datos (boleta genérica):
- Tipo de documento: `(0) Otros tipos`
- NIF/CIF: `00000000` (u otro código genérico)
- Nombre: `CLIENTES VARIOS`

---

## 11. Primer flujo de facturación

### Paso 1 — Crear factura

`Facturación → Clientes → Facturas → Nuevo`

| Campo              | Valor                                      |
|--------------------|--------------------------------------------|
| Cliente            | Seleccionar cliente configurado            |
| Fecha de factura   | Fecha de emisión                           |
| Diario             | Seleccionar la serie (ej. "Facturas F002") |
| Tipo de Documento  | Se asigna automáticamente según el diario  |

Agregar líneas de producto con cantidad, precio e impuesto IGV.

### Paso 2 — Confirmar (Publicar)

Clic en **"Confirmar"** o **"Registrar"**.

El número interno de Odoo se asigna: `F 00000001`.
Debajo del título aparece el **número SUNAT en verde**: `F002-1` (preview antes de enviar).

### Paso 3 — Enviar a SUNAT

Clic en **"Enviar SUNAT"** (botón naranja en el header).

El sistema:
1. Genera el JSON con los datos del comprobante
2. Envía al endpoint de FacturaloPeru PRO
3. Descarga el XML y CDR de SUNAT
4. Almacena el QR y el monto en letras
5. Actualiza el número oficial: `F002-00000001`
6. Cambia el estado API a **Aceptado** ✓

> Si el estado queda en **Rechazado**: clic en **"Consultar estado en API"** para obtener el detalle del error de SUNAT.

### Estados API

| Estado     | Significado                                              |
|------------|----------------------------------------------------------|
| Registrado | Factura confirmada en Odoo, aún no enviada a SUNAT       |
| Enviado    | Enviado a FacturaloPeru, esperando respuesta de SUNAT    |
| Aceptado   | SUNAT aceptó el comprobante ✓                           |
| Observado  | SUNAT aceptó con observaciones (válido, revisar nota)    |
| Rechazado  | SUNAT rechazó — ver mensaje de error para corregir      |
| Anulado    | Comprobante anulado mediante comunicación de baja       |

### Paso 4 — Descargar / Imprimir

Desde la factura aceptada:

| Botón        | Acción                                              |
|--------------|-----------------------------------------------------|
| **PDF-A4**   | Genera reporte A4 con logo, tabla, QR y totales     |
| **PDF Ticket** | Genera reporte 80mm para impresora térmica        |
| **Link CDR** | Descarga la Constancia de Recepción de SUNAT       |
| **Link XML** | Descarga el XML firmado enviado a SUNAT            |
| **Link PDF** | Descarga el PDF generado por FacturaloPeru         |

---

## 12. Reportes PDF disponibles

El módulo incluye tres reportes para `account.move` (facturas/boletas):

### PDF-A4 — Reporte principal A4

**Botón:** "PDF-A4" (visible tras envío a SUNAT)
**Papel:** A4 (210 × 297 mm)

Contenido:
- Header: logo empresa + datos + caja RUC/tipo/número
- Tabla de datos del comprobante
- Tabla de productos (COD, CANT, UNIDAD, DESCRIPCIÓN, P.UNIT, DTO, TOTAL)
- Totales (IGV + Total a pagar)
- Monto en letras (`Son:`)
- Cuentas bancarias de la empresa
- QR de verificación SUNAT
- Pie de página con URL de consulta

### PDF Ticket 80ml — Impresora térmica

**Botón:** "PDF Ticket" (visible tras envío a SUNAT)
**Papel:** 80 × 200 mm (customizable)

Contenido:
- Header empresa (centrado, compacto)
- Caja tipo de documento centrada
- Datos del comprobante en tabla compacta:
  - F. Emisión / H. Emisión / F. Vencimiento
  - Cliente, tipo doc, dirección, orden de compra
- Tabla productos (fuente 8px)
- IGV + Total
- Son (monto en letras)
- Cuentas bancarias + CCI
- Código Hash SUNAT (cuando está disponible)
- Condición de pago + vendedor
- Pie de página con URL consulta

### Configurar impresora térmica

El papel del ticket (80mm) se define en:
`Contabilidad → Configuración → Formatos de Papel` (o `Ajustes → Técnico → Reportes → Formatos de Papel`)

Registro: **"Ticket 80mm - FacturaloPeru"** — 80mm × 200mm, DPI 80.

> Para ajustar la altura del ticket (si el contenido es más largo), aumentar `page_height` en el registro del formato de papel.

### Reporte en el menú "Imprimir"

Ambos reportes también aparecen en el menú **"Imprimir"** de cualquier factura (dropdown junto al botón Imprimir).

---

## 13. Configuración del Punto de Venta (POS)

### Requisitos previos

- Completar pasos 3, 4, 5 y 6 de esta guía
- Al menos un diario Efectivo o Banco creado

### Configuración básica POS

`Punto de Venta → Configuración → Ajustes`

| Campo                 | Valor                                               |
|-----------------------|-----------------------------------------------------|
| URL API               | `https://mi-empresa.qhipa.org.pe/api/documents`     |
| Token API             | Token Bearer del Facturador PRO                     |
| Diario CPE Factura    | Seleccionar diario F002 (o el que uses para POS)    |
| Diario CPE Boleta     | Seleccionar diario B002 (o el que uses para POS)    |
| Fijación de precios   | **Precios con impuestos incluidos**                 |
| Envío de email        | Activar si se desea enviar comprobante al cliente   |

### Activar IVA en productos digitales (requerido)

`Ajustes → Contabilidad → IVA de bienes digitales de la UE` → Activar.

> Sin esto el POS no puede calcular correctamente los impuestos.

---

## 14. Errores comunes y soluciones

### ❌ Error FK constraint al enviar a SUNAT

```
Cannot add or update a child row: persons_district_id_foreign
(district_id = 0, address = 0, email = 0)
```

**Causa:** el cliente tiene campos de dirección vacíos. PHP interpreta `null` como `0` y viola la FK de la tabla de distritos en la API.

**Solución:**
1. Ir al contacto del cliente
2. Completar los campos: **Calle, Ciudad, Estado/Departamento, País, Código postal (ubigeo)**
3. Si el cliente no tiene dirección conocida, poner al menos: calle = "-", ciudad = "LIMA"

---

### ❌ Número de documento incorrecto en SUNAT

**Síntoma:** la API recibe `numero_documento = '#'` o un número incorrecto.

**Causa:** el campo `l10n_latam_document_number` está vacío o el diario no tiene el código de serie configurado.

**Solución:**
1. Verificar que el diario tenga **Código = F002** (no `F002-` ni `F 002`)
2. La factura debe estar en estado **Confirmado** (no borrador) para tener el número asignado
3. Verificar que `l10n_latam_document_number` tenga valor en la pestaña "Otra información"

---

### ❌ "No se encontró el tipo de documento" al confirmar factura

**Causa:** el diario no tiene configurado el campo `Tipo de documento (SUNAT)`.

**Solución:** ir al diario → campo `Tipo de documento SUNAT` → seleccionar el código correspondiente (01=Factura, 03=Boleta, etc.).

---

### ❌ Estado API queda en "Rechazado"

**Pasos para diagnosticar:**
1. Clic en **"Consultar estado en API"** — muestra el mensaje de error de SUNAT
2. Revisar la pestaña **"API JSON"** de la factura — ver el JSON enviado
3. Errores frecuentes de SUNAT:

| Código SUNAT | Causa                                              |
|--------------|----------------------------------------------------|
| 2329         | Código de producto (unidad de medida) inválido     |
| 2800         | Tipo de documento de identidad del receptor inválido|
| 3101         | El monto total no coincide con la suma de líneas   |
| 1033         | Serie-correlativo ya existe en SUNAT               |
| 0152         | RUC del receptor no existe en SUNAT               |

---

### ❌ El botón "PDF-A4" o "PDF Ticket" no aparece

**Causa:** el botón solo es visible cuando:
- La factura NO está en borrador (`state != 'draft'`)
- El estado API NO es "Registrado" (`state_api != 'register'`)
- El campo `number_feapi` tiene valor (se llena al enviar a SUNAT)

**Solución:** enviar primero a SUNAT. Una vez aceptado, los botones aparecen.

---

### ❌ "Son:" vacío en los reportes

**Causa:** `api_number_to_letter` se llena cuando se envía el comprobante a FacturaloPeru. Las facturas antiguas (antes de la integración) pueden tenerlo vacío.

**Solución:** usar el botón **"Enviar SUNAT"** o **"Consultar estado en API"** para que el sistema llene el campo.

---

### ❌ El número muestra "F 00000046" en lugar de "F002-46"

**Explicación:** Odoo usa `F 00000046` como nombre interno de contabilidad (secuencia del diario). El número SUNAT `F002-46` se muestra en **verde debajo del título** de la factura (campo `feapi_display_number`).

Ambos números son correctos:
- `F 00000046` = correlativo interno de Odoo (para contabilidad)
- `F002-00000046` = número oficial ante SUNAT (para el comprobante electrónico)

---

## Resumen de configuración mínima antes del primer comprobante

```
✅ Docker levantado y módulos instalados
✅ Plan de cuentas peruano (PCGE) instalado
✅ Al menos un diario de Efectivo o Banco creado
✅ Empresa: RUC, dirección completa, teléfono, email configurados
✅ Empresa: URL API y Token de FacturaloPeru configurados
✅ Al menos un diario de facturación creado (ej. F002, tipo 01-Factura)
✅ Al menos un diario de boleta creado (ej. B002, tipo 03-Boleta)
✅ Impuestos IGV con código SUNAT configurado (1000 para 18%)
✅ Unidades de medida con código SUNAT (NIU, KGM, etc.)
✅ Cliente con: tipo de documento, número doc, dirección completa
```

---

*Última actualización: 2026-03-18*
