# 3_agente_contabilidad.py
# Contabilidad Pipeline — Agente IA

import json
import sqlite3
import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
API_KEY       = os.getenv("GROQ_API_KEY")
BASE_DE_DATOS = "contabilidad.db"

# ─── HERRAMIENTA: ejecutar SQL ─────────────────────────────────────────────────
def ejecutar_sql(consulta):
    try:
        conexion   = sqlite3.connect(BASE_DE_DATOS)
        cursor     = conexion.cursor()
        cursor.execute(consulta)
        resultados = cursor.fetchall()
        columnas   = [desc[0] for desc in cursor.description]
        conexion.close()
        if not resultados:
            return "No se encontraron resultados."
        lineas = []
        for fila in resultados:
            linea = " | ".join(f"{columnas[i]}: {fila[i]}" for i in range(len(fila)))
            lineas.append(linea)
        return "\n".join(lineas)
    except Exception as e:
        return f"Error: {str(e)}"

# ─── HERRAMIENTA: resumen contable ────────────────────────────────────────────
def resumen_contable():
    try:
        conexion = sqlite3.connect(BASE_DE_DATOS)
        cursor   = conexion.cursor()

        cursor.execute("SELECT SUM(monto) FROM ingresos WHERE estado = 'Pagado'")
        ingresos = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(monto) FROM gastos WHERE estado = 'Pagado'")
        gastos = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(monto) FROM ingresos WHERE estado = 'Pendiente'")
        ingresos_pendientes = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(monto) FROM cuentas_por_cobrar WHERE estado = 'Pendiente'")
        por_cobrar = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(monto) FROM cuentas_por_pagar WHERE estado = 'Pendiente'")
        por_pagar = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(monto) FROM cuentas_por_cobrar WHERE estado = 'Vencido'")
        vencido_cobrar = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(monto) FROM cuentas_por_pagar WHERE estado = 'Vencido'")
        vencido_pagar = cursor.fetchone()[0] or 0

        conexion.close()

        utilidad = ingresos - gastos
        return (
            f"Ingresos cobrados: ${ingresos:.2f} | "
            f"Gastos pagados: ${gastos:.2f} | "
            f"Utilidad neta: ${utilidad:.2f} | "
            f"Ingresos pendientes: ${ingresos_pendientes:.2f} | "
            f"Por cobrar: ${por_cobrar:.2f} | "
            f"Por pagar: ${por_pagar:.2f} | "
            f"Cuentas vencidas por cobrar: ${vencido_cobrar:.2f} | "
            f"Cuentas vencidas por pagar: ${vencido_pagar:.2f}"
        )
    except Exception as e:
        return f"Error: {str(e)}"

# ─── HERRAMIENTAS PARA EL MODELO ──────────────────────────────────────────────
herramientas = [
    {
        "type": "function",
        "function": {
            "name": "ejecutar_sql",
            "description": f"""Ejecuta consultas SQL sobre la base de datos contable.
            Fecha actual: {datetime.now().strftime('%Y-%m-%d')}
            Mes actual: {datetime.now().strftime('%Y-%m')}

            TABLAS DISPONIBLES:

            1. ingresos: id, fecha, descripcion, categoria, monto, cliente, estado
               - categorias: 'Servicios', 'Consultoria', 'Productos', 'Capacitacion'
               - estados: 'Pagado', 'Pendiente'

            2. gastos: id, fecha, descripcion, categoria, monto, proveedor, estado
               - categorias: 'Arriendo', 'Servicios', 'Nomina', 'Materiales', 'Marketing', 'Tecnologia', 'Transporte', 'Capacitacion', 'Mantenimiento'
               - estados: 'Pagado', 'Pendiente'

            3. cuentas_por_cobrar: id, fecha_emision, fecha_vencimiento, cliente, descripcion, monto, estado
               - estados: 'Pendiente', 'Vencido'

            4. cuentas_por_pagar: id, fecha_emision, fecha_vencimiento, proveedor, descripcion, monto, estado
               - estados: 'Pagado', 'Pendiente', 'Vencido'

            REGLAS SQL:
            - Usa SUM(monto) para totales
            - Usa GROUP BY para agrupar por categoria, cliente o proveedor
            - Usa WHERE estado = 'Pagado' para ingresos/gastos reales
            - Usa WHERE estado = 'Pendiente' para cuentas pendientes
            - Solo SELECT, nunca INSERT UPDATE DELETE""",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "La consulta SQL a ejecutar"
                    }
                },
                "required": ["consulta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_contable",
            "description": "Devuelve un resumen completo del estado contable de la empresa",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def ejecutar_herramienta(nombre, argumentos):
    if nombre == "ejecutar_sql":
        return ejecutar_sql(argumentos["consulta"])
    elif nombre == "resumen_contable":
        return resumen_contable()
    return "Herramienta no encontrada"

# ─── AGENTE PRINCIPAL ──────────────────────────────────────────────────────────
cliente = Groq(api_key=API_KEY)

system_prompt = {
    "role": "system",
    "content": f"""Eres el asistente contable de la Empresa X.
    Fecha actual: {datetime.now().strftime('%Y-%m-%d')}
    Tienes acceso a la base de datos contable con ingresos, gastos,
    cuentas por cobrar y cuentas por pagar.

    Usa siempre las herramientas para responder con datos reales.
    Responde en español claro para el dueño del negocio.

    CONCEPTOS IMPORTANTES:
    - Utilidad = Ingresos cobrados - Gastos pagados
    - Flujo de caja = dinero real disponible (pagado)
    - Cuentas por cobrar = dinero que nos deben los clientes
    - Cuentas por pagar = dinero que debemos a proveedores
    - Vencido = plazo de pago superado, requiere atención urgente

    Solo usa SELECT en SQL."""
}

print("=" * 55)
print("  📊 Asistente Contable — Empresa X")
print("=" * 55)
print("Ejemplos de preguntas:")
print("  • Dame un resumen contable del mes")
print("  • ¿Cuál es la utilidad neta?")
print("  • ¿Cuánto me deben los clientes?")
print("  • ¿Qué cuentas están vencidas?")
print("  • ¿Cuál es mi categoría de gasto más alta?")
print("  • ¿Cuánto debo a proveedores?")
print("  • Escribe 'salir' para terminar")
print("=" * 55)

while True:
    try:
        pregunta = input("\nTú: ").strip()
    except EOFError:
        break

    if pregunta.lower() == "salir":
        print("\nAsistente: ¡Hasta luego! 📊")
        break

    if not pregunta:
        continue

    messages_turno = [system_prompt, {"role": "user", "content": pregunta}]

    respuesta = cliente.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages_turno,
        tools=herramientas,
        tool_choice="auto"
    )

    mensaje = respuesta.choices[0].message

    if mensaje.tool_calls:
        messages_turno.append({"role": "assistant", "tool_calls": mensaje.tool_calls})

        for tool_call in mensaje.tool_calls:
            nombre     = tool_call.function.name
            argumentos = json.loads(tool_call.function.arguments)
            if nombre == "ejecutar_sql":
                print(f"\n  [SQL] {argumentos.get('consulta', '')}")
            resultado = ejecutar_herramienta(nombre, argumentos)
            messages_turno.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(resultado)
            })

        # segunda llamada sin tools para forzar respuesta en texto
        respuesta_final = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_turno
        )
        respuesta_texto = respuesta_final.choices[0].message.content
        if not respuesta_texto:
            respuesta_texto = "No encontré datos para responder esa pregunta."
    else:
        respuesta_texto = mensaje.content

    print(f"\nAsistente: {respuesta_texto}")