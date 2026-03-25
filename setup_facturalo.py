#!/usr/bin/env python3
"""
setup_facturalo.py
==================
Configura automáticamente los parámetros de FacturaloPeru en Odoo 19
vía XML-RPC. Lee la configuración desde 'setup_facturalo.env' o
variables de entorno.

Uso:
    python3 setup_facturalo.py
    python3 setup_facturalo.py --dry-run   # muestra qué haría sin ejecutar
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
    """Carga variables desde un archivo .env si existe."""
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

        "api_url":        os.environ.get("API_URL", ""),
        "api_token":      os.environ.get("API_TOKEN", ""),
        "api_send_email": os.environ.get("API_SEND_EMAIL", "false").lower() == "true",
        "apiperu_token":  os.environ.get("APIPERU_TOKEN", ""),

        "company_name":   os.environ.get("COMPANY_NAME", ""),
        "company_vat":    os.environ.get("COMPANY_VAT", ""),
        "company_street": os.environ.get("COMPANY_STREET", ""),
        "company_city":   os.environ.get("COMPANY_CITY", ""),
        "company_phone":  os.environ.get("COMPANY_PHONE", ""),
        "company_email":  os.environ.get("COMPANY_EMAIL", ""),

        "warehouse_code": os.environ.get("WAREHOUSE_ESTABLISHMENT_CODE", "0000"),

        "pos_name":      os.environ.get("POS_NAME", ""),
        "pos_api_url":   os.environ.get("POS_API_URL", ""),
        "pos_api_token": os.environ.get("POS_API_TOKEN", ""),
    }


# ──────────────────────────────────────────────
# Conexión Odoo XML-RPC
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

    def write(self, model, ids, vals):
        return self.execute(model, "write", ids, vals)

    def create(self, model, vals):
        return self.execute(model, "create", [vals])

    def search(self, model, domain):
        return self.execute(model, "search", domain)


# ──────────────────────────────────────────────
# Pasos de configuración
# ──────────────────────────────────────────────

def step_company(client, cfg, dry_run):
    """Configura datos básicos + API de la empresa principal."""
    print("\n[1/5] Configurando empresa principal...")

    companies = client.search_read("res.company", [], ["id", "name"], limit=1)
    if not companies:
        print("  ERROR: No se encontró ninguna empresa")
        return
    company = companies[0]
    print(f"  Empresa: [{company['id']}] {company['name']}")

    vals = {}
    if cfg["api_url"]:
        vals["api_url"] = cfg["api_url"]
    if cfg["api_token"]:
        vals["api_token"] = cfg["api_token"]
    vals["api_send_email"] = cfg["api_send_email"]

    if cfg["company_name"]:
        vals["name"] = cfg["company_name"]
    if cfg["company_vat"]:
        vals["vat"] = cfg["company_vat"]
    if cfg["company_street"]:
        vals["street"] = cfg["company_street"]
    if cfg["company_city"]:
        vals["city"] = cfg["company_city"]
    if cfg["company_phone"]:
        vals["phone"] = cfg["company_phone"]
    if cfg["company_email"]:
        vals["email"] = cfg["company_email"]

    # apiperu_token — campo opcional en res.company
    if cfg["apiperu_token"]:
        vals["apiperu_token"] = cfg["apiperu_token"]

    if not vals:
        print("  Sin cambios (no hay datos de empresa en el .env)")
        return

    print(f"  Valores a aplicar: {list(vals.keys())}")
    if not dry_run:
        client.write("res.company", [company["id"]], vals)
        print("  OK — empresa actualizada")
    else:
        print("  DRY-RUN — no se escribió nada")


def step_system_params(client, cfg, dry_run):
    """Crea/actualiza parámetros del sistema."""
    print("\n[2/5] Configurando parámetros del sistema...")

    params = {}
    if cfg["api_url"]:
        params["facturaloperu_odoo_facturacion.api_url"] = cfg["api_url"]
    if cfg["pos_api_url"] or cfg["api_url"]:
        pos_url = cfg["pos_api_url"] or (cfg["api_url"].rstrip("/") + "/api/documents")
        params["pos_facturalo_api_api_url"] = pos_url

    if not params:
        print("  Sin parámetros para actualizar")
        return

    for key, value in params.items():
        existing = client.search_read(
            "ir.config_parameter",
            [["key", "=", key]],
            ["id", "key", "value"]
        )
        if existing:
            print(f"  UPDATE  {key} = {value}")
            if not dry_run:
                client.write("ir.config_parameter", [existing[0]["id"]], {"value": value})
        else:
            print(f"  CREATE  {key} = {value}")
            if not dry_run:
                client.create("ir.config_parameter", {"key": key, "value": value})

    if dry_run:
        print("  DRY-RUN — no se escribió nada")
    else:
        print("  OK — parámetros del sistema actualizados")


def step_warehouse(client, cfg, dry_run):
    """Configura el código de establecimiento en el almacén principal."""
    print("\n[3/5] Configurando almacén principal...")

    if not cfg["warehouse_code"]:
        print("  Sin código de establecimiento configurado, omitiendo")
        return

    warehouses = client.search_read("stock.warehouse", [], ["id", "name"], limit=1)
    if not warehouses:
        print("  No se encontró ningún almacén")
        return

    wh = warehouses[0]
    print(f"  Almacén: [{wh['id']}] {wh['name']}")
    print(f"  Código de establecimiento: {cfg['warehouse_code']}")

    if not dry_run:
        client.write("stock.warehouse", [wh["id"]], {"establishment_code": cfg["warehouse_code"]})
        print("  OK — almacén actualizado")
    else:
        print("  DRY-RUN — no se escribió nada")


def step_pos(client, cfg, dry_run):
    """Configura el POS con URL y Token de la API."""
    print("\n[4/5] Configurando Punto de Venta...")

    if not cfg["api_url"] and not cfg["pos_api_url"]:
        print("  Sin URL de API configurada, omitiendo POS")
        return

    pos_url   = cfg["pos_api_url"] or (cfg["api_url"].rstrip("/") + "/api/documents")
    pos_token = cfg["pos_api_token"] or cfg["api_token"]

    # Buscar POS por nombre o usar el primero
    if cfg["pos_name"]:
        pos_list = client.search_read(
            "pos.config",
            [["name", "=", cfg["pos_name"]]],
            ["id", "name"]
        )
    else:
        pos_list = client.search_read("pos.config", [], ["id", "name"], limit=1)

    if not pos_list:
        print("  No se encontró ningún POS, omitiendo")
        return

    pos = pos_list[0]
    print(f"  POS: [{pos['id']}] {pos['name']}")

    vals = {
        "is_facturalo_api": True,
        "iface_facturalo_url_endpoint": pos_url,
        "iface_api_send_email": cfg["api_send_email"],
    }
    if pos_token:
        vals["iface_facturalo_token"] = pos_token

    print(f"  URL endpoint: {pos_url}")
    print(f"  Envío email:  {cfg['api_send_email']}")

    if not dry_run:
        client.write("pos.config", [pos["id"]], vals)
        print("  OK — POS actualizado")
    else:
        print("  DRY-RUN — no se escribió nada")


def step_journals_check(client, cfg, dry_run):
    """Verifica que los diarios F001 y B001 existan."""
    print("\n[5/5] Verificando diarios SUNAT...")

    journals = client.search_read(
        "account.journal",
        [["type", "=", "sale"]],
        ["id", "name", "code", "l10n_pe_sunat_code"]
    )

    found_codes = {}
    for j in journals:
        sunat = j.get("l10n_pe_sunat_code") or ""
        print(f"  Diario: [{j['id']}] {j['name']} (código: {j['code']}, SUNAT: {sunat or 'N/A'})")
        found_codes[j["code"]] = j

    # Verificar F001 y B001
    for serie in ["F001", "B001"]:
        if serie not in found_codes:
            print(f"  AVISO: No se encontró diario con código '{serie}' — crear manualmente")
        else:
            print(f"  OK: Diario {serie} encontrado")

    # Verificar diario de guías (sunat_code = 09)
    guia_journals = [j for j in journals if j.get("l10n_pe_sunat_code") == "09"]
    if not guia_journals:
        print("  AVISO: No hay diario con código SUNAT '09' (Guías de Remisión) — crear manualmente")
    else:
        for j in guia_journals:
            print(f"  OK: Diario de Guías encontrado: {j['name']}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Configura FacturaloPeru en Odoo 19")
    parser.add_argument("--dry-run", action="store_true",
                        help="Muestra los cambios sin aplicarlos")
    parser.add_argument("--env-file", default="setup_facturalo.env",
                        help="Ruta al archivo .env (default: setup_facturalo.env)")
    args = parser.parse_args()

    load_env(args.env_file)
    cfg = get_config()

    if args.dry_run:
        print("\n*** MODO DRY-RUN: no se realizarán cambios ***\n")

    # Validaciones mínimas
    if not cfg["api_url"] and not cfg["api_token"]:
        print("AVISO: API_URL y API_TOKEN no configurados — solo se verificarán diarios")

    try:
        client = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["password"])
    except Exception as e:
        print(f"ERROR de conexión: {e}")
        print("\nVerifica que Odoo esté corriendo y los datos de acceso sean correctos:")
        print(f"  URL:      {cfg['url']}")
        print(f"  DB:       {cfg['db']}")
        print(f"  Usuario:  {cfg['user']}")
        sys.exit(1)

    step_company(client, cfg, args.dry_run)
    step_system_params(client, cfg, args.dry_run)
    step_warehouse(client, cfg, args.dry_run)
    step_pos(client, cfg, args.dry_run)
    step_journals_check(client, cfg, args.dry_run)

    print("\n" + "="*50)
    if args.dry_run:
        print("DRY-RUN completado. Ejecutar sin --dry-run para aplicar cambios.")
    else:
        print("Configuración completada exitosamente.")
        print("Reinicia Odoo si es necesario:")
        print("  docker restart fp_odoo")


if __name__ == "__main__":
    main()
