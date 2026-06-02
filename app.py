"""
In Me — Sistema análisis financiero para PyMes argentinas
Streamlit + Gorq
"""

import streamlit as st
from groq import Groq
import json
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import date
from dateutil.relativedelta import relativedelta

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="In Me - Análisis financiero para PyMes argentinas",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown("""
    <style>
        /* Elimina el margen superior excesivo que muerde el contenido */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            max-width: 95% !important;
        }
        /* Fuerza a que el contenedor principal no oculte el desborde */
        .main .block-container {
            overflow: visible !important;
        }
    </style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
PROVINCES = [
    "CABA","Buenos Aires","Catamarca","Chaco","Chubut","Córdoba",
    "Corrientes","Entre Ríos","Formosa","Jujuy","La Pampa","La Rioja",
    "Mendoza","Misiones","Neuquén","Río Negro","Salta","San Juan",
    "San Luis","Santa Cruz","Santa Fe","Santiago del Estero",
    "Tierra del Fuego","Tucumán",
]

COUNTRIES = [
    "Argentina","Brasil","Uruguay","Chile","Paraguay","Bolivia",
    "Perú","Colombia","Venezuela","Ecuador","México","España",
    "Estados Unidos","Otro",
]

CITIES = {
    "CABA":["Buenos Aires (CABA)"],
    "Buenos Aires":["La Plata","Mar del Plata","Quilmes","Lanús","Lomas de Zamora",
        "Bahía Blanca","Vicente López","San Isidro","Tigre","Morón","Tres de Febrero",
        "Avellaneda","Berazategui","Florencio Varela","Merlo","Moreno","San Miguel",
        "La Matanza","General San Martín","Almirante Brown","Ezeiza","Pilar",
        "Campana","Zárate","Escobar","Pergamino","Junín","Tandil","Olavarría","Otro"],
    "Córdoba":["Córdoba Capital","Villa Carlos Paz","Río Cuarto","San Francisco",
        "Villa María","Cosquín","Alta Gracia","Río Tercero","Jesús María","Otro"],
    "Santa Fe":["Rosario","Santa Fe Capital","Rafaela","Reconquista",
        "Venado Tuerto","Esperanza","Villa Constitución","Otro"],
    "Mendoza":["Mendoza Capital","San Rafael","Godoy Cruz","Maipú","Luján de Cuyo","Otro"],
    "Tucumán":["San Miguel de Tucumán","Tafí Viejo","Yerba Buena","Concepción","Otro"],
    "Salta":["Salta Capital","San Ramón de la Nueva Orán","Tartagal","Metán","Otro"],
    "Entre Ríos":["Paraná","Concordia","Gualeguaychú","Colón","Otro"],
    "Chaco":["Resistencia","Presidencia Roque Sáenz Peña","Villa Ángela","Otro"],
    "Corrientes":["Corrientes Capital","Goya","Paso de los Libres","Mercedes","Otro"],
    "Misiones":["Posadas","Oberá","Eldorado","Puerto Iguazú","Otro"],
    "Neuquén":["Neuquén Capital","San Martín de los Andes","Cutral-Co","Zapala","Otro"],
    "Río Negro":["Bariloche","Viedma","Cipolletti","General Roca","Otro"],
    "Jujuy":["San Salvador de Jujuy","San Pedro","Palpalá","Otro"],
    "Santiago del Estero":["Santiago del Estero Capital","La Banda","Termas de Río Hondo","Otro"],
    "San Juan":["San Juan Capital","Rawson","Chimbas","Rivadavia","Otro"],
    "San Luis":["San Luis Capital","Villa Mercedes","Merlo","Otro"],
    "La Pampa":["Santa Rosa","General Pico","Otro"],
    "Catamarca":["San Fernando del Valle de Catamarca","Otro"],
    "La Rioja":["La Rioja Capital","Chilecito","Otro"],
    "Formosa":["Formosa Capital","Clorinda","Otro"],
    "Chubut":["Rawson","Comodoro Rivadavia","Puerto Madryn","Trelew","Otro"],
    "Santa Cruz":["Río Gallegos","Caleta Olivia","El Calafate","Otro"],
    "Tierra del Fuego":["Ushuaia","Río Grande","Tolhuin"]
}

RUBROS = [
    "Alimentos y Bebidas","Agro y Ganadería","Automotriz","Belleza y Estética",
    "Construcción","Consultoría","Contabilidad y Finanzas","Educación y Capacitación",
    "Electrónica y Tecnología","Energía","Eventos y Entretenimiento","Farmacia y Salud",
    "Gastronomía","Hotelería y Turismo","Hogar y Decoración","Imprenta y Gráfica",
    "Indumentaria y Textil","Industria Manufacturera","Inmobiliaria","Logística y Transporte",
    "Marketing y Publicidad","Mascotas","Metalúrgica","Minería","Muebles y Carpintería",
    "Recursos Humanos","Reparaciones y Mantenimiento","Seguridad","Servicios Jurídicos",
    "Servicios Profesionales","Software y Sistemas","Telecomunicaciones","Veterinaria",
    "Venta Mayorista","Venta Minorista","E-commerce","Salud y Bienestar","Limpieza e Higiene",
    "Distribución","Importación y Exportación","Papelería y Librería","Deportes y Fitness",
    "Arte y Diseño","Producción Audiovisual","Otro",
]

INSTRUMENTS = [
    {"id":"dolar",      "name":"Dólar (ME)",                  "cat":"Monedas",        "risk":"Riesgo Bajo",     "desc":"Resguardo de valor via Dólar MEP o CCL."},
    {"id":"plazo_fijo", "name":"Plazo Fijo",                  "cat":"Renta Fija",     "risk":"Riesgo Bajo", "desc":"Depósito a tasa fija en banco o fintech regulada."},
    {"id":"caucion",    "name":"Cauciones Bursátiles",        "cat":"Renta Fija",     "risk":"Riesgo Bajo", "desc":"Préstamo garantizado de corto plazo en el mercado de capitales."},
    {"id":"on",         "name":"Obligaciones Negociables",    "cat":"Renta Fija",     "risk":"Riesgo Bajo",     "desc":"Bonos corporativos emitidos por empresas argentinas."},
    {"id":"bonos",      "name":"Bonos Soberanos",             "cat":"Renta Fija",     "risk":"Riesgo Medio",    "desc":"Títulos de deuda del Estado Nacional."},
    {"id":"letras",     "name":"Letras del Tesoro",           "cat":"Renta Fija",     "risk":"Riesgo Bajo",     "desc":"Instrumentos de corto plazo emitidos por el Tesoro."},
    {"id":"lecap",      "name":"LECAPs",                      "cat":"Renta Fija",     "risk":"Riesgo Bajo",     "desc":"Letras de Capitalización del Banco Central."},
    {"id":"acciones",   "name":"Acciones",                    "cat":"Renta Variable", "risk":"Riesgo Alto",     "desc":"Participación en empresas cotizantes en el BYMA."},
    {"id":"fci",        "name":"Fondos Comunes de Inversión", "cat":"Renta Variable", "risk":"Riesgo Medio",    "desc":"Cartera diversificada gestionada profesionalmente."},
    {"id":"opciones",   "name":"Opciones",                    "cat":"Derivados",      "risk":"Riesgo Alto", "desc":"Contratos sobre activos subyacentes con apalancamiento."},
    {"id":"futuros",    "name":"Futuros (MatbaRofex)",        "cat":"Derivados",      "risk":"Riesgo Alto", "desc":"Contratos a término de tipo de cambio o commodities."},
    {"id":"swaps",      "name":"Swaps de Tasas",              "cat":"Derivados",      "risk":"Riesgo Alto",     "desc":"Intercambio de flujos entre tasas fijas y variables."},
]

PLATFORMS = [
    {"name":"IOL – InvertirOnline","url":"https://www.invertironline.com","color":"#003087"},
    {"name":"Balanz","url":"https://balanz.com","color":"#E63946"},
    {"name":"PPI – Portfolio Personal","url":"https://www.portfoliopersonal.com","color":"#2563EB"},
    {"name":"Binance","url":"https://www.binance.com","color":"#F0B90B"},
    {"name":"Bull Market Brokers","url":"https://bullmarketbrokers.com","color":"#16A34A"},
]

RISK_QS = [
    {"k":"maquinaria",   "q":"¿La actividad requiere maquinaria o equipamiento crítico?",      "opts":["Sí","Indiferente","No"]},
    {"k":"fallaOp",      "q":"¿Una falla operativa puede detener completamente el negocio?",   "opts":["Alto impacto","Medio impacto","Bajo impacto"]},
    {"k":"pocosProv",    "q":"¿La empresa depende de pocos proveedores?",                       "opts":["Sí","Indiferente","No"]},
    {"k":"perecederos",  "q":"¿Maneja productos perecederos, frágiles o de alta sensibilidad?","opts":["Sí","Indiferente","No"]},
    {"k":"personalEsp",  "q":"¿La operación depende de personal especializado?",                "opts":["Sí","Indiferente","No"]},
    {"k":"insuImp",      "q":"¿La empresa depende de insumos importados?",                      "opts":["Sí","Parcialmente","No"]},
    {"k":"dolar",        "q":"¿La empresa se ve afectada por variaciones del dólar?",           "opts":["Sí","Indiferente","No"]},
    {"k":"estacional",   "q":"¿Los ingresos son estacionales?",                                 "opts":["Sí","No","Indiferente"]},
    {"k":"costosFijos",  "q":"¿Qué porcentaje de costos son fijos?",                            "opts":["<30%","30%-60%",">60%"]},
    {"k":"distribucion", "q":"¿Realiza distribución o envíos?",                                  "opts":["Sí","Indiferente","No"]},
    {"k":"temporadas",   "q":"¿Depende de temporadas de alta demanda?",                         "opts":["Sí","Indiferente","No"]},
    {"k":"sistemas",     "q":"¿Depende de sistemas digitales para operar?",                     "opts":["Sí","Indiferente","No"]},
    {"k":"ventasOnline", "q":"¿Realiza ventas online?",                                          "opts":["Sí","Indiferente","No"]},
    {"k":"respaldo",     "q":"¿Cuenta con respaldo digital y seguridad?",                        "opts":["Sí","Indiferente","No"]},
    {"k":"ciberataque",  "q":"¿Ha sufrido problemas tecnológicos o ciberataques?",              "opts":["Sí","Indiferente","No"]},
    {"k":"regulado",     "q":"¿La actividad está regulada por organismos oficiales?",            "opts":["Sí","Indiferente","No"]},
    {"k":"datosSens",    "q":"¿Manipula datos sensibles de clientes?",                          "opts":["Sí","Indiferente","No"]},
    {"k":"alimentos",    "q":"¿Trabaja con alimentos, medicamentos o químicos?",                "opts":["Sí","Indiferente","No"]},
    {"k":"habilitaciones","q":"¿Requiere habilitaciones o certificaciones especiales?",         "opts":["Sí","Indiferente","No"]},
]

SIM_RATES = {
    "dolar":      {"Conservador":0.02,  "Moderado":0.06,  "Optimista":0.12},
    "plazo_fijo": {"Conservador":0.09,  "Moderado":0.11,  "Optimista":0.13},
    "caucion":    {"Conservador":0.08,  "Moderado":0.10,  "Optimista":0.12},
    "on":         {"Conservador":0.07,  "Moderado":0.10,  "Optimista":0.15},
    "bonos":      {"Conservador":0.04,  "Moderado":0.11,  "Optimista":0.22},
    "letras":     {"Conservador":0.09,  "Moderado":0.11,  "Optimista":0.13},
    "lecap":      {"Conservador":0.10,  "Moderado":0.12,  "Optimista":0.14},
    "acciones":   {"Conservador":-0.08, "Moderado":0.18,  "Optimista":0.45},
    "fci":        {"Conservador":0.07,  "Moderado":0.13,  "Optimista":0.24},
    "opciones":   {"Conservador":-0.40, "Moderado":0.25,  "Optimista":1.20},
    "futuros":    {"Conservador":-0.25, "Moderado":0.18,  "Optimista":0.70},
    "swaps":      {"Conservador":0.03,  "Moderado":0.08,  "Optimista":0.14},
}

RISK_COLORS = {
    "Riesgo Bajo": "#2ECC71",   # Verde
    "Riesgo Medio": "#F39C12",  # Naranja
    "Riesgo Alto": "#E74C3C",   # Rojo
}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;}
.block-container{padding-top:1rem!important;max-width:900px!important;}
.pyme-card{background:#fff;border-radius:12px;padding:1.75rem;
    box-shadow:0 2px 12px rgba(18,60,105,.08);margin-bottom:1.25rem;
    border:1px solid #E0E6ED;}
.pyme-card h2{color:#123C69;font-weight:800;margin-bottom:.3rem;font-size:1.35rem;}
.pyme-card .sub{color:#7F8C8D;font-size:.88rem;margin-bottom:1.25rem;}
.risk-card{border-radius:12px;padding:1.5rem;color:white;margin-bottom:1.25rem;}
.risk-badge{display:inline-block;background:rgba(255,255,255,.2);border-radius:20px;
    padding:5px 16px;font-weight:700;font-size:.95rem;margin-bottom:.65rem;}
.ai-box{background:linear-gradient(135deg,rgba(18,60,105,.04),rgba(77,168,218,.07));
    border:1.5px solid rgba(77,168,218,.25);border-radius:10px;padding:1.1rem;
    margin:.75rem 0;font-size:.88rem;line-height:1.7;}
.hint-box{background:rgba(46,204,113,.1);border:1.5px solid #2ECC71;border-radius:9px;
    padding:.8rem 1rem;font-size:.85rem;font-weight:600;color:#1e8449;margin:.75rem 0;}
.compat-bar-bg{background:#E0E6ED;border-radius:4px;height:8px;overflow:hidden;flex:1;}
.compat-fill{height:8px;border-radius:4px;}
div.stButton>button{background:#123C69!important;color:white!important;
    border:none!important;border-radius:8px!important;font-weight:600!important;
    font-family:'Inter',sans-serif!important;}
div.stButton>button:hover{background:#0d2d50!important;}
.stepper-bar{display:flex;align-items:center;background:white;border-radius:12px;
    padding:1rem 1.5rem;box-shadow:0 2px 12px rgba(18,60,105,.08);margin-bottom:1.75rem;}
.step-dot{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;
    justify-content:center;font-size:.75rem;font-weight:700;flex-shrink:0;}
.sd-done{background:#2ECC71;color:white;}
.sd-active{background:#123C69;color:white;box-shadow:0 0 0 4px rgba(18,60,105,.15);}
.sd-pend{background:#F5F7FA;color:#7F8C8D;border:2px solid #E0E6ED;}
.step-line{flex:1;height:2px;background:#E0E6ED;margin:0 4px;}
.sl-done{background:#2ECC71;}
.step-lbl{font-size:.6rem;color:#7F8C8D;text-align:center;margin-top:4px;font-weight:600;}
.sl-act{color:#123C69;}
.step-item{display:flex;flex-direction:column;align-items:center;}


.float-bot-btn:hover {
    transform: scale(1.12);
    box-shadow:
        0 0 30px rgba(77,168,218,.7),
        0 14px 45px rgba(18,60,105,.6);
}

/* Movimiento flotante */
@keyframes floatBot {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
    100% { transform: translateY(0px); }
}

/* Glow/pulso */
@keyframes pulseBot {
    0% {
        box-shadow:
        0 0 0 0 rgba(77,168,218,.55),
        0 10px 35px rgba(18,60,105,.45);
    }

    70% {
        box-shadow:
        0 0 0 18px rgba(77,168,218,0),
        0 10px 35px rgba(18,60,105,.45);
    }

    100% {
        box-shadow:
        0 0 0 0 rgba(77,168,218,0),
        0 10px 35px rgba(18,60,105,.45);
    }
}

/* Robot */
.bot-emoji {
    animation: robotMove 2s infinite ease-in-out;
    display: inline-block;
}

@keyframes robotMove {
    0% { transform: rotate(-4deg); }
    50% { transform: rotate(4deg); }
    100% { transform: rotate(-4deg); }
}
.float-chat-panel {
    position: fixed; bottom: 100px; right: 28px; z-index: 9998;
    width: 340px; background: white; border-radius: 16px;
    box-shadow: 0 8px 40px rgba(18,60,105,.18);
    border: 1.5px solid #E0E6ED; display: none; flex-direction: column;
    max-height: 480px; overflow: hidden;
}
.float-chat-panel.open { display: flex; }
.float-chat-header {
    background: #123C69; color: white; padding: .75rem 1rem;
    border-radius: 14px 14px 0 0; font-weight: 700; font-size: .9rem;
    display: flex; align-items: center; gap: .5rem;
}
.float-chat-messages {
    flex: 1; overflow-y: auto; padding: .75rem; font-size: .83rem;
    display: flex; flex-direction: column; gap: .5rem;
}
.fcm-user { background: #123C69; color: white; border-radius: 12px 12px 2px 12px; padding: .5rem .75rem; align-self: flex-end; max-width: 80%; }
.fcm-bot  { background: #F0F4F8; color: #1a1a1a; border-radius: 12px 12px 12px 2px; padding: .5rem .75rem; align-self: flex-start; max-width: 80%; }
.float-chat-input { display: flex; border-top: 1px solid #E0E6ED; padding: .5rem; gap: .4rem; }
.float-chat-input input { flex: 1; border: 1.5px solid #E0E6ED; border-radius: 8px; padding: .4rem .7rem; font-size: .83rem; outline: none; }
.float-chat-input button { background: #123C69; color: white; border: none; border-radius: 8px; padding: .4rem .85rem; font-weight: 700; cursor: pointer; font-size: .83rem; }
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def get_client():
    key = st.secrets.get("GROQ_API_KEY","")
    if not key:
        st.error("Configurá `GROQ_API_KEY` en `.streamlit/secrets.toml`")
        st.stop()
    return Groq(api_key=key)


def call_groq(messages, system=""):
    client = get_client()
    msgs = []
    if system:
        msgs.append({
            "role": "system",
            "content": system
        })
    msgs.extend(messages)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=msgs,
        max_tokens=1000,
    )
    return resp.choices[0].message.content


def parse_json(text):
    text = re.sub(r"```json|```","",text).strip()
    try:
        return json.loads(text)
    except Exception as e:
        st.error(f"Error parseando JSON: {e}")
        return {}


def validate_cuit(v):
    return bool(re.match(r"^\d{2}-\d{8}-\d{1}$",v))

def compute_risk(risk):
    # Definimos los conjuntos de respuestas exactas para agruparlas por tipo
    a_set = {"Sí", "Alto impacto", "<30%"}
    b_set = {"Indiferente", "Medio impacto", "30%-60%", "Parcialmente"}
    c_set = {"No", "Bajo impacto", ">60%"} # Agregamos explícitamente el conjunto C
    
    a = b = c = 0
    for v in risk.values():
        if v in a_set: a += 1
        elif v in b_set: b += 1
        elif v in c_set: c += 1
            
    # Lógica de decisión basada en la mayoría simple
    if a >= b and a >= c: 
        return "Riesgo Alto"
    elif b >= a and b >= c: 
        return "Riesgo Medio"
    else: 
        return "Riesgo Bajo"


@st.cache_data(ttl=600)
def obtener_mercado_completo_real():

    categorias = {
        "Acciones (Merval)": [],
        "Cedears populares": [],
        "Bonos y ONs": []
    }

 
    # Lista dinámica REAL
    tickers_merval = [
        "GGAL.BA","YPFD.BA","PAMP.BA","BMA.BA",
        "ALUA.BA","TXAR.BA","LOMA.BA","CEPU.BA",
        "SUPV.BA","BYMA.BA","COME.BA","EDN.BA"
    ]

    categorias["Acciones (Merval)"] = tickers_merval

    # =========================
    # CEDEARS
    # =========================
    categorias["Cedears populares"] = [
        "AAPL","MSFT","AMZN","META",
        "NVDA","TSLA","GOOGL","MELI"
    ]

    # =========================
    # BONOS
    # =========================
    categorias["Bonos y ONs"] = [
        "AL30.BA",
        "GD30.BA",
        "GD35.BA",
        "AL29.BA",
        "AE38.BA"
    ]

    # =========================
    # DESCARGA REAL
    # =========================
    todos = []

    for lista in categorias.values():
        todos.extend(lista)

    datos = yf.download(
        tickers=todos,
        period="5d",
        auto_adjust=True,
        progress=False,
        group_by="ticker"
    )

    resultado_final = {
        "Acciones (Merval)": [],
        "Cedears populares": [],
        "Bonos y ONs": []
    }

    for categoria, lista in categorias.items():

        for ticker in lista:

            try:

                if isinstance(datos.columns, pd.MultiIndex):

                    serie = datos[ticker]["Close"].dropna()

                else:

                    serie = datos["Close"].dropna()

                if serie.empty:
                    continue

                precio = serie.iloc[-1]

                resultado_final[categoria].append({
                    "activo": ticker.replace(".BA", ""),
                    "precio": round(float(precio), 2)
                })

            except Exception as e:
                print(f"Error con {ticker}: {e}")
                continue

    return resultado_final


def compat_color(pct):
    return "#2ECC71" if pct>=70 else ("#F39C12" if pct>=40 else "#E74C3C")


def stepper(current):
    steps=["Usuario","Negocio", "Instrumentos"]
    parts=[]
    for i,s in enumerate(steps):
        n=i+1
        if current>n:   cls,lbl,dot="sd-done","sl-act","✓"
        elif current==n: cls,lbl,dot="sd-active","sl-act",str(n)
        else:            cls,lbl,dot="sd-pend","",str(n)
        parts.append(f'<div class="step-item"><div class="step-dot {cls}">{dot}</div>'
                     f'<div class="step-lbl {lbl}">{s}</div></div>')
        if i<len(steps)-1:
            lc="sl-done" if current>n else ""
            parts.append(f'<div class="step-line {lc}"></div>')
    st.markdown(f'<div class="stepper-bar">{"".join(parts)}</div>',unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def obtener_accion(ticker):

    data = yf.Ticker(ticker)

    info = data.info

    hist = data.history(period="5y")

    precio = info.get("currentPrice")

    if precio is None and not hist.empty:
        precio = round(hist["Close"].iloc[-1], 2)

    return {
        "precio": precio,
        "hist": hist
    }


def grafico_velas(hist, ticker):

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=hist.index,
                open=hist["Open"],
                high=hist["High"],
                low=hist["Low"],
                close=hist["Close"],
                name=ticker
            )
        ]
    )

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False
    )

    return fig

# ─── SESSION ──────────────────────────────────────────────────────────────────
def init():
    defs={
        "step":1,
        "u_nombre":"","u_apellido":"","u_fecha":None,"u_cuit":"",
        "u_pais":"Argentina","u_prov":"","u_ciudad":"","u_fin":"",
        "b_desc":"","b_emp":"","b_fac":"","b_mon":"ARS",
        "b_rubro":"","b_origen":[],"b_modo":"","b_prov_u":"","b_merc":"",
        "risk":{},"profile":"","summary":"","explicacion":"",
        "scores":{},"chat":[],
    }
    for k,v in defs.items():
        if k not in st.session_state:
            st.session_state[k]=v


# ─── STEP 1 ───────────────────────────────────────────────────────────────────
def step1():
    st.markdown('<div class="pyme-card"><h2>👤 Creá tu cuenta</h2>'
                '<p class="sub">Completá tus datos para iniciar el diagnóstico de tu PyMe.</p>',
                unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: st.session_state.u_nombre=st.text_input("Nombre *",value=st.session_state.u_nombre,placeholder="Juan")
    with c2: st.session_state.u_apellido=st.text_input("Apellido *",value=st.session_state.u_apellido,placeholder="García")

    c3,c4=st.columns(2)
    with c3:
        fd=st.date_input("Fecha de nacimiento *",
            value=st.session_state.u_fecha or date(1990,1,1),
            min_value=date(1920,1,1),
            max_value=date.today()-relativedelta(years=18))
        st.session_state.u_fecha=fd
    with c4:
        cuit=st.text_input("CUIT/CUIL *",value=st.session_state.u_cuit,
            placeholder="20-12345678-9",help="Formato: XX-XXXXXXXX-X")
        st.session_state.u_cuit=cuit
        if cuit and not validate_cuit(cuit):
            st.error("Formato incorrecto. Ejemplo: 20-12345678-9")

    c5,c6=st.columns(2)
    with c5:
        st.session_state.u_pais=st.selectbox("País *",COUNTRIES,
            index=COUNTRIES.index(st.session_state.u_pais) if st.session_state.u_pais in COUNTRIES else 0)
    with c6:
        prov_list=["— Seleccioná —"]+PROVINCES
        prov_idx=PROVINCES.index(st.session_state.u_prov)+1 if st.session_state.u_prov in PROVINCES else 0
        prov=st.selectbox("Provincia *",prov_list,index=prov_idx)
        if prov!="— Seleccioná —":
            if prov!=st.session_state.u_prov: st.session_state.u_ciudad=""
            st.session_state.u_prov=prov

    cities=CITIES.get(st.session_state.u_prov,["Otro"])
    city_list=["— Seleccioná —"]+cities
    city_idx=cities.index(st.session_state.u_ciudad)+1 if st.session_state.u_ciudad in cities else 0
    city=st.selectbox("Ciudad *",city_list,index=city_idx,disabled=not st.session_state.u_prov)
    if city!="— Seleccioná —": st.session_state.u_ciudad=city

    st.write("**Tipo de financiamiento \***")
    fin_opts=["Propio","De terceros","Mixto"]
    fin_idx=fin_opts.index(st.session_state.u_fin) if st.session_state.u_fin in fin_opts else 0
    st.session_state.u_fin=st.radio("",fin_opts,index=fin_idx,horizontal=True,label_visibility="collapsed")

    st.markdown('</div>',unsafe_allow_html=True)

    age_ok=st.session_state.u_fecha and (date.today()-st.session_state.u_fecha).days/365.25>=18
    valid=(st.session_state.u_nombre and st.session_state.u_apellido and age_ok
           and validate_cuit(st.session_state.u_cuit) and st.session_state.u_pais
           and st.session_state.u_prov and st.session_state.u_ciudad and st.session_state.u_fin)
    if st.button("Continuar →",disabled=not valid):
        st.session_state.step=2; st.rerun()

def generar_compatibilidades():

    sys = """
    Sos un asesor financiero especializado en PyMes argentinas.
    
    Respondé EXCLUSIVAMENTE un JSON válido. 
    
    NO escribas explicaciones. 
    NO uses markdown. 
    NO uses ```json. 
    NO agreges texto antes ni después. 

    Analizá:
    - Perfil de riesgo
    - Rubro
    - Facturación
    - Empleados
    - Mercado
    - Origen de insumos
    - Dependencia del dólar
    - Respuestas del cuestionario

    Asigná obligatoriamente un valor entero entre 0 y 100 para TODOS los campos.

    No omitas ningún campo.

    Si no estás seguro usa un valor estimado.

    Devolvé únicamente JSON válido que tenga exactamente esta estructura:
    {
        "dolar":0,
        "plazo_fijo":0,
        "caucion":0,
        "on":0,
        "bonos":0,
        "letras":0,
        "lecap":0,
        "acciones":0,
        "fci_rf":0,
        "fci_rv":0,
        "fci_mixto":0,
        "opciones":0,
        "futuros":0,
        "swap_tasas":0,
        "swap_commodities":0,
        "swap_monedas":0
    }
    """

    payload = {
        "perfil": st.session_state.profile,
        "rubro": st.session_state.b_rubro,
        "facturacion": st.session_state.b_fac,
        "empleados": st.session_state.b_emp,
        "mercado": st.session_state.b_merc,
        "origen_insumos": st.session_state.b_origen,
        "moneda": st.session_state.b_mon,
        "modo_operacion": st.session_state.b_modo,
        "depende_proveedor_unico": st.session_state.b_prov_u,
        "cuestionario": st.session_state.risk
    }

    return parse_json(
        call_groq(
            [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            sys
        )
    )

def step2():
    st.markdown('<div class="pyme-card"><h2>🏢 Tu negocio</h2>'
                '<p class="sub">Completá los datos de tu empresa y evaluá tu perfil de riesgo.</p>',
                unsafe_allow_html=True)

    # ── Caja descripción libre ─────────────────────────────────────────────
    st.session_state.b_desc = st.text_area(
        "Describí tu negocio",
        value=st.session_state.b_desc,
        placeholder="Contanos sobre tu proyecto: actividad, empleados, facturación, cómo operás...",
        height=140
    )

    if st.session_state.b_desc and st.button("✨ Analizar con IA y pre-completar"):
        with st.spinner("Analizando..."):
            sys = (
                "Sos un asistente financiero para PyMes argentinas. "
                "Extraé y devolvé SOLO un objeto JSON (sin markdown):\n"
                '{"cantidadEmpleados":number|null,"facturacionMensual":number|null,'
                '"monedaFacturacion":"ARS"|"USD"|null,"rubro":string|null,'
                '"modoOperacion":"fisica"|"online"|"ambas"|null,"dependeProveedorUnico":boolean|null}'
            )
            r = parse_json(call_groq([{"role": "user", "content": st.session_state.b_desc}], sys))
            if r.get("cantidadEmpleados"): st.session_state.b_emp = str(int(r["cantidadEmpleados"]))
            if r.get("facturacionMensual"): st.session_state.b_fac = str(int(r["facturacionMensual"]))
            if r.get("monedaFacturacion"): st.session_state.b_mon = r["monedaFacturacion"]
            if r.get("rubro"):
                m = next((x for x in RUBROS if r["rubro"].lower() in x.lower()), None)
                if m: st.session_state.b_rubro = m
            if r.get("modoOperacion"):
                st.session_state.b_modo = {"fisica": "Física", "online": "Online", "ambas": "Ambas"}.get(r["modoOperacion"], "")
            if r.get("dependeProveedorUnico") is not None:
                st.session_state.b_prov_u = "Sí" if r["dependeProveedorUnico"] else "No"
        st.success("✅ Formulario pre-completado. Revisá los campos abajo.")

    st.markdown("---")

    # ── Formulario del negocio ─────────────────────────────────────────────
    st.markdown("#### 📋 Formulario del negocio")

    c1, c2 = st.columns(2)
    with c1: st.session_state.b_emp = st.text_input("Cantidad de empleados", value=st.session_state.b_emp, placeholder="Ej: 5")
    with c2: st.session_state.b_fac = st.text_input("Facturación mensual promedio", value=st.session_state.b_fac, placeholder="Ej: 500000")

    c3, c4 = st.columns(2)
    with c3:
        mon_opts = ["ARS", "USD", "EUR"]
        st.session_state.b_mon = st.selectbox("Moneda", mon_opts, index=mon_opts.index(st.session_state.b_mon) if st.session_state.b_mon in mon_opts else 0)
    with c4:
        rub_list = ["— Seleccioná —"] + RUBROS
        rub_idx = RUBROS.index(st.session_state.b_rubro) + 1 if st.session_state.b_rubro in RUBROS else 0
        rub = st.selectbox("Rubro", rub_list, index=rub_idx)
        if rub != "— Seleccioná —": st.session_state.b_rubro = rub

    st.write("**Origen de insumos**")
    orig_opts = ["Nacionales", "Importados", "Ambos"]
    cols = st.columns(3)
    new_orig = []
    for i, opt in enumerate(orig_opts):
        if cols[i].checkbox(opt, value=opt in st.session_state.b_origen, key=f"orig_{opt}"):
            new_orig.append(opt)
    st.session_state.b_origen = new_orig

    modo_opts = ["Física", "Online", "Ambas"]
    modo_idx = modo_opts.index(st.session_state.b_modo) if st.session_state.b_modo in modo_opts else 0
    st.write("**¿Opera física, online o ambas?**")
    st.session_state.b_modo = st.radio("", modo_opts, index=modo_idx, horizontal=True, label_visibility="collapsed", key="modo_r")

    c5, c6 = st.columns(2)
    with c5:
        pu_opts = ["Sí", "No"]
        pu_idx = pu_opts.index(st.session_state.b_prov_u) if st.session_state.b_prov_u in pu_opts else 0
        st.write("**¿Depende de un único proveedor?**")
        st.session_state.b_prov_u = st.radio("", pu_opts, index=pu_idx, horizontal=True, label_visibility="collapsed", key="prov_r")
    with c6:
        me_opts = ["Nacional", "Internacional", "Ambas"]
        me_idx = me_opts.index(st.session_state.b_merc) if st.session_state.b_merc in me_opts else 0
        st.write("**¿En qué mercado opera?**")
        st.session_state.b_merc = st.radio("", me_opts, index=me_idx, horizontal=True, label_visibility="collapsed", key="merc_r")

    st.markdown("---")

    # ── Evaluación de riesgo ───────────────────────────────────────────────
    st.markdown("#### ⚠️ Evaluación de riesgo")

    risk = st.session_state.risk.copy()
    filled = len(risk)
    if filled >= 10:
        st.markdown(f'<div class="hint-box">✅ Ya respondiste {filled}/19 preguntas.</div>', unsafe_allow_html=True)
    else:
        st.caption(f"{filled}/19 respondidas — mínimo 10 para continuar.")

    for q in RISK_QS:
        opts = q["opts"]
        cur = risk.get(q["k"], None)
        idx = opts.index(cur) if cur in opts else None
        ans = st.radio(q["q"], opts, index=idx, horizontal=True, key=f"rq_{q['k']}")
        if ans: risk[q["k"]] = ans
    st.session_state.risk = risk

    st.markdown("---")

    # ── Análisis de riesgo IA ──────────────────────────────────────────────
    st.markdown("#### 🛡️ Análisis de perfil de riesgo")

    if not st.session_state.profile:
        biz_ready = st.session_state.b_emp and st.session_state.b_fac and st.session_state.b_rubro
        risk_ready = len(st.session_state.risk) >= 5
        if biz_ready or risk_ready:
            if st.button("✨ Generar análisis de riesgo con IA"):
                with st.spinner("Analizando tu negocio con IA..."):
                    computed = compute_risk(st.session_state.risk)
                    payload = {
                        "negocio": {"empleados": st.session_state.b_emp, "facturacion": st.session_state.b_fac,
                                    "moneda": st.session_state.b_mon, "rubro": st.session_state.b_rubro,
                                    "modo": st.session_state.b_modo, "mercado": st.session_state.b_merc},
                        "riesgo": st.session_state.risk
                    }
                    sys = ('Sos analista financiero experto en PyMes argentinas. Devolvé SOLO JSON válido:\n'
                           '{"resumen":"3-4 oraciones sobre el negocio","explicacion":"2-3 oraciones sobre factores de riesgo"}')
                    d = parse_json(call_groq([{"role": "user", "content": json.dumps(payload)}], sys))
                    st.session_state.profile = computed
                    st.session_state.summary = d.get("resumen", "Diagnóstico generado exitosamente.")
                    st.session_state.explicacion = d.get("explicacion", "Los factores analizados determinaron el perfil.")
                st.rerun()
        else:
            st.info("Completá al menos los datos básicos del negocio o 5 preguntas de riesgo para generar el análisis.")
    else:
        color = RISK_COLORS.get(st.session_state.profile, "#F39C12")
        icon = {"Riesgo Bajo": "✅", "Riesgo Medio": "ℹ️", "Riesgo Alto": "⚠️"}.get(st.session_state.profile, "📊")
        st.markdown(
            f'<div class="risk-card" style="background:{color};">'
            f'<div class="risk-badge">{icon} {st.session_state.profile}</div>'
            f'<p style="font-size:.93rem;opacity:.95;line-height:1.65;">{st.session_state.summary}</p>'
            f'</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ai-box"><strong style="color:#123C69;">🔍 Factores determinantes</strong>'
            f'<br/>{st.session_state.explicacion}</div>', unsafe_allow_html=True)
        if st.button("🔁 Regenerar análisis"):
            st.session_state.profile = ""
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    cb, cs, cn = st.columns([1, 1, 1])
    with cb:
        if st.button("← Volver"): st.session_state.step = 1; st.rerun()
    with cs:
        if st.button("Omitir →"): st.session_state.step = 3; st.rerun()
    with cn:
        can = (st.session_state.b_emp and st.session_state.b_fac) or len(st.session_state.risk) >= 5
        if st.button("Ver instrumentos →", disabled=not can):
            if not st.session_state.scores:
                with st.spinner("Calculando compatibilidad..."):
                    st.session_state.scores = generar_compatibilidades()

            st.session_state.step = 3; st.rerun()

def step3():
    compat = st.session_state.scores
    st.markdown(
        f'<div class="pyme-card"><h2>📊 Instrumentos & Mercado</h2>'
        f'<p class="sub">Recomendaciones para tu perfil <strong>{st.session_state.profile or "—"}</strong>.</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ─────────────────────────────────────────────────────────────
    # CONTENIDO POR COMPATIBILIDAD
    # ─────────────────────────────────────────────────────────────

    CONTENIDO = {
        
        "dolar" : {
            "titulo": "Dólar",
            "desc" : (
                "El dólar es una de las opciones más populares para protegerse contra la inflación y la devaluación en Argentina. "
            ), 
            "items": [
                {
                    "nombre" : "Dólar MEP",
                    "desc" : "Permite comprar dólares de forma legal a través de la bolsa local.",
                    "compat": compat.get("dolar", 0)
                }
            ]
        }, 
        
        "renta_fija": {
            "titulo": "Renta Fija", 
            "desc" : (
                "La renta fija es una categoría de inversión que se caracteriza por ofrecer pagos periódicos de intereses y la devolución del capital al vencimiento. "
                "Es ideal para inversores que buscan estabilidad y menor riesgo, aunque con rendimientos generalmente más bajos que la renta variable."
            ), 
            "items": [
                {
                    "nombre": "Plazos fijos",
                    "desc": "Ofrecen estabilidad y una renta previsible con bajo nivel de riesgo.",
                    "compat": compat.get("plazo_fijo", 0)
                },
                {
                    "nombre": "Caución",
                    "desc": "Permite obtener financiamiento a corto plazo con garantía de activos.",
                    "compat": compat.get("caucion", 0)
                },
                {
                    "nombre": "Letras del Tesoro",
                    "desc": "Instrumentos emitidos por el Estado con vencimientos a corto plazo y rendimientos fijos.",
                    "compat": compat.get("letras", 0)
                },
                {
                    "nombre": "LECAPs",
                    "desc": "Instrumentos de corto plazo emitidos por el Estado con rendimientos moderados y relativa seguridad.",
                    "compat": compat.get("lecap", 0)
                },
                {
                    "nombre": "Bonos",
                    "desc": "Permiten generar ingresos mediante intereses periódicos con menor volatilidad.",
                    "compat": compat.get("bonos", 0)
                },
                {
                    "nombre": "Obligaciones Negociables (ONs)",
                    "desc": "Brindan rendimientos estables respaldados por compañías con buena situación financiera.",
                    "compat": compat.get("on", 0)
                },
            ]
        },
        
        "renta_variable": {
            "titulo": "Renta Variable",
            "desc": (
                "La renta variable incluye inversiones en acciones y otros instrumentos que no garantizan un retorno fijo."
            ), 
            "items": [
                {
                    "nombre": "Acciones", 
                    "desc": "Invertir en acciones de empresas puede ofrecer altos rendimientos, pero con mayor volatilidad y riesgo.",
                    "compat": compat.get("acciones", 0)
                }
            ]
        },
        
        "fondos_comunes":{
            "titulo": "Fondos Comunes de Inversión",
            "desc": (
                "Los fondos comunes de inversión (FCI) son vehículos que agrupan el dinero de varios inversores para invertir en una cartera diversificada de activos. "
                "Pueden ser de renta fija, renta variable o mixtos, dependiendo del perfil de riesgo y los objetivos de inversión."
            ),
            "items": [
                {
                    "nombre": "FCI de renta fija",
                    "desc": "Diversifican el capital reduciendo el riesgo general de la inversión.",
                    "compat": compat.get("fci_rf", 0)
                },
                {
                    "nombre": "FCI de renta variable",
                    "desc": "Ofrecen potencial de crecimiento a largo plazo, aunque con mayor volatilidad.",
                    "compat": compat.get("fci_rv", 0)
                },
                {
                    "nombre": "FCI mixtos",
                    "desc": "Combinan renta fija y variable para equilibrar riesgo y retorno.",
                    "compat": compat.get("fci_mixto", 0)
                }
            ]
        },
        
        "derivados":{
            "titulo": "Derivados",
            "desc": (
                "Los derivados son instrumentos financieros cuyo valor se basa en el precio de otro activo subyacente. "
                "Incluyen opciones, futuros y swaps, y suelen ser utilizados para cobertura o especulación. "
                "Requieren un conocimiento avanzado del mercado y no son recomendados para todos los perfiles de inversor."
            ),
            "items": [
                {
                    "nombre": "Opciones",
                    "desc": "Permiten comprar o vender un activo a un precio determinado en el futuro, útil para cobertura o especulación.",
                    "compat": compat.get("opciones", 0)
                },
                {
                    "nombre": "Futuros",
                    "desc": "Contratos que obligan a comprar o vender un activo en una fecha futura a un precio acordado, usados para cobertura o especulación.",
                    "compat": compat.get("futuros", 0)
                },
                {
                    "nombre": "Swaps de tasas",
                    "desc": "Permiten reducir riesgos asociados a cambios en las tasas de interés.",
                    "compat": compat.get("swap_tasas", 0)
                },
                {
                    "nombre": "Swaps de commodities",
                    "desc": "Se utilizan para gestionar riesgos relacionados con precios de materias primas.",
                    "compat": compat.get("swap_commodities", 0)
                },
                {
                    "nombre": "Swaps de moneda",
                    "desc": "Se utilizan para disminuir riesgos cambiarios.",
                    "compat": compat.get("swap_monedas", 0)
                }
            ]
        }
    }

    # ─────────────────────────────────────────────────────────────
    # HEADER PERFIL
    # ─────────────────────────────────────────────────────────────

    #color_perfil = RISK_COLORS.get(perfil, "#F39C12")

    #st.markdown(
        #f'<div style="background:{color_perfil};color:white;border-radius:12px;padding:1rem 1.25rem;margin-bottom:1.2rem;">'
        #f'<div style="font-size:1rem;font-weight:700;margin-bottom:.4rem;">{CONTENIDO["intro"]["titulo"]}</div>'
        #f'<div style="font-size:.88rem;line-height:1.5;">{CONTENIDO["intro"]["texto"]}</div>'
        #f'</div>',
        #unsafe_allow_html=True
    #)

    # ─────────────────────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────────────────────

    def render_seccion(data):

        st.markdown(
            f'<div style="margin-bottom:1rem;">'
            f'<div style="font-size:1.05rem;font-weight:700;color:#123C69;margin-bottom:.35rem;">{data["titulo"]}</div>'
            f'<div style="font-size:.85rem;color:#7F8C8D;margin-bottom:1rem;line-height:1.5;">{data["desc"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        for item in data["items"]:
            score = item["compat"]
            if score>=80:
                color="#2ECC71"
            elif score>=60:
                color="#27AE60"
            elif score>=40:
                color="#F39C12"
            elif score>=20:
                color="#E67E22"
            else:
                color="#E74C3C"
    
            st.markdown(
                f'<div style="background:#F8FAFC;border-radius:10px;padding:.9rem 1rem;margin:.5rem 0;border:1px solid #E0E6ED;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:.45rem;">'
                f'<span style="font-weight:700;color:#123C69;font-size:.92rem;">• {item["nombre"]}</span>'
                f'<span style="background:{color};color:white;padding:4px 10px;border-radius:20px;font-size:.72rem;font-weight:700;">{item["compat"]}</span>'
                f'</div>'
                f'<div style="font-size:.83rem;color:#555;line-height:1.5;">{item["desc"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # ─────────────────────────────────────────────────────────────
    # SECCIONES
    # ─────────────────────────────────────────────────────────────

    st.markdown(
        '<h3 style="color:#123C69;"> 💸 Dólar</h3>',
        unsafe_allow_html=True
    )
    render_seccion(CONTENIDO["dolar"])

    st.markdown(
        '<hr style="margin:1.2rem 0;">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<h3 style="color:#123C69;">📘 Renta Fija</h3>',
        unsafe_allow_html=True
    )
    render_seccion(CONTENIDO["renta_fija"])

    st.markdown(
        '<hr style="margin:1.2rem 0;">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<h3 style="color:#123C69;">📗 Renta Variable</h3>',
        unsafe_allow_html=True
    )
    render_seccion(CONTENIDO["renta_variable"])

    # =====================================================
    # ACCIONES RECOMENDADAS SEGÚN PERFIL
    # =====================================================

    perfil = st.session_state.profile or "Riesgo Medio"

    if perfil == "Riesgo Bajo":

        acciones_demo = {
            "KO": {
                "nombre": "Coca-Cola",
                "desc": "Empresa líder mundial en bebidas."
            },
            "MSFT": {
                "nombre": "Microsoft",
                "desc": "Gigante tecnológico especializado en software y nube."
            },
            "AAPL": {
                "nombre": "Apple",
                "desc": "Fabricante del iPhone y uno de los negocios más rentables del mundo."
            },
            "JNJ": {
                "nombre": "Johnson & Johnson",
                "desc": "Multinacional de salud y productos farmacéuticos."
            }
        }

    elif perfil == "Riesgo Medio":

        acciones_demo = {
            "AMZN": {
                "nombre": "Amazon",
                "desc": "Líder global en e-commerce y servicios cloud."
            },
            "V": {
                "nombre": "Visa",
                "desc": "Principal procesadora de pagos electrónicos."
            },
            "GOOGL": {
                "nombre": "Google",
                "desc": "Empresa matriz de Google y YouTube."
            },
            "MELI": {
                "nombre": "Mercado Libre",
                "desc": "Principal plataforma de e-commerce de Latinoamérica."
            }
        }

    else:

        acciones_demo = {
            "TSLA": {
                "nombre": "Tesla",
                "desc": "Fabricante de vehículos eléctricos liderado por Elon Musk."
            },
            "NVDA": {
                "nombre": "Nvidia",
                "desc": "Líder mundial en chips para inteligencia artificial."
            },
            "META": {
                "nombre": "Meta",
                "desc": "Empresa propietaria de Facebook, Instagram y WhatsApp."
            },
            "PLTR": {
                "nombre": "Palantir",
                "desc": "Empresa especializada en análisis avanzado de datos e IA."
            }
        }

    with st.expander("📈 Ver ejemplos de acciones recomendadas para mi perfil"):

        st.info(
            f"Estas acciones son ejemplos educativos alineados con un perfil {perfil.lower()}."
        )

        for ticker, accion in acciones_demo.items():

            with st.expander(f"{accion['nombre']} ({ticker})"):

                try:

                    datos = obtener_accion(ticker)

                    st.write(accion["desc"])

                    variacion = (
                        (datos["hist"]["Close"].iloc[-1] /
                        datos["hist"]["Close"].iloc[0] - 1)
                        * 100
                    )
                    st.metric(
                        "Rendimiento 5 años",
                        f"{variacion:.2f}%"
                    )
                    
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Precio actual",
                            f"USD {datos['precio']:,.2f}"
                        )

                    with col2:
                        st.metric(
                            "Rendimiento 5 años",
                            f"{variacion:.2f}%"
                        )

                    fig = grafico_velas(
                        datos["hist"],
                        ticker
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                except Exception:

                    st.warning(
                        f"No se pudieron obtener datos para {ticker}"
                    )

    st.markdown(
        '<hr style="margin:1.2rem 0;">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<h3 style="color:#123C69;"> 💰 Fondos Comunes de Inversion</h3>',
        unsafe_allow_html=True
    )
    render_seccion(CONTENIDO["fondos_comunes"])

    st.markdown(
        '<hr style="margin:1.2rem 0;">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<h3 style="color:#123C69;">📙 Derivados</h3>',
        unsafe_allow_html=True
    )
    render_seccion(CONTENIDO["derivados"])

    # ─────────────────────────────────────────────────────────────
    # BOTONES
    # ─────────────────────────────────────────────────────────────

    cb, _ = st.columns([1, 3])

    with cb:
        if st.button("← Volver"):
            st.session_state.step = 2
            st.rerun()

    if st.button("🔄 Nuevo diagnóstico"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    init()
    nombre=st.session_state.u_nombre
    greeting=f" · Hola, {nombre} 👋" if nombre else ""
    
    st.markdown(
        f'<div style="background:#123C69;color:white;padding:14px 22px;border-radius:12px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<div style="font-size:28px;">🏦</div>'
        f'<div style="font-size:22px;font-weight:800;">IN ME - INvertí como pyME</div>'
        f'</div>'
        f'<div style="font-size:14px;opacity:.9;">{greeting}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    stepper(st.session_state.step)
    s=st.session_state.step
    if s==1: step1()
    elif s==2: step2()
    elif s==3: step3()
    
    # ── Bot flotante ──────────────────────────────────────────────────────
    if "bot_open" not in st.session_state:
        st.session_state.bot_open = False
    if "bot_chat" not in st.session_state:
        st.session_state.bot_chat = []

    # Botón circular flotante (simulado abajo a la derecha con columnas)
    st.markdown("""
    <div style="position:fixed;bottom:28px;right:28px;z-index:9999;">
      <div id="floatBotAnchor"></div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 🤖 Consultor financiero IA")
        st.caption(f"Perfil activo: **{st.session_state.profile or 'Sin perfil aún'}**")
        st.markdown("---")

        for m in st.session_state.bot_chat:
            with st.chat_message(m["role"]):
                st.write(m["content"])

        inp = st.chat_input("Preguntá sobre inversiones...", key="bot_input")
        if inp:
            st.session_state.bot_chat.append({"role": "user", "content": inp})
            with st.chat_message("user"):
                st.write(inp)
            with st.chat_message("assistant"):
                with st.spinner(""):
                    sys_bot = (
                        f"Sos asesor financiero experto en PyMes argentinas. "
                        f"El usuario tiene perfil {st.session_state.profile or 'Sin perfil aún'}. "
                        "Respondé breve y claro en español rioplatense. Máx 4 oraciones."
                    )
                    hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.bot_chat]
                    reply = call_groq(hist, sys_bot)
                    st.write(reply)
                    st.session_state.bot_chat.append({"role": "assistant", "content": reply})

if __name__=="__main__":
    main()
