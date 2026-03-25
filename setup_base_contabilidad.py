#!/usr/bin/env python3
"""
setup_base_contabilidad.py
==========================
Configura la contabilidad base de Odoo 19 necesaria para que el POS funcione:

  1. Verifica si el plan de cuentas está instalado en la empresa
  2. Si no hay cuentas → aplica la localización peruana (l10n_pe / PCGE)
  3. Crea el diario de Efectivo (cash) si no existe
  4. Crea el diario de Banco (bank) si no existe

Lee la conexión desde 'setup_facturalo.env' o variables de entorno.

Uso:
    python3 setup_base_contabilidad.py
    python3 setup_base_contabilidad.py --dry-run
    python3 setup_base_contabilidad.py --env-file mi.env
"""

import xmlrpc.client
import os
import sys
import argparse
from pathlib import Path


# ──────────────────────────────────────────────
# Carga de configuración
# ──────────────────────────────────────────────

def load_env(filepath="setup_facturalo.env"):
    env_path = Path(filepath)
    if env_path.exists():
        print(f"[config] Leyendo {filepath}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())
    else:
        print(f"[config] {filepath} no encontrado, usando variables de entorno")


def get_config():
    return {
        "url":      os.environ.get("ODOO_URL", "http://localhost:8069"),
        "db":       os.environ.get("ODOO_DB", "fp_bd"),
        "user":     os.environ.get("ODOO_USER", "admin"),
        "password": os.environ.get("ODOO_PASSWORD", "admin"),
    }


# ──────────────────────────────────────────────
# Cliente XML-RPC
# ──────────────────────────────────────────────

class OdooClient:
    def __init__(self, url, db, user, password):
        self.db = db
        self.password = password

        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        self.uid = common.authenticate(db, user, password, {})
        if not self.uid:
            raise ConnectionError(f"Autenticación fallida en {url} db={db} user={user}")
        print(f"[odoo] Conectado como uid={self.uid} a {url} db={db}")

        self._models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

    def execute(self, model, method, *args, **kwargs):
        return self._models.execute_kw(
            self.db, self.uid, self.password,
            model, method, list(args), kwargs
        )

    def search_read(self, model, domain, fields, limit=0):
        kwargs = {"fields": fields}
        if limit:
            kwargs["limit"] = limit
        return self.execute(model, "search_read", domain, **kwargs)

    def search(self, model, domain):
        return self.execute(model, "search", domain)

    def create(self, model, vals):
        return self.execute(model, "create", [vals])

    def write(self, model, ids, vals):
        return self.execute(model, "write", ids, vals)

    def call(self, model, method, *args, **kwargs):
        return self.execute(model, method, *args, **kwargs)


# ──────────────────────────────────────────────
# Pasos
# ──────────────────────────────────────────────

def step_check_accounts(client):
    """Retorna True si la empresa ya tiene cuentas contables."""
    count = client.execute("account.account", "search_count", [])
    print(f"\n[1/4] Plan de cuentas: {count} cuenta(s) encontrada(s)")
    return count > 0


def step_apply_chart(client, dry_run):
    """Aplica el plan de cuentas l10n_pe a la empresa principal."""
    print("\n[2/4] Aplicando localización peruana (l10n_pe)...")

    # Obtener empresa principal
    companies = client.search_read("res.company", [], ["id", "name"], limit=1)
    if not companies:
        print("  ERROR: No se encontró ninguna empresa")
        return False
    company = companies[0]
    print(f"  Empresa: [{company['id']}] {company['name']}")

    # Buscar plantilla de plan de cuentas peruano
    # En Odoo 19 el chart template se identifica por el campo 'name' o 'country_id'
    templates = client.search_read(
        "account.chart.template",
        [],
        ["id", "name"],
        limit=50
    )

    if not templates:
        print("  ERROR: No se encontraron plantillas de plan de cuentas")
        print("  Verifica que el módulo l10n_pe esté instalado")
        return False

    # Buscar plantilla peruana (prioridad: 'pe' en nombre, luego primera disponible)
    pe_template = None
    for t in templates:
        name_lower = t["name"].lower()
        if "peru" in name_lower or "perú" in name_lower or "pcge" in name_lower or "_pe" in name_lower:
            pe_template = t
            break

    if not pe_template:
        print("  Plantillas disponibles:")
        for t in templates:
            print(f"    [{t['id']}] {t['name']}")
        print("  AVISO: No se encontró plantilla peruana específica, usando la primera disponible")
        pe_template = templates[0]

    print(f"  Plantilla seleccionada: [{pe_template['id']}] {pe_template['name']}")

    if dry_run:
        print("  DRY-RUN — no se aplicó el plan de cuentas")
        return True

    try:
        client.call(
            "account.chart.template",
            "try_loading",
            [pe_template["id"]],
            company=company["id"],
            install_demo=False
        )
        print("  OK — plan de cuentas aplicado")
        return True
    except Exception as e:
        # Odoo 19: algunos métodos usan 'generate_journals' directamente
        print(f"  AVISO try_loading: {e}")
        try:
            client.call(
                "account.chart.template",
                "_load",
                [pe_template["id"]],
                company["id"]
            )
            print("  OK — plan de cuentas aplicado (método _load)")
            return True
        except Exception as e2:
            print(f"  ERROR al aplicar plan de cuentas: {e2}")
            print("  Aplica el plan de cuentas manualmente:")
            print("  Ajustes → Contabilidad → Localización fiscal → País: Perú → Guardar")
            return False


def step_create_journal(client, dry_run, journal_type, name, code):
    """Crea un diario si no existe uno con ese código."""
    label = "Efectivo" if journal_type == "cash" else "Banco"
    print(f"\n[{'3' if journal_type == 'cash' else '4'}/4] Verificando diario de {label}...")

    existing = client.search_read(
        "account.journal",
        [["code", "=", code]],
        ["id", "name", "type"]
    )

    if existing:
        j = existing[0]
        print(f"  Ya existe: [{j['id']}] {j['name']} (tipo: {j['type']}) — omitiendo")
        return True

    # Verificar si hay alguno del mismo tipo
    same_type = client.search_read(
        "account.journal",
        [["type", "=", journal_type]],
        ["id", "name", "code"]
    )
    if same_type:
        print(f"  Ya existe un diario de tipo '{journal_type}':")
        for j in same_type:
            print(f"    [{j['id']}] {j['name']} ({j['code']})")
        print(f"  No se creará '{name}' para evitar duplicados")
        return True

    print(f"  Creando diario '{name}' (código: {code}, tipo: {journal_type})...")

    if dry_run:
        print(f"  DRY-RUN — no se creó el diario")
        return True

    try:
        vals = {
            "name": name,
            "type": journal_type,
            "code": code,
        }
        journal_id = client.create("account.journal", vals)
        print(f"  OK — diario creado con id={journal_id}")
        return True
    except Exception as e:
        print(f"  ERROR al crear diario: {e}")
        print(f"  Crea el diario manualmente:")
        print(f"  Contabilidad → Configuración → Diarios → Nuevo")
        print(f"  Nombre: {name} | Tipo: {label} | Código: {code}")
        return False


def step_summary(client):
    """Muestra el estado final de cuentas y diarios."""
    print("\n" + "=" * 50)
    print("ESTADO FINAL")
    print("=" * 50)

    count = client.execute("account.account", "search_count", [])
    print(f"  Cuentas contables:  {count}")

    journals = client.search_read(
        "account.journal",
        [["type", "in", ["cash", "bank"]]],
        ["id", "name", "code", "type"]
    )
    if journals:
        print(f"  Diarios cash/bank:")
        for j in journals:
            print(f"    [{j['id']}] {j['name']} ({j['code']}) — tipo: {j['type']}")
    else:
        print("  Diarios cash/bank:  ninguno")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Configura contabilidad base de Odoo 19 para FacturadorPeru"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Muestra los cambios sin aplicarlos")
    parser.add_argument("--env-file", default="setup_facturalo.env",
                        help="Ruta al archivo .env (default: setup_facturalo.env)")
    args = parser.parse_args()

    load_env(args.env_file)
    cfg = get_config()

    if args.dry_run:
        print("\n*** MODO DRY-RUN: no se realizarán cambios ***\n")

    try:
        client = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["password"])
    except Exception as e:
        print(f"\nERROR de conexión: {e}")
        print("\nVerifica que Odoo esté corriendo y los datos de acceso sean correctos:")
        print(f"  URL:     {cfg['url']}")
        print(f"  DB:      {cfg['db']}")
        print(f"  Usuario: {cfg['user']}")
        sys.exit(1)

    has_accounts = step_check_accounts(client)

    if not has_accounts:
        step_apply_chart(client, args.dry_run)
    else:
        print("  Plan de cuentas ya instalado — omitiendo paso 2")

    step_create_journal(client, args.dry_run, "cash", "Efectivo", "CASH")
    step_create_journal(client, args.dry_run, "bank", "Banco",    "BNK")

    step_summary(client)

    print()
    if args.dry_run:
        print("DRY-RUN completado. Ejecutar sin --dry-run para aplicar cambios.")
    else:
        print("Configuración completada.")
        print("Accede a: http://localhost:8069/odoo/settings#point_of_sale")


if __name__ == "__main__":
    main()
