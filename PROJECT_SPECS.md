# FacturadorPeru Pro7 - Odoo 19 Migration Specifications

## Project Description

Migrar e implementar los addons de facturación electrónica peruana (FacturadorPeru Pro7) para Odoo 19, asegurando compatibilidad completa con la API REST de FacturaloPeru y cumplimiento SUNAT.

---

## Execution Parameters

| Parameter | Value |
|-----------|-------|
| **Odoo Version** | 19.0 (Docker: `odoo:19.0`) |
| **Database** | PostgreSQL 16 (container: `fp_bd`) |
| **Container Odoo** | `fp_odoo` |
| **Python** | 3.12+ |
| **API Base URL** | `https://yiwu.qhipa.org.pe/` |
| **API Token** | `hsTcBnakU3XbUPS1I1QllldNVUUHLVLXd0JEQ98kYGvCUR5VDK` |
| **API Reference** | `API FACTURADOR PRO V5.postman_collection (2).json` |
| **Addons Path** | `./addons` → `/mnt/extra-addons` |

---

## Epics & User Stories

### Epic 1: Migración de Addons Base (Prioridad 1)

Migrar los módulos base que son dependencia de todos los demás.

#### US-001: Migrar odoope_einvoice_base
- **Estado:** ✅ Completado — Fixed display_name computed fields (7 modelos)

#### US-002: Migrar odoope_account
- **Estado:** ✅ Completado — Instala OK, sin cambios necesarios

#### US-003: Migrar odoope_toponyms
- **Estado:** ✅ Completado — Instala OK, ubigeos cargados

#### US-004: Migrar odoope_product
- **Estado:** ✅ Completado — Instala OK, sin cambios necesarios

#### US-005: Migrar odoope_currency
- **Estado:** ✅ Completado — Instala OK, sin cambios necesarios

#### US-006: Migrar odoope_stock
- **Estado:** ✅ Completado — Instala OK, sin cambios necesarios

---

### Epic 2: Migración Core Facturación (Prioridad 2)

Módulo principal de facturación electrónica con integración API.

#### US-007: Migrar facturaloperu_odoo_facturacion
- **Estado:** ✅ Completado — Fixed report button, added action_print_invoice_sunat

#### US-008: Migrar facturaloperu_odoo_base
- **Estado:** ⬜ Evaluación pendiente — Sin manifest, contiene subproyecto git; no requerido por otros módulos

---

### Epic 3: POS con Facturación Electrónica (Prioridad 3)

#### US-009: Migrar facturaloperu_odoo_pos
- **Estado:** ✅ Completado (backend) — Models, views, journal.xml, assets migrados. JS frontend (AMD) excluido de assets; pendiente reescritura OWL 2

#### US-010: Migrar facturaloperu_api_pos
- **Estado:** ✅ Completado — Fixed XPath posbox→group_system, Char→Many2one conflict, attrs→inline

#### US-011: Migrar l10n_pe_pos_consulta_dni_ruc
- **Estado:** ✅ Completado (instala OK, JS frontend pendiente OWL 2)
- **Tareas:** Consulta DNI/RUC desde POS
- **Criterio:** Backend OK; frontend JS pendiente reescritura OWL 2

---

### Epic 4: Guías y Logística (Prioridad 3)

#### US-012: Migrar facturaloperu_odoo_guias
- **Estado:** ✅ Completado — Full migration: models, views, fixed account_tax NOT NULL, record IDs

---

### Epic 5: Reportes y Kardex (Prioridad 4)

#### US-013: Migrar facturaloperu_odoo_reportes
- **Estado:** ✅ Completado — create_multi, tree→list, act_window/report→record, src_model removed

#### US-014: Migrar facturaloperu_odoo_kardex
- **Estado:** ✅ Completado — @api.one removed, qty_done→quantity, cross-module IDs fixed, stock locs pruned

---

### Epic 6: Módulos de Soporte (Prioridad 5)

#### US-015: Migrar módulos de soporte
| Módulo | Versión | Estado | Nota |
|--------|---------|--------|------|
| l10n_pe_partner_consulta_dni_ruc | 19.0.1.0.0 | ✅ | Fixed openerp→odoo, attrs→inline, statusbar_colors |
| l10n_pe_pos_consulta_dni_ruc | 19.0.1.0.0 | ✅ | create_multi, removed AMD assets/template.xml |
| l10n_pe_sunat_data | 19.0.1.0.0 | ✅ | Sin cambios necesarios |
| report_xlsx | 19.0.1.0.0 | ✅ | Sin cambios necesarios |
| date_range | 19.0.1.0.0 | ✅ | Sin cambios necesarios |
| stock_picking_invoice_link | 19.0.1.0.0 | ✅ | Sin cambios necesarios |
| web_responsive | 19.0.1.0.0 | ✅ | Fixed ResUsers.__init__, removed old web templates |
| pos_stock_quantity | 19.0.1.0.0 | ✅ | Removed AMD assets, fixed attrs→inline |
| pos_ticket | 19.0.1.0.0 | ✅ | Removed AMD QWeb assets |
| enterprise_theme | 19.0.1.0.0 | ✅ | Sin cambios necesarios |

---

## Acceptance Criteria (Global)

### Por cada addon migrado:
1. `__manifest__.py` con `version: '19.0.x.x.x'` y dependencias correctas
2. Sin uso de `@api.one`, `@api.multi`, `<tree>`, `attrs=`
3. Security: `ir.model.access.csv` + `ir.rule` donde aplique
4. Instala sin errores: `docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -i <addon> --stop-after-init`
5. Funcionalidad verificada en navegador (puerto 8069)

### Para la facturación completa:
1. Crear factura → Enviar a SUNAT vía API → Recibir CDR exitoso
2. Crear boleta desde POS → Enviar a SUNAT → Respuesta OK
3. Generar reportes PLE en formato correcto
4. Consulta DNI/RUC funcional

---

## Diagnóstico Rápido de Estado

### Addons con manifest ya en v19 (requieren validación de código):
- `facturaloperu_odoo_facturacion` → 19.0.1.0.0
- `facturaloperu_odoo_reportes` → 19.0.1.0.0
- `odoope_einvoice_base` → 19.0.1.0.0
- `odoope_account` → 19.0.1.0.0
- `odoope_currency` → 19.0.1.0.0
- `odoope_product` → 19.0.1.0.0
- `odoope_stock` → 19.0.1.0.0
- `odoope_toponyms` → 19.0.1.0.0

### Addons aún en v11 (requieren migración completa):
- `facturaloperu_odoo_guias` → 11.0.1.0.0
- `facturaloperu_odoo_kardex` → 11.0.1.0.0
- `facturaloperu_odoo_pos` → 11.0.1.0.0
- `facturaloperu_api_pos` → 11.0.1.0.0

### Addons sin manifest o por evaluar:
- `facturaloperu_odoo_base` → Contiene subproyecto, evaluar

---

## Protocolo de Trabajo (Agent Memory)

### Al iniciar sesión:
1. Leer `memory/migration-progress.md` para estado actual
2. Revisar `git status` y `git log` para cambios recientes
3. Continuar desde la siguiente tarea pendiente

### Durante el trabajo:
- Migrar **un módulo a la vez** (sesiones enfocadas)
- Validar instalación después de cada módulo
- Registrar errores encontrados y soluciones aplicadas

### Antes de cerrar sesión:
- Actualizar `memory/migration-progress.md` con progreso
- Actualizar este archivo (`PROJECT_SPECS.md`) con nuevos estados
- Hacer commit del progreso si el usuario lo solicita

### Orden de migración recomendado:
```
1. odoope_einvoice_base (base de todo)
2. odoope_account → odoope_product → odoope_stock → odoope_toponyms → odoope_currency
3. facturaloperu_odoo_facturacion (core)
4. l10n_pe_partner_consulta_dni_ruc → l10n_pe_sunat_data
5. facturaloperu_odoo_pos → facturaloperu_api_pos → l10n_pe_pos_consulta_dni_ruc
6. facturaloperu_odoo_guias
7. facturaloperu_odoo_reportes → facturaloperu_odoo_kardex
8. Módulos de soporte restantes
```
