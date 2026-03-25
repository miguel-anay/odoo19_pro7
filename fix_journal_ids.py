import xmlrpc.client

url = 'http://localhost:8069'
db = 'fp_bd'
username = 'admin'
password = "admin"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Find existing journals
journals = models.execute_kw(db, uid, password, 'account.journal', 'search_read',
    [[['code', 'in', ['B002', 'F002']]]], {'fields': ['id', 'name', 'code']})
print("Found journals:", journals)

# Map code to XML ID name
xml_id_map = {
    'B002': 'account_journal_boleta_b002',
    'F002': 'account_journal_factura_f002',
}

for j in journals:
    code = j['code']
    xml_name = xml_id_map.get(code)
    if not xml_name:
        continue

    # Check if ir.model.data already has this entry
    existing = models.execute_kw(db, uid, password, 'ir.model.data', 'search_read',
        [[['module', '=', 'facturaloperu_api_pos'], ['name', '=', xml_name]]],
        {'fields': ['id', 'res_id']})

    if existing:
        print(f"  {code}: ir.model.data entry already exists: {existing}")
    else:
        # Create the ir.model.data entry to link the existing journal
        new_id = models.execute_kw(db, uid, password, 'ir.model.data', 'create', [{
            'module': 'facturaloperu_api_pos',
            'name': xml_name,
            'model': 'account.journal',
            'res_id': j['id'],
            'noupdate': True,
        }])
        print(f"  {code} (id={j['id']}): created ir.model.data id={new_id} as {xml_name}")

print("Done. Now re-run: MSYS_NO_PATHCONV=1 docker-compose exec -T web odoo -c /etc/odoo/odoo.conf -u facturaloperu_api_pos -d fp_bd --stop-after-init")
