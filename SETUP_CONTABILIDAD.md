# Configuración de Contabilidad Base — Odoo 19 FacturadorPeru

Guía para configurar el plan de cuentas y los diarios de efectivo/banco.
Requerido antes de acceder a **Ajustes > Punto de Venta** (sin esto aparece el error
*"Asegúrese de que haya un diario bancario existente"*).

---

## ¿Por qué es necesario?

Odoo 19 requiere que la empresa tenga:

1. **Plan de cuentas instalado** — cuentas contables del l10n_pe (localización peruana)
2. **Al menos un diario de tipo `cash` o `bank`** — para que el POS pueda configurar métodos de pago

Sin estas dos cosas, la página de ajustes del POS lanza el error antes de cargar.

---

## Opción A — Por script (recomendado)

### Requisitos

- Python 3.8+ instalado en el host
- Odoo corriendo (`docker-compose up -d`)
- Archivo `setup_facturalo.env` configurado (ver `setup_facturalo.env.example`)

### Ejecutar

```bash
python3 setup_base_contabilidad.py
```

Con dry-run para ver qué haría sin aplicar cambios:

```bash
python3 setup_base_contabilidad.py --dry-run
```

### ¿Qué hace el script?

| Paso | Acción |
|------|--------|
| 1 | Verifica si hay cuentas contables en la empresa |
| 2 | Si no hay cuentas → aplica el plan de cuentas l10n_pe (localización peruana) |
| 3 | Crea diario **Efectivo** (`CASH`, tipo `cash`) si no existe |
| 4 | Crea diario **Banco** (`BNK`, tipo `bank`) si no existe |
| 5 | Muestra resumen del estado final |

> El script es idempotente: si los diarios ya existen, no los duplica.

---

## Opción B — Por interfaz de usuario

### Paso 1 — Activar modo desarrollador

`Ajustes → General → Activar el modo desarrollador`

O directamente: `http://localhost:8069/web?debug=1`

---

### Paso 2 — Instalar localización peruana (plan de cuentas)

> Si ya ves cuentas en `Contabilidad > Contabilidad > Plan de cuentas`, saltar al Paso 3.

**Ruta:** `Ajustes` → sección **Contabilidad** → campo **"Paquete de localización fiscal"**

> Esta opción aparece solo si el módulo **Contabilidad** está instalado.
> Si no aparece, instálalo primero desde `Aplicaciones → buscar "Contabilidad"`.

1. Ir a `Ajustes` (menú principal superior)
2. En la página de Ajustes, localizar la sección **Contabilidad** (scroll hacia abajo)
3. En el campo **Paquete de localización fiscal** seleccionar `Perú - Plan de Cuentas (PCGE)`
4. Clic en **Guardar**

Odoo creará automáticamente todas las cuentas del PCGE para tu empresa.

**Verificar:**
`Contabilidad > Contabilidad > Plan de cuentas`
Deberías ver las cuentas del 1 al 9 del PCGE peruano.

---

### Paso 3 — Crear diario de Efectivo

**Ruta:** `Contabilidad → Configuración → Diarios → Nuevo`

| Campo | Valor |
|-------|-------|
| Nombre | `Efectivo` |
| Tipo | `Efectivo` |
| Código | `CASH` |
| Moneda | `PEN` (Soles) |

Clic en **Guardar**.

> Odoo asigna automáticamente las cuentas contables de caja (10.1.1.01 o equivalente).

---

### Paso 4 — Crear diario de Banco (opcional pero recomendado)

**Ruta:** `Contabilidad → Configuración → Diarios → Nuevo`

| Campo | Valor |
|-------|-------|
| Nombre | `Banco` |
| Tipo | `Banco` |
| Código | `BNK` |
| Moneda | `PEN` (Soles) |
| Número de cuenta | N° de cuenta bancaria de la empresa |

Clic en **Guardar**.

---

### Paso 5 — Verificar en el POS

1. Ir a `Ajustes → Punto de Venta`
2. La página debe cargar **sin el error** de diario bancario
3. En `Punto de Venta → Configuración → Ajustes → Métodos de Pago` debe aparecer `Efectivo`

---

## Verificación final

```bash
# Confirmar que existen cuentas contables
docker exec fp_odoo bash -c \
  "psql postgresql://odoo:odoo@db/fp_bd -c 'SELECT COUNT(*) FROM account_account;'"
# Esperado: COUNT > 0

# Confirmar que existen los diarios
docker exec fp_odoo bash -c \
  "psql postgresql://odoo:odoo@db/fp_bd -c \
   \"SELECT name, code, type FROM account_journal WHERE type IN ('cash','bank');\""
# Esperado: filas con Efectivo y Banco
```

---

## Notas

- Este paso se realiza **una sola vez** por base de datos nueva
- Si instalas una BD desde backup de producción, los diarios ya deberían existir
- Los diarios F001, B001, T001 son de tipo `sale` (facturación SUNAT) — son distintos a los diarios de efectivo/banco que necesita el POS
- Después de crear los diarios, **no es necesario reiniciar Odoo**
