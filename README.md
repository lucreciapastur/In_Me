<<<<<<< HEAD
# 🏦 InMe

Aplicación para PyMes argentinas, que permiten infromar sobre instrumentos financieros que cubran el riesgo de variables asociadas a su negocio. 

---

## ✨ Funcionalidades

| Paso | Pantalla | Descripción |
|------|----------|-------------|
| 1 | **Crear cuenta** | Registro con validación de CUIT, edad y provincia/ciudad |
| 2 | **Tu negocio** | Descripción libre + análisis con IA + formulario |
| 3 | **Perfil de riesgo** | formulario para determinar el riesgo como Bajo / Medio / Alto |
| 4 | **Instrumentos** | Índices de compatibilidad para 12 instrumentos financieros + chatbot financiero |
| 5 | **Simulador** | Simulador específico por instrumento + chatbot financiero |

---

## 🚀 Instalación y uso

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd pymeinvierte
```

### 2. Crear y activar el entorno virtual

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (cmd)
python -m venv .venv
.venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la API key de Anthropic

Creá el archivo `.streamlit/secrets.toml` (ya está en `.gitignore`):

```toml
GROQ_API_KEY = "..."
```

Esta se obtiene del link https://console.groq.com/keys 


### 5. Correr la aplicación

```bash
streamlit run app.py
```

Abrí tu navegador en `http://localhost:8501`

---

## 🗂️ Estructura del proyecto

```
pymeinvierte/
├── app.py                   # Aplicación Streamlit principal
├── requirements.txt         # Dependencias Python
├── README.md                # Este archivo
├── .gitignore               # Archivos ignorados por git
└── .streamlit/
    ├── secrets.toml         # 🔑 API key (NO subir a git)
    └── config.toml          # Configuración de Streamlit (opcional)
```

---

## 🛠️ Stack tecnológico

- **[Streamlit](https://streamlit.io/)** — Framework web para apps de datos en Python
- **[Gorq](https://console.groq.com/keys)** — IA para análisis, diagnóstico y chatbot
- **[Plotly](https://plotly.com/)** — Gráficos interactivos
- **[Pandas](https://pandas.pydata.org/)** — Manejo de datos
- **[NumPy](https://numpy.org/)** — Cálculos numéricos

---

## 📋 Variables de entorno / Secrets

| Variable | Descripción |
|----------|-------------|
| `GROQ_API_KEY` | Clave de API de Gorq (obligatoria) |

---

## ⚠️ Disclaimer

Esta aplicación es únicamente con fines educativos e informativos.  
**No constituye asesoramiento financiero, legal ni impositivo.**  
Las tasas y rendimientos mostrados en el simulador son estimaciones ficticias.  
Consultá siempre con un asesor financiero matriculado antes de invertir.

---

## 📄 Licencia

MIT — Libre para uso educativo y comercial.