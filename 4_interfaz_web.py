# 4_interfaz_web.py
# Contabilidad Pipeline — Interfaz web con Streamlit

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
API_KEY       = os.getenv("GROQ_API_KEY")
BASE_DE_DATOS = "contabilidad.db"

# ─── CONFIGURACIÓN DE LA PÁGINA ───────────────────────────────────────────────
st.set_page_config(
    page_title="Asistente Contable — Empresa X",
    page_icon="📊",
    layout="wide"
)

# ─── FUNCIONES DE BASE DE DATOS ───────────────────────────────────────────────
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
        return {
            "ingresos": ingresos,
            "gastos": gastos,
            "utilidad": utilidad,
            "ingresos_pendientes": ingresos_pendientes,
            "por_cobrar": por_cobrar,
            "por_pagar": por_pagar,
            "vencido_cobrar": vencido_cobrar,
            "vencido_pagar": vencido_pagar
        }
    except Exception as e:
        return None

def ejecutar_herramienta(nombre, argumentos):
    if nombre == "ejecutar_sql":
        return ejecutar_sql(argumentos["consulta"])
    elif nombre == "resumen_contable":
        r = resumen_contable()
        if r:
            return (
                f"Ingresos cobrados: ${r['ingresos']:.2f} | "
                f"Gastos pagados: ${r['gastos']:.2f} | "
                f"Utilidad neta: ${r['utilidad']:.2f} | "
                f"Por cobrar: ${r['por_cobrar']:.2f} | "
                f"Por pagar: ${r['por_pagar']:.2f} | "
                f"Vencido por cobrar: ${r['vencido_cobrar']:.2f} | "
                f"Vencido por pagar: ${r['vencido_pagar']:.2f}"
            )
        return "Error al obtener resumen"
    return "Herramienta no encontrada"

# ─── HERRAMIENTAS PARA EL MODELO ──────────────────────────────────────────────
herramientas = [
    {
        "type": "function",
        "function": {
            "name": "ejecutar_sql",
            "description": f"""Ejecuta consultas SQL sobre la base de datos contable.
            Fecha actual: {datetime.now().strftime('%Y-%m-%d')}
            TABLAS: ingresos, gastos, cuentas_por_cobrar, cuentas_por_pagar
            COLUMNAS: fecha, descripcion, categoria, monto, estado
            ESTADOS: 'Pagado', 'Pendiente', 'Vencido'
            Solo SELECT.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "Consulta SQL"}
                },
                "required": ["consulta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_contable",
            "description": "Devuelve resumen completo del estado contable",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

system_prompt = {
    "role": "system",
    "content": f"""Eres el asistente contable de la Empresa X.
    Fecha actual: {datetime.now().strftime('%Y-%m-%d')}.
    Usa las herramientas para responder con datos reales.
    Responde en español claro para el dueño del negocio.
    Utilidad = Ingresos cobrados - Gastos pagados.
    Solo usa SELECT en SQL."""
}

# ─── FUNCIÓN DEL AGENTE ───────────────────────────────────────────────────────
def consultar_agente(pregunta):
    cliente = Groq(api_key=API_KEY)
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
            resultado  = ejecutar_herramienta(nombre, argumentos)
            messages_turno.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(resultado)
            })
        respuesta_final = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_turno
        )
        return respuesta_final.choices[0].message.content or "No encontré datos."
    else:
        return mensaje.content

# ─── INTERFAZ PRINCIPAL ───────────────────────────────────────────────────────
st.title("📊 Asistente Contable — Empresa X")
st.caption(f"Datos actualizados al {datetime.now().strftime('%d/%m/%Y')}")

# ─── PANEL DE MÉTRICAS ────────────────────────────────────────────────────────
datos = resumen_contable()
if datos:
    st.subheader("Resumen del mes")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ingresos cobrados", f"${datos['ingresos']:,.2f}")
        st.metric("Ingresos pendientes", f"${datos['ingresos_pendientes']:,.2f}")
    with col2:
        st.metric("Gastos pagados", f"${datos['gastos']:,.2f}")
        st.metric("Por pagar", f"${datos['por_pagar']:,.2f}")
    with col3:
        utilidad = datos['utilidad']
        st.metric(
            "Utilidad neta",
            f"${utilidad:,.2f}",
            delta=f"{'Positiva' if utilidad >= 0 else 'Negativa'}"
        )
        st.metric("Por cobrar", f"${datos['por_cobrar']:,.2f}")

    if datos['vencido_cobrar'] > 0 or datos['vencido_pagar'] > 0:
        st.warning(
            f"⚠ Cuentas vencidas — "
            f"Por cobrar: ${datos['vencido_cobrar']:,.2f} | "
            f"Por pagar: ${datos['vencido_pagar']:,.2f}"
        )

st.divider()

# ─── CHAT DEL AGENTE ──────────────────────────────────────────────────────────
st.subheader("💬 Consulta al asistente")

# inicializar historial
if "historial" not in st.session_state:
    st.session_state.historial = []

# mostrar historial
for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

# preguntas rápidas
st.write("**Preguntas frecuentes:**")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📈 ¿Cuál es la utilidad neta?"):
        st.session_state.pregunta_rapida = "¿Cuál es la utilidad neta?"
with col2:
    if st.button("⚠ ¿Qué cuentas están vencidas?"):
        st.session_state.pregunta_rapida = "¿Qué cuentas están vencidas?"
with col3:
    if st.button("💸 ¿Cuál es mi gasto más alto?"):
        st.session_state.pregunta_rapida = "¿Cuál es mi categoría de gasto más alta?"

# input del usuario
pregunta = st.chat_input("Escribe tu pregunta contable...")

# manejar pregunta rápida
if "pregunta_rapida" in st.session_state and st.session_state.pregunta_rapida:
    pregunta = st.session_state.pregunta_rapida
    st.session_state.pregunta_rapida = None

if pregunta:
    # mostrar pregunta
    with st.chat_message("user"):
        st.write(pregunta)
    st.session_state.historial.append({"rol": "user", "texto": pregunta})

    # obtener respuesta
    with st.chat_message("assistant"):
        with st.spinner("Consultando la base de datos..."):
            respuesta = consultar_agente(pregunta)
        st.write(respuesta)
    st.session_state.historial.append({"rol": "assistant", "texto": respuesta})

    st.rerun()

# botón limpiar historial
if st.session_state.historial:
    if st.button("🗑 Limpiar conversación"):
        st.session_state.historial = []
        st.rerun()