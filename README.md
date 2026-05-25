# 📊 Pipeline Contable con IA

Sistema de automatización contable completo que extrae datos financieros
desde Google Sheets, los limpia y consolida en SQLite, y permite
consultarlos mediante un agente de inteligencia artificial en lenguaje natural.
Automatizado mensualmente con n8n.

## ¿Qué problema resuelve?

Antes: el contador revisaba manualmente 4 hojas de Excel al final del mes.
Después: el primer día de cada mes los datos se limpian solos y el dueño
puede hacer preguntas en lenguaje natural sobre el estado financiero.

## Arquitectura del pipeline

```
Google Sheets (4 hojas con datos sucios)
        ↓  [2_etl_contabilidad.py]
SQLite (contabilidad.db)
        ↓  [3_agente_contabilidad.py]
Agente IA responde preguntas contables
        ↑
n8n lo ejecuta automáticamente cada mes
        ↑
PythonAnywhere expone el endpoint
```

## Archivos

| Archivo | Descripción |
|---|---|
| `1_crear_base_de_datos.py` | Inicializa la BD con 4 tablas contables |
| `2_etl_contabilidad.py` | ETL: limpia y carga 4 hojas de Google Sheets |
| `3_agente_contabilidad.py` | Agente IA para consultas contables |

## Tablas de la base de datos

| Tabla | Contenido |
|---|---|
| `ingresos` | Ventas y cobros del mes |
| `gastos` | Pagos y egresos del mes |
| `cuentas_por_cobrar` | Facturas pendientes de clientes |
| `cuentas_por_pagar` | Facturas pendientes a proveedores |

## Instalación

**1. Clonar el repositorio:**
```bash
git clone https://github.com/Francisco1298/contabilidad-pipeline.git
cd contabilidad-pipeline
```

**2. Instalar dependencias:**
```bash
pip install gspread google-auth groq python-dotenv
```

**3. Configurar credenciales:**
- Crea un archivo `.env` con tu API key de Groq:
```
GROQ_API_KEY=tu_api_key_aqui
```

**4. Agregar credenciales de Google Cloud:**
- Descarga el JSON de tu cuenta de servicio
- Renómbralo a `credenciales.json`
- Comparte tu Google Sheet con el email de la cuenta de servicio

**5. Ejecutar:**
```bash
python 1_crear_base_de_datos.py
python 2_etl_contabilidad.py
python 3_agente_contabilidad.py
```

## Ejemplo de uso del agente

```
Tú: Dame un resumen contable del mes
Asistente: Ingresos cobrados: $11,700 | Gastos pagados: $15,184
           Utilidad neta: -$3,483 | Por cobrar: $9,950 | Por pagar: $4,930

Tú: ¿Qué cuentas están vencidas?
Asistente: Tienes 2 cuentas por cobrar vencidas por $4,450
           y 1 cuenta por pagar vencida por $250.

Tú: ¿Cuál es mi categoría de gasto más alta?
Asistente: Nómina con $8,508 representa el mayor gasto del mes.

Tú: ¿Cuánto debo a proveedores?
Asistente: Debes $5,180 entre cuentas pendientes y vencidas.
```

## Stack tecnológico

- **Python 3.12** — lenguaje principal
- **gspread** — extracción desde Google Sheets
- **sqlite3** — base de datos local
- **Groq + LLaMA 3.3** — agente de IA con function calling
- **n8n** — automatización mensual (iPaaS open source)
- **PythonAnywhere** — deploy en la nube
- **Git + GitHub** — control de versiones

## Conceptos aplicados

- ETL con limpieza de datos reales (4 formatos de fecha, montos con símbolos, textos inválidos)
- SQL: 4 tablas, SUM, GROUP BY, WHERE, estados financieros
- Agentes de IA con function calling
- Prompt engineering contable
- Deploy en la nube
- Automatización con n8n
- Variables de entorno y seguridad