import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import time
import glob
from gtts import gTTS
from googletrans import Translator

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO (DARK MODE AUDIO)
# ==========================================
st.set_page_config(
    page_title="Vocal-Synth AV",
    page_icon="🎙️",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Mono', monospace;
        background-color: #0a0a1a !important;
        color: #e0e0ff !important;
    }
    
    /* Panel lateral oscuro con acentos morados */
    [data-testid="stSidebar"] {
        background-color: #11112b !important;
        border-right: 1px solid #2a2a5a;
    }
    
    h1, h2, h3 { color: #b366ff !important; }
    
    /* Botón de grabación estilo Sampler */
    .stButton > button {
        background: #1a1a3a !important;
        color: #b366ff !important;
        border: 2px solid #b366ff !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: #b366ff !important;
        color: #000000 !important;
        box-shadow: 0 0 15px rgba(179, 102, 255, 0.6);
    }
    
    .audio-card {
        background: #11112b;
        border: 1px solid #333366;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        border-left: 5px solid #b366ff;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DICCIONARIOS DE IDIOMAS
# ==========================================
IDIOMAS = {
    "Inglés": "en", "Español": "es", "Bengali": "bn", 
    "Coreano": "ko", "Mandarín": "zh-cn", "Japonés": "ja", 
    "Alemán": "de", "Francés": "fr", "Ruso": "ru", "Italiano": "it"
}

ACENTOS_INGLES = {
    "Global (Por defecto)": "com",
    "Estados Unidos": "com",
    "Reino Unido": "co.uk",
    "Australia": "com.au",
    "Canadá": "ca",
    "Irlanda": "ie",
    "Sudáfrica": "co.za"
}

# ==========================================
# 3. INTERFAZ: SIDEBAR (PARÁMETROS DEL SYNTH)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3293/3293043.png", width=100) # Icono de onda sonora
    st.title("🎛️ Parámetros del Sample")
    st.caption("Configura la síntesis de voz antes de grabar.")
    
    in_lang_name = st.selectbox("🗣️ Tu idioma (Entrada):", list(IDIOMAS.keys()), index=1)
    out_lang_name = st.selectbox("🤖 Idioma del Sample (Salida):", list(IDIOMAS.keys()), index=5) # Japonés por defecto para el toque Cyberpunk
    
    # Solo mostrar acentos si la salida es Inglés, Español o Francés (gTTS soporta TLDs para estos)
    tld = "com"
    if out_lang_name == "Inglés":
        accent_name = st.selectbox("🌍 Acento / Región:", list(ACENTOS_INGLES.keys()))
        tld = ACENTOS_INGLES[accent_name]
    elif out_lang_name == "Español":
        tld = st.selectbox("🌍 Acento / Región:", ["com.mx (México)", "es (España)"]).split(" ")[0]

    input_language = IDIOMAS[in_lang_name]
    output_language = IDIOMAS[out_lang_name]

# ==========================================
# 4. ÁREA PRINCIPAL: CAPTURA DE AUDIO
# ==========================================
st.markdown("<h1>🎙️ Vocal-Synth AV</h1>", unsafe_allow_html=True)
st.markdown("Generador de *samples* vocales mediante traducción neuronal y *Text-to-Speech*. Ideal para **diálogos en Unity**, texturas en **TouchDesigner** o pistas musicales.")

st.write("### 1. Graba tu mensaje")
st.info(f"Haz clic en el botón de abajo. Habla en **{in_lang_name}** y espera un segundo a que el sistema procese el texto.")

# Botón de grabación usando JS/Bokeh
stt_button = Button(label="🔴 INICIAR GRABACIÓN (Micrófono)", width=300, height=50)
stt_button.js_on_event("button_click", CustomJS(code=f"""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = '{input_language}'; 

    recognition.onresult = function (e) {{
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {{
            if (e.results[i].isFinal) {{
                value += e.results[i][0].transcript;
            }}
        }}
        if ( value != "") {{
            document.dispatchEvent(new CustomEvent("GET_TEXT", {{detail: value}}));
        }}
    }}
    recognition.start();
"""))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# ==========================================
# 5. PROCESAMIENTO Y SÍNTESIS (TTS)
# ==========================================
os.makedirs("temp", exist_ok=True) # Crea la carpeta de forma segura

if result and "GET_TEXT" in result:
    texto_original = result.get("GET_TEXT")
    
    st.write("### 2. Procesando Audio...")
    st.write(f"**Reconocido:** *'{texto_original}'*")
    
    translator = Translator()
    
    with st.spinner("Traduciendo y sintetizando ondas de audio..."):
        try:
            # Traducción
            translation = translator.translate(texto_original, src=input_language, dest=output_language)
            trans_text = translation.text
            
            # Text to Speech
            tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
            
            # Nombre de archivo seguro basado en timestamp
            my_file_name = f"sample_vocal_{int(time.time())}"
            file_path = f"temp/{my_file_name}.mp3"
            tts.save(file_path)
            
            # 6. RENDERIZADO DEL RESULTADO
            st.markdown(f"""
            <div class="audio-card">
                <h3 style="margin-top:0;">🔊 Sample Generado con Éxito</h3>
                <p><b>Idioma:</b> {out_lang_name} | <b>Texto Sintetizado:</b> {trans_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Leer audio para reproducir y descargar
            with open(file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
                
            st.audio(audio_bytes, format="audio/mp3")
            
            st.download_button(
                label="💾 Descargar Sample (MP3)",
                data=audio_bytes,
                file_name=f"{my_file_name}.mp3",
                mime="audio/mp3",
                type="primary"
            )
            
        except Exception as e:
            st.error(f"Error en la síntesis. (¿Tienes googletrans==4.0.0-rc1 instalado?): {e}")

# Limpieza automática de archivos viejos (Gestión de memoria)
def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                os.remove(f)

remove_files(1) # Borra archivos de más de 1 día para no saturar el servidor en la nube
