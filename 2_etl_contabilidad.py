# 2_etl_contabilidad.py
# Contabilidad Pipeline — ETL con limpieza de datos
# Extrae 4 hojas de Google Sheets → limpia → carga en SQLite

import sqlite3
import gspread
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
ARCHIVO_CREDENCIALES = r"C:\Users\franc\tipo-de-cambio\credenciales.json"
NOMBRE_HOJA          = "Contabilidad Empresa X"
BASE_DE_DATOS        = "contabilidad.db"
# ──────────────────────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ─── FUNCIONES DE LIMPIEZA ────────────────────────────────────────────────────
def limpiar_fecha(valor):
    valor = str(valor).strip()
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formatos:
        try:
            return datetime.strptime(valor, fmt).strftime("%Y-%m-%d")
        except:
            continue
    return None

def limpiar_texto(valor):
    if not valor:
        return None
    return str(valor).strip().title()

def limpiar_estado(valor):
    if not valor:
        return None
    estados = {
        "pagado":    "Pagado",
        "pendiente": "Pendiente",
        "vencido":   "Vencido",
    }
    return estados.get(str(valor).strip().lower(), str(valor).strip().title())

def limpiar_monto(valor):
    if valor is None or valor == "":
        return None
    valor = str(valor).strip()
    valor = valor.replace("$", "").replace(" ", "")
    if re.search(r",\d{1,2}$", valor):
        valor = valor.replace(".", "").replace(",", ".")
    else:
        valor = valor.replace(",", "")
    valor = re.sub(r"[a-zA-ZáéíóúÁÉÍÓÚ]+", "", valor).strip()
    try:
        return float(valor)
    except:
        return None

def leer_hoja(libro, nombre):
    hoja = libro.worksheet(nombre)
    raw  = hoja.get_all_values()
    encabezados = raw[0]
    return [dict(zip(encabezados, fila)) for fila in raw[1:] if any(fila)]

# ─── CONECTAR CON GOOGLE SHEETS ───────────────────────────────────────────────
print("Conectando con Google Sheets...")
credenciales = Credentials.from_service_account_file(
    ARCHIVO_CREDENCIALES, scopes=SCOPES
)
cliente = gspread.authorize(credenciales)
libro   = cliente.open(NOMBRE_HOJA)
print("✓ Conexión exitosa\n")

ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
conexion = sqlite3.connect(BASE_DE_DATOS)
cursor   = conexion.cursor()

# ─── ETL: INGRESOS ────────────────────────────────────────────────────────────
print("Procesando ingresos...")
registros  = leer_hoja(libro, "ingresos")
filas_ok   = []
filas_err  = []

for i, r in enumerate(registros, 2):
    errores = []
    fecha    = limpiar_fecha(r.get("fecha", ""))
    desc     = limpiar_texto(r.get("descripcion", ""))
    categoria= limpiar_texto(r.get("categoria", ""))
    monto    = limpiar_monto(r.get("monto", ""))
    cliente_n= limpiar_texto(r.get("cliente", ""))
    estado   = limpiar_estado(r.get("estado", ""))

    if not fecha:    errores.append("fecha inválida")
    if monto is None: errores.append(f"monto inválido: '{r.get('monto')}'")
    if not estado:   errores.append("estado vacío")

    if errores:
        filas_err.append(f"  Fila {i}: {' | '.join(errores)}")
        continue
    filas_ok.append((fecha, desc, categoria, monto, cliente_n, estado, ahora))

cursor.execute("DELETE FROM ingresos")
cursor.executemany("""
    INSERT INTO ingresos (fecha, descripcion, categoria, monto, cliente, estado, registrado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", filas_ok)

print(f"  ✓ {len(filas_ok)} registros limpios")
if filas_err:
    print(f"  ⚠ {len(filas_err)} errores:")
    for e in filas_err: print(e)

# ─── ETL: GASTOS ──────────────────────────────────────────────────────────────
print("\nProcesando gastos...")
registros = leer_hoja(libro, "gastos")
filas_ok  = []
filas_err = []

for i, r in enumerate(registros, 2):
    errores = []
    fecha     = limpiar_fecha(r.get("fecha", ""))
    desc      = limpiar_texto(r.get("descripcion", ""))
    categoria = limpiar_texto(r.get("categoria", ""))
    monto     = limpiar_monto(r.get("monto", ""))
    proveedor = limpiar_texto(r.get("proveedor", ""))
    estado    = limpiar_estado(r.get("estado", ""))

    if not fecha:     errores.append("fecha inválida")
    if monto is None: errores.append(f"monto inválido: '{r.get('monto')}'")
    if not estado:    errores.append("estado vacío")

    if errores:
        filas_err.append(f"  Fila {i}: {' | '.join(errores)}")
        continue
    filas_ok.append((fecha, desc, categoria, monto, proveedor, estado, ahora))

cursor.execute("DELETE FROM gastos")
cursor.executemany("""
    INSERT INTO gastos (fecha, descripcion, categoria, monto, proveedor, estado, registrado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", filas_ok)

print(f"  ✓ {len(filas_ok)} registros limpios")
if filas_err:
    print(f"  ⚠ {len(filas_err)} errores:")
    for e in filas_err: print(e)

# ─── ETL: CUENTAS POR COBRAR ──────────────────────────────────────────────────
print("\nProcesando cuentas por cobrar...")
registros = leer_hoja(libro, "cuentas_por_cobrar")
filas_ok  = []
filas_err = []

for i, r in enumerate(registros, 2):
    errores = []
    f_emision    = limpiar_fecha(r.get("fecha_emision", ""))
    f_vencimiento= limpiar_fecha(r.get("fecha_vencimiento", ""))
    cliente_n    = limpiar_texto(r.get("cliente", ""))
    desc         = limpiar_texto(r.get("descripcion", ""))
    monto        = limpiar_monto(r.get("monto", ""))
    estado       = limpiar_estado(r.get("estado", ""))

    if not f_emision:     errores.append("fecha emisión inválida")
    if not f_vencimiento: errores.append("fecha vencimiento inválida")
    if monto is None:     errores.append(f"monto inválido: '{r.get('monto')}'")
    if not estado:        errores.append("estado vacío")

    if errores:
        filas_err.append(f"  Fila {i}: {' | '.join(errores)}")
        continue
    filas_ok.append((f_emision, f_vencimiento, cliente_n, desc, monto, estado, ahora))

cursor.execute("DELETE FROM cuentas_por_cobrar")
cursor.executemany("""
    INSERT INTO cuentas_por_cobrar
        (fecha_emision, fecha_vencimiento, cliente, descripcion, monto, estado, registrado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", filas_ok)

print(f"  ✓ {len(filas_ok)} registros limpios")
if filas_err:
    print(f"  ⚠ {len(filas_err)} errores:")
    for e in filas_err: print(e)

# ─── ETL: CUENTAS POR PAGAR ───────────────────────────────────────────────────
print("\nProcesando cuentas por pagar...")
registros = leer_hoja(libro, "cuentas_por_pagar")
filas_ok  = []
filas_err = []

for i, r in enumerate(registros, 2):
    errores = []
    f_emision    = limpiar_fecha(r.get("fecha_emision", ""))
    f_vencimiento= limpiar_fecha(r.get("fecha_vencimiento", ""))
    proveedor    = limpiar_texto(r.get("proveedor", ""))
    desc         = limpiar_texto(r.get("descripcion", ""))
    monto        = limpiar_monto(r.get("monto", ""))
    estado       = limpiar_estado(r.get("estado", ""))

    if not f_emision:     errores.append("fecha emisión inválida")
    if not f_vencimiento: errores.append("fecha vencimiento inválida")
    if monto is None:     errores.append(f"monto inválido: '{r.get('monto')}'")
    if not estado:        errores.append("estado vacío")

    if errores:
        filas_err.append(f"  Fila {i}: {' | '.join(errores)}")
        continue
    filas_ok.append((f_emision, f_vencimiento, proveedor, desc, monto, estado, ahora))

cursor.execute("DELETE FROM cuentas_por_pagar")
cursor.executemany("""
    INSERT INTO cuentas_por_pagar
        (fecha_emision, fecha_vencimiento, proveedor, descripcion, monto, estado, registrado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", filas_ok)

print(f"  ✓ {len(filas_ok)} registros limpios")
if filas_err:
    print(f"  ⚠ {len(filas_err)} errores:")
    for e in filas_err: print(e)

# ─── RESUMEN FINAL ────────────────────────────────────────────────────────────
conexion.commit()

cursor.execute("SELECT SUM(monto) FROM ingresos WHERE estado = 'Pagado'")
ingresos_cobrados = cursor.fetchone()[0] or 0

cursor.execute("SELECT SUM(monto) FROM gastos WHERE estado = 'Pagado'")
gastos_pagados = cursor.fetchone()[0] or 0

cursor.execute("SELECT SUM(monto) FROM cuentas_por_cobrar WHERE estado = 'Pendiente'")
por_cobrar = cursor.fetchone()[0] or 0

cursor.execute("SELECT SUM(monto) FROM cuentas_por_pagar WHERE estado = 'Pendiente'")
por_pagar = cursor.fetchone()[0] or 0

conexion.close()

utilidad = ingresos_cobrados - gastos_pagados

print("\n" + "=" * 45)
print("RESUMEN CONTABLE")
print("=" * 45)
print(f"  Ingresos cobrados:    ${ingresos_cobrados:>10.2f}")
print(f"  Gastos pagados:       ${gastos_pagados:>10.2f}")
print(f"  Utilidad neta:        ${utilidad:>10.2f}")
print(f"  Por cobrar:           ${por_cobrar:>10.2f}")
print(f"  Por pagar:            ${por_pagar:>10.2f}")
print("=" * 45)
print(f"\n✓ ETL completado: {ahora}")