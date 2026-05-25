# 1_crear_base_de_datos.py
# Contabilidad Pipeline — Crear base de datos

import sqlite3

BASE_DE_DATOS = "contabilidad.db"

conexion = sqlite3.connect(BASE_DE_DATOS)
cursor = conexion.cursor()

# Tabla de ingresos
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingresos (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha           TEXT NOT NULL,
        descripcion     TEXT NOT NULL,
        categoria       TEXT NOT NULL,
        monto           REAL NOT NULL,
        cliente         TEXT,
        estado          TEXT NOT NULL,
        registrado_en   TEXT NOT NULL
    )
""")

# Tabla de gastos
cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha           TEXT NOT NULL,
        descripcion     TEXT NOT NULL,
        categoria       TEXT NOT NULL,
        monto           REAL NOT NULL,
        proveedor       TEXT,
        estado          TEXT NOT NULL,
        registrado_en   TEXT NOT NULL
    )
""")

# Tabla de cuentas por cobrar
cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas_por_cobrar (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_emision   TEXT NOT NULL,
        fecha_vencimiento TEXT NOT NULL,
        cliente         TEXT NOT NULL,
        descripcion     TEXT NOT NULL,
        monto           REAL NOT NULL,
        estado          TEXT NOT NULL,
        registrado_en   TEXT NOT NULL
    )
""")

# Tabla de cuentas por pagar
cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_emision   TEXT NOT NULL,
        fecha_vencimiento TEXT NOT NULL,
        proveedor       TEXT NOT NULL,
        descripcion     TEXT NOT NULL,
        monto           REAL NOT NULL,
        estado          TEXT NOT NULL,
        registrado_en   TEXT NOT NULL
    )
""")

conexion.commit()
conexion.close()

print("✓ Base de datos creada: contabilidad.db")
print("✓ Tabla 'ingresos' lista")
print("✓ Tabla 'gastos' lista")
print("✓ Tabla 'cuentas_por_cobrar' lista")
print("✓ Tabla 'cuentas_por_pagar' lista")
print("\nSiguiente paso: prepara el Google Sheets")