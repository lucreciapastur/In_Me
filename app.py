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
/* ── Bot flotante ── */
.float-bot-btn {
    position: fixed; bottom: 28px; right: 28px; z-index: 9999;
    width: 60px; height: 60px; border-radius: 50%;
    background: #123C69; border: none; cursor: pointer;
    box-shadow: 0 4px 20px rgba(18,60,105,.35);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem; transition: transform .2s, box-shadow .2s;
}
.float-bot-btn:hover { transform: scale(1.1); box-shadow: 0 6px 28px rgba(18,60,105,.5); }
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
        cuit=st.text_input("CUIT *",value=st.session_state.u_cuit,
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
                    sys = ('Generá índices de compatibilidad del 0 al 100. Devolvé SOLO JSON:\n'
                           '{"dolar":n,"plazo_fijo":n,"caucion":n,"on":n,"bonos":n,"letras":n,'
                           '"lecap":n,"acciones":n,"fci":n,"opciones":n,"futuros":n,"swaps":n}')
                    st.session_state.scores = parse_json(call_groq(
                        [{"role": "user", "content": json.dumps({"perfil": st.session_state.profile, "rubro": st.session_state.b_rubro})}], sys))
            st.session_state.step = 3; st.rerun()

def step3():
    st.markdown(f'<div class="pyme-card"><h2>📊 Instrumentos & Mercado</h2>'
                f'<p class="sub">Recomendaciones para tu perfil <strong>{st.session_state.profile or "—"}</strong>.</p>',
                unsafe_allow_html=True)

    perfil = st.session_state.profile or "Riesgo Medio"

    # ── Contenido estático por perfil ──────────────────────────────────────
    CONTENIDO = {
        "Riesgo Bajo": {
            "intro": "Tenés un perfil conservador (0–33%). Se priorizan inversiones estables, con baja volatilidad y rendimientos previsibles.",
            "renta_fija": {
                "titulo": "Renta Fija — Bonos, ONs, LECAPs y Plazos Fijos",
                "desc": "Las inversiones más recomendadas son aquellas que brindan estabilidad y menor exposición a la volatilidad del mercado.",
                "items": [
                    ("Plazos fijos", "Ofrecen estabilidad y una renta previsible con bajo nivel de riesgo."),
                    ("LECAPs", "Instrumentos de corto plazo emitidos por el Estado con rendimientos moderados y relativa seguridad."),
                    ("Bonos soberanos de bajo riesgo", "Generan ingresos mediante intereses periódicos con menor volatilidad."),
                    ("ONs de empresas sólidas", "Rendimientos estables respaldados por compañías con buena situación financiera."),
                    ("FCI conservadores", "Diversifican el capital reduciendo el riesgo general de la inversión."),
                ]
            },
            "renta_variable": {
                "titulo": "Renta Variable — Acciones y CEDEARs",
                "desc": "Se recomienda invertir en empresas grandes y consolidadas con trayectoria estable y generación constante de ingresos.",
                "items": [
                    ("Coca-Cola (KO)", "Posee demanda constante y estabilidad en sus ingresos a nivel mundial."),
                    ("Johnson & Johnson (JNJ)", "Pertenece al sector salud, considerado defensivo frente a crisis económicas."),
                    ("Procter & Gamble (PG)", "Comercializa productos de consumo básico con ventas sostenidas."),
                    ("Microsoft (MSFT)", "Combina estabilidad financiera con crecimiento constante."),
                    ("Apple (AAPL)", "Mantiene una sólida posición de mercado y alta rentabilidad."),
                ]
            },
            "derivados": {
                "titulo": "Derivados — Opciones, Futuros y Swaps",
                "desc": "No son los más recomendados para perfiles conservadores, pero pueden usarse de manera defensiva como cobertura.",
                "items": [
                    ("Futuros como cobertura", "Ayudan a proteger inversiones frente a variaciones de precios."),
                    ("Swaps de tasas de interés", "Permiten reducir riesgos asociados a cambios en las tasas."),
                    ("Swaps de moneda", "Se utilizan para disminuir riesgos cambiarios."),
                    ("Opciones de cobertura", "Limitan posibles pérdidas en una cartera de inversión."),
                ]
            }
        },
        "Riesgo Medio": {
            "intro": "Tenés un perfil moderado (33–67%). Se busca equilibrio entre seguridad y crecimiento, combinando instrumentos estables con otros de mayor potencial.",
            "renta_fija": {
                "titulo": "Renta Fija — Bonos, ONs, LECAPs y Plazos Fijos",
                "desc": "La renta fija continúa siendo importante, aunque combinada con instrumentos que ofrezcan mayor rendimiento.",
                "items": [
                    ("ONs corporativas", "Ofrecen rendimientos superiores a los plazos fijos con riesgo moderado."),
                    ("Bonos ajustados por inflación", "Protegen el capital frente al aumento de precios."),
                    ("LECAPs", "Permiten obtener liquidez y rendimientos de corto plazo."),
                    ("FCI mixtos", "Combinan renta fija y variable para equilibrar riesgo y retorno."),
                    ("Bonos corporativos", "Brindan ingresos periódicos y posibilidades de crecimiento moderado."),
                ]
            },
            "renta_variable": {
                "titulo": "Renta Variable — Acciones y CEDEARs",
                "desc": "Se buscan empresas con potencial de crecimiento que también mantengan cierta estabilidad.",
                "items": [
                    ("Microsoft (MSFT)", "Presenta crecimiento sostenido y fuerte presencia global."),
                    ("Amazon (AMZN)", "Mantiene expansión constante en comercio electrónico y tecnología."),
                    ("Visa (V)", "Se beneficia del crecimiento de los pagos digitales a nivel mundial."),
                    ("Nvidia (NVDA)", "Posee gran potencial por el avance de la inteligencia artificial."),
                    ("Google (GOOGL)", "Lidera el mercado publicitario y tecnológico."),
                    ("Mercado Libre (MELI)", "Fuerte crecimiento en comercio electrónico y fintech en Latinoamérica."),
                ]
            },
            "derivados": {
                "titulo": "Derivados — Opciones, Futuros y Swaps",
                "desc": "Pueden utilizarse tanto para cobertura como para obtener ganancias adicionales.",
                "items": [
                    ("Opciones financieras", "Permiten aprovechar movimientos del mercado con riesgo controlado."),
                    ("Contratos de futuros", "Sirven tanto para cobertura como para especulación moderada."),
                    ("Swaps de tasas", "Ayudan a administrar riesgos financieros."),
                    ("Swaps de monedas", "Reducen la exposición a variaciones cambiarias."),
                ]
            }
        },
        "Riesgo Alto": {
            "intro": "Tenés un perfil agresivo (67–100%). Buscás mayor rentabilidad aceptando alta volatilidad y posibilidad de pérdidas importantes en el corto plazo.",
            "renta_fija": {
                "titulo": "Renta Fija — Bonos, ONs, LECAPs y Plazos Fijos",
                "desc": "Aunque se prioriza el crecimiento, puede mantenerse una pequeña parte en renta fija para equilibrar riesgos.",
                "items": [
                    ("Bonos de alto rendimiento", "Ofrecen mayores ganancias potenciales a cambio de mayor riesgo."),
                    ("ONs de mayor riesgo", "Permiten acceder a tasas más elevadas."),
                    ("Bonos de mercados emergentes", "Pueden generar retornos altos aunque con más volatilidad."),
                    ("Instrumentos especulativos", "Buscan maximizar la rentabilidad asumiendo riesgos elevados."),
                ]
            },
            "renta_variable": {
                "titulo": "Renta Variable — Acciones y CEDEARs",
                "desc": "Predominan las inversiones en acciones de crecimiento, empresas tecnológicas y sectores innovadores.",
                "items": [
                    ("Tesla (TSLA)", "Gran potencial de crecimiento en tecnología y automóviles eléctricos."),
                    ("Nvidia (NVDA)", "Liderazgo en inteligencia artificial y procesamiento gráfico."),
                    ("Meta (META)", "Apuesta al crecimiento tecnológico y desarrollo de nuevas plataformas digitales."),
                    ("Amazon (AMZN)", "Continúa expandiéndose en múltiples mercados globales."),
                    ("Palantir (PLTR)", "Expectativas de crecimiento en análisis de datos e inteligencia artificial."),
                    ("Mercado Libre (MELI)", "Fuerte crecimiento en comercio electrónico y servicios financieros digitales."),
                ]
            },
            "derivados": {
                "titulo": "Derivados — Opciones, Futuros y Swaps",
                "desc": "Los derivados tienen un rol activo en estrategias de alto riesgo para especular y buscar mayores ganancias.",
                "items": [
                    ("Opciones especulativas", "Permiten obtener ganancias elevadas con alta volatilidad."),
                    ("Futuros financieros", "Se utilizan para especular sobre variaciones de precios."),
                    ("Swaps sobre commodities", "Permiten operar con cambios en precios de materias primas."),
                    ("Swaps de monedas", "Posibilitan aprovechar variaciones en los tipos de cambio."),
                    ("Derivados apalancados", "Incrementan el potencial de rentabilidad, aunque también el riesgo de pérdidas."),
                ]
            }
        }
    }

    contenido = CONTENIDO.get(perfil, CONTENIDO["Riesgo Medio"])

    # ── Calcular scores con IA si no están ────────────────────────────────
    if not st.session_state.scores:
        with st.spinner("Calculando compatibilidad con IA..."):
            sys_scores = (
                'Sos analista financiero para PyMes argentinas. '
                'Según el perfil de riesgo y rubro, generá índices de compatibilidad del 0 al 100 '
                'para cada categoría. Devolvé SOLO JSON válido sin markdown:\n'
                '{"renta_fija":n,"renta_variable":n,"derivados":n,'
                '"plazo_fijo":n,"lecap":n,"bonos":n,"on":n,"fci":n,'
                '"acciones":n,"cedears":n,"opciones":n,"futuros":n,"swaps":n}'
            )
            st.session_state.scores = parse_json(call_groq(
                [{"role": "user", "content": json.dumps({
                    "perfil": perfil,
                    "rubro": st.session_state.b_rubro,
                    "facturacion": st.session_state.b_fac,
                    "mercado": st.session_state.b_merc
                })}], sys_scores))
            
    if not isinstance(st.session_state.scores, dict):
        st.session_state.scores = {}
    
    scores = st.session_state.scores

    def pct_badge(pct):
        color = "#2ECC71" if pct >= 70 else ("#F39C12" if pct >= 40 else "#E74C3C")
        return (f'<span style="background:{color};color:white;padding:3px 12px;'
                f'border-radius:20px;font-size:.78rem;font-weight:700;">{pct}% compatibilidad</span>')

    def render_seccion(key_score, data):
        pct = scores.get(key_score, 50)
        color_sec = "#2ECC71" if pct >= 70 else ("#F39C12" if pct >= 40 else "#E74C3C")

        st.markdown(
            f'<div style="border-left:4px solid {color_sec};padding-left:1rem;margin-bottom:.5rem;">'
            f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
            f'<span style="font-size:1rem;font-weight:700;color:#123C69;">{data["titulo"]}</span>'
            f'{pct_badge(pct)}'
            f'</div>'
            f'<p style="font-size:.85rem;color:#7F8C8D;margin:.4rem 0 .75rem;">{data["desc"]}</p>'
            f'</div>',
            unsafe_allow_html=True)

        for nombre, fundamento in data["items"]:
            st.markdown(
                f'<div style="background:#F8FAFC;border-radius:8px;padding:.6rem 1rem;'
                f'margin:.35rem 0;border:1px solid #E0E6ED;">'
                f'<span style="font-weight:700;color:#123C69;">• {nombre}</span><br/>'
                f'<span style="font-size:.82rem;color:#555;">{fundamento}</span>'
                f'</div>',
                unsafe_allow_html=True)

    # ── Intro perfil ───────────────────────────────────────────────────────
    color_perfil = RISK_COLORS.get(perfil, "#F39C12")
    icon_perfil = {"Riesgo Bajo": "✅", "Riesgo Medio": "ℹ️", "Riesgo Alto": "⚠️"}.get(perfil, "📊")
    st.markdown(
        f'<div style="background:{color_perfil};color:white;border-radius:10px;'
        f'padding:1rem 1.25rem;margin-bottom:1.25rem;">'
        f'<strong>{icon_perfil} {perfil}</strong><br/>'
        f'<span style="font-size:.88rem;opacity:.95;">{contenido["intro"]}</span>'
        f'</div>',
        unsafe_allow_html=True)

    # ── Sección Renta Fija ─────────────────────────────────────────────────
    st.markdown("### 📘 Renta Fija")
    render_seccion("renta_fija", contenido["renta_fija"])

    st.markdown("---")

    # ── Sección Renta Variable ─────────────────────────────────────────────
    st.markdown("### 📗 Renta Variable")
    render_seccion("renta_variable", contenido["renta_variable"])

    st.markdown("---")

    # ── Sección Derivados ──────────────────────────────────────────────────
    st.markdown("### 📙 Derivados")
    render_seccion("derivados", contenido["derivados"])

    st.markdown("---")

    # ── Precios de mercado ─────────────────────────────────────────────────
    st.markdown("### 📈 Elementos del mercado")

    with st.spinner("Cargando mercado en tiempo real..."):
        datos_mercado = obtener_mercado_completo_real()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Acciones (Merval)**")

        acciones = datos_mercado.get("Acciones (Merval)", [])

        for item in acciones[:5]:
            try:
                activo = item.get("activo", "Sin nombre")

                precio_raw = item.get("precio", 0)

                if precio_raw in [None, "", "N/A"]:
                    continue

                precio = float(precio_raw)

                st.metric(
                    activo,
                    f"ARS {precio:,.2f}"
                )

            except Exception as e:
                st.write("Error:", e)

    with col2:
        st.markdown("**CEDEARs**")

        cedears = datos_mercado.get("Cedears populares", [])

        for item in cedears[:5]:
            try:
                activo = item.get("activo", "Sin nombre")

                precio_raw = item.get("precio", 0)

                if precio_raw in [None, "", "N/A"]:
                    continue

                precio = float(precio_raw)

                st.metric(
                    activo,
                    f"USD {precio:,.2f}"
                )

            except Exception as e:
                st.write("Error:", e)

    with col3:
        st.markdown("**Bonos soberanos**")

        bonos = datos_mercado.get("Bonos y ONs", [])

        for item in bonos[:5]:
            try:
                activo = item.get("activo", "Sin nombre")

                precio_raw = item.get("precio", 0)

                if precio_raw in [None, "", "N/A"]:
                    continue

                precio = float(precio_raw)

                st.metric(
                    activo,
                    f"ARS {precio:,.2f}"
                )

            except Exception as e:
                st.write("Error:", e)

    st.markdown("---")

    # ── Brokers y bancos ───────────────────────────────────────────────────
    st.markdown("### 🏦 Brokers y bancos donde operar")

    BROKERS_BANCOS = [
        {"name": "IOL – InvertirOnline",     "url": "https://www.invertironline.com",    "color": "#003087", "tipo": "Broker"},
        {"name": "Balanz",                   "url": "https://balanz.com",                "color": "#E63946", "tipo": "Broker"},
        {"name": "PPI – Portfolio Personal", "url": "https://www.portfoliopersonal.com", "color": "#2563EB", "tipo": "Broker"},
        {"name": "Bull Market Brokers",      "url": "https://bullmarketbrokers.com",     "color": "#16A34A", "tipo": "Broker"},
        {"name": "Banco BBVA Argentina",     "url": "https://www.bbva.com.ar",           "color": "#004481", "tipo": "Banco"},
        {"name": "Banco Galicia",            "url": "https://www.bancogalicia.com",      "color": "#E8000D", "tipo": "Banco"},
        {"name": "Banco Patagonia",          "url": "https://www.bancopatagonia.com.ar", "color": "#005DAA", "tipo": "Banco"},
    ]

    broker_tab, banco_tab = st.tabs(["📊 Brokers", "🏛️ Bancos"])
    with broker_tab:
        for item in [x for x in BROKERS_BANCOS if x["tipo"] == "Broker"]:
            st.markdown(
                f'<a href="{item["url"]}" target="_blank" style="display:inline-block;margin:4px;'
                f'padding:8px 18px;border-radius:8px;border:2px solid {item["color"]};'
                f'color:{item["color"]};text-decoration:none;font-size:.85rem;font-weight:700;">'
                f'🔗 {item["name"]}</a>', unsafe_allow_html=True)
    with banco_tab:
        for item in [x for x in BROKERS_BANCOS if x["tipo"] == "Banco"]:
            st.markdown(
                f'<a href="{item["url"]}" target="_blank" style="display:inline-block;margin:4px;'
                f'padding:8px 18px;border-radius:8px;border:2px solid {item["color"]};'
                f'color:{item["color"]};text-decoration:none;font-size:.85rem;font-weight:700;">'
                f'🏛️ {item["name"]}</a>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    cb, _ = st.columns([1, 3])
    with cb:
        if st.button("← Volver"): st.session_state.step = 2; st.rerun()
    if st.button("🔄 Nuevo diagnóstico"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    init()
    nombre=st.session_state.u_nombre
    greeting=f" · Hola, {nombre} 👋" if nombre else ""
    st.markdown(
        f'<div style="background:#123C69;color:white;padding:.75rem 1.5rem;border-radius:10px;'
        f'margin-bottom:1.5rem;display:flex;align-items:center;gap:.75rem;">'
        f'<span style="font-size:1.4rem;">🏦</span>'
        f'<span style="font-weight:800;font-size:1.2rem;">PyMeInvierte</span>'
        f'<span style="background:#2ECC71;color:white;font-size:.7rem;font-weight:700;'
        f'padding:2px 8px;border-radius:20px;">BETA</span>'
        f'<span style="margin-left:auto;font-size:.85rem;opacity:.8;">{greeting}</span>'
        f'</div>',unsafe_allow_html=True)

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
                    perfil_ctx = st.session_state.profile or "Riesgo Medio"
                    sys_bot = (
                        f"Sos asesor financiero experto en PyMes argentinas. "
                        f"El usuario tiene perfil {perfil_ctx}. "
                        "Respondé breve y claro en español rioplatense. Máx 4 oraciones."
                    )
                    hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.bot_chat]
                    reply = call_groq(hist, sys_bot)
                    st.write(reply)
                    st.session_state.bot_chat.append({"role": "assistant", "content": reply})

if __name__=="__main__":
    main()
