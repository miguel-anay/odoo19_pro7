# CLAUDE.md - Odoo 19 FacturadorPeru

Migración Odoo 11 → 19. Facturación electrónica SUNAT con API FacturaloPeru Pro V5.
Estado detallado en `PROJECT_SPECS.md`. Progreso por sesión en `memory/migration-progress.md`.

## Docker (container: fp_odoo, db: fp_bd)

```bash
docker-compose up -d                    # Iniciar
docker restart fp_odoo                  # Reiniciar Odoo
docker logs --tail 100 fp_odoo         # Ver logs
# Instalar/actualizar addon:
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -i <addon> --stop-after-init
docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -u <addon> --stop-after-init
```

## Cambios críticos Odoo 11 → 19

| Odoo 11 | Odoo 19 |
|---|---|
| `<tree>` | `<list>` |
| `attrs="{'invisible': [...]}"` | `invisible="expresion"` directo |
| `@api.one`, `@api.multi` | Eliminar (usar `@api.depends`, `@api.constrains`) |
| `def unlink()` override | `@api.ondelete(at_uninstall=False)` |
| `group_operator=` | `aggregator=` |
| `cr.execute("SELECT...")` | `SQL()` + `execute_query_dict()` |
| `create({...})` un dict | `create([{...}])` lista de dicts |
| `function=`, `store=` | `compute=` + `@api.depends` |

## Módulos (addons/)

**Core:** `facturaloperu_odoo_facturacion` (API SUNAT), `_pos`, `_guias`, `_kardex`, `_reportes`
**Base:** `odoope_einvoice_base`, `_account`, `_product`, `_stock`, `_toponyms`, `_currency`
**L10n:** `l10n_pe_partner_consulta_dni_ruc`, `_pos_consulta_dni_ruc`, `_sunat_data`
**Soporte:** `report_xlsx`, `date_range`, `stock_picking_invoice_link`, `web_responsive`, `pos_stock_quantity`, `pos_ticket`, `enterprise_theme`

**API FacturaloPeru:** URL `https://yiwu.qhipa.org.pe/`, token en `data/api_url.xml`, modelos en `models/feapi*.py`

## Config

Odoo 19.0 | Python 3.12+ | PostgreSQL 16 | Config: `config/odoo.conf` | Addons: `./addons` → `/mnt/extra-addons` | Puerto: 8069

## Estrategia de modelos (OBLIGATORIO)

**Sonnet = modelo principal.** Ejecuta el 90% del trabajo: editar archivos, correr Docker, migración mecánica.
**Opus = solo escalación.** Invocar ÚNICAMENTE para:
- Decisiones arquitectónicas complejas (multi-addon, refactoring mayor)
- Debugging de errores que Sonnet no pueda resolver en 2 intentos
- Diseño de nuevas features que no existían en Odoo 11

Para escalar a Opus: `Task(subagent_type="odoo19-facturadorperu-specialist", model="opus")`
NO invocar al especialista para migraciones mecánicas (reemplazar decoradores, actualizar vistas, etc).

## Workflow de migración

1. Leer `PROJECT_SPECS.md` y `memory/migration-progress.md`
2. Ejecutar migración directamente (editar .py, .xml, __manifest__.py)
3. Probar: `docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -i <addon> --stop-after-init`
4. Si hay error complejo → escalar a Opus specialist
5. Actualizar `PROJECT_SPECS.md` y `memory/migration-progress.md`

Orden: einvoice_base → account → product → stock → toponyms → currency → facturacion → pos → guias → reportes → kardex → soporte
