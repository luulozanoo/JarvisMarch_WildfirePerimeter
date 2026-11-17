import os
import streamlit as st
import random
import math
import time
import plotly.graph_objects as go
from PIL import Image

#########################
## CONFIGURACIÓN DE PÁGINA
#########################
st.set_page_config(
    page_title="Proyecto Geo",
    page_icon="🔢",
    layout="wide",
    initial_sidebar_state="expanded"
)

#########################
## FUNCIONES JARVIS 
#########################
def ordenAngular(p,C):
    derecha=[]
    izquierda=[]
    superior=[]
    inferior=[]
    for i in range(len(p)):
        if p[i][0]>C[0]:
            derecha.append(p[i])
        elif p[i][0]<C[0]:
            izquierda.append(p[i])
        elif p[i][1]>C[1]:
            superior.append(p[i])
        elif p[i][1]<C[1]:
            inferior.append(p[i])
    derecha=sorted(derecha,key=lambda x: [(x[1]-C[1])/(x[0]-C[0]),((x[0]-C[0])**2+(x[1]-C[1])**2)**0.5])
    izquierda=sorted(izquierda,key=lambda x: [(x[1]-C[1])/(x[0]-C[0]),((x[0]-C[0])**2+(x[1]-C[1])**2)**0.5])
    superior=sorted(superior)
    inferior=sorted(inferior)
    if C in p:
        return [C]+derecha+superior+izquierda+inferior
    return derecha+superior+izquierda+inferior

def Ymin(p):
    p_select=p[0]
    for i in range(len(p)):
        if p[i][1]<p_select[1]:
            p_select=p[i]
    return p_select

def Jarvis(p):
    C = Ymin(p)
    envolvente = [C]
    anterior = C
    actual = ordenAngular(p, C)[1]
    while actual != C:
        envolvente.append(actual)
        orden = ordenAngular(p, actual)[1:]
        i = orden.index(anterior)
        if i + 1 < len(orden):
            siguiente = orden[i + 1]
        else:
            siguiente = orden[0]

        anterior = actual
        actual = siguiente

    return envolvente

#########################
## GENERADOR DE PUNTOS
#########################
# Primero las distribuciones propias del incendio; al final las genéricas
# (útiles como casos de prueba en la sección de análisis).
DISTRIBUCIONES = [
    "Viento (Direccional)",
    "Múltiples Focos",
    "Frente de Fuego",
    "Gaussiana (Centro)",
    "Anillo",
    "Uniforme",
]

def generar_puntos(num, distribucion):
    """
    Genera 'num' focos dentro del cuadrado unidad [0,1] x [0,1].
    Si un punto cae fuera de la zona se descarta y se sortea otro, para que
    ningún foco (ni vértice del perímetro) se salga del mapa.
    """
    # Las semillas de los grupos se eligen una sola vez, lejos de los bordes
    semillas = []
    if distribucion == "Múltiples Focos":
        num_focos = random.randint(3, 4)
        semillas = [[random.uniform(0.15, 0.85), random.uniform(0.15, 0.85)]
                    for _ in range(num_focos)]

    p = []
    while len(p) < num:
        if distribucion == "Uniforme":
            x, y = random.random(), random.random()

        elif distribucion == "Gaussiana (Centro)":
            x, y = random.gauss(0.5, 0.15), random.gauss(0.5, 0.15)

        elif distribucion == "Anillo":
            angulo = random.uniform(0, 2 * math.pi)
            radio = random.uniform(0.3, 0.5)
            x = 0.5 + radio * math.cos(angulo)
            y = 0.5 + radio * math.sin(angulo)

        elif distribucion == "Viento (Direccional)":
            # Origen a la izquierda, gran dispersión en X (avance del fuego)
            # y poca en Y (flancos)
            x = abs(random.gauss(0.2, 0.25))
            y = random.gauss(0.5, 0.05)

        elif distribucion == "Múltiples Focos":
            foco = random.choice(semillas)
            x = random.gauss(foco[0], 0.03)
            y = random.gauss(foco[1], 0.03)

        elif distribucion == "Frente de Fuego":
            # Línea diagonal (Y = X) con ruido gaussiano
            x = random.random()
            y = x + random.gauss(0, 0.05)

        else:
            raise ValueError(f"Distribución desconocida: {distribucion}")

        if 0 <= x <= 1 and 0 <= y <= 1:
            p.append([x, y])
    return p

#########################
## IMAGEN DE FONDO
#########################
@st.cache_resource
def cargar_fondo():
    """Busca la imagen junto a este archivo y la carga una sola vez."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapa_bosque.jpeg")
    if os.path.exists(ruta):
        return Image.open(ruta).convert("RGB")
    return None

#########################
## CONTENIDO PRINCIPAL Y SIDEBAR
#########################
st.title("Envolvente Convexa: JARVIS MARCH")
st.divider()

with st.sidebar:
    st.title("⚙️ CONTENIDOS")
    st.divider()

    # Selector de página/sección
    pagina = st.selectbox(
        "Información",
        ["🏡 Inicio","🗺️ Escenario", "💥 Algoritmo", "🛠️ Consecuencias", "📈 Evolución", "📊 Análisis"]
    )

    st.divider()

    #########################
    ## PARÁMETROS
    #########################
    st.subheader("Parámetros del Algoritmo")
    distribucion = st.selectbox("Distribución de puntos", DISTRIBUCIONES)
    num_puntos = st.slider("Número de puntos a generar", min_value=3, max_value=1000, value=50)
    rang_incendio = st.slider("Rango en Km del incendio", min_value=1, max_value=10, value=10)
    semilla = st.number_input(
        "Semilla (0 = aleatoria)", min_value=0, value=0, step=1,
        help="Con la misma semilla y los mismos parámetros se obtiene siempre el mismo incendio."
    )

    st.divider()
    ejecutar = st.button("🚀 Ejecutar Algoritmo", use_container_width=True, type="primary")
    st.divider()


########################
## BLOQUE A: GENERAR Y GUARDAR (solo al pulsar el botón)
########################
if ejecutar:
    # Con semilla 0 se vuelve a sortear de forma aleatoria
    random.seed(semilla if semilla != 0 else None)

    p = generar_puntos(num_puntos, distribucion)
    tiempo_inicio = time.time()
    CH = Jarvis(p)
    tiempo_ms = (time.time() - tiempo_inicio) * 1000

    st.session_state["p"] = p
    st.session_state["CH"] = CH
    st.session_state["tiempo_ms"] = tiempo_ms
    st.session_state["params"] = (distribucion, num_puntos)
    st.session_state["rango_incendio"] = rang_incendio
    st.session_state["semilla"] = semilla


#########################
## BLOQUE B Y C: ENRUTAMIENTO Y DIBUJO
#########################
if pagina == "🏡 Inicio":
    st.subheader("INFORMACIÓN")
    st.write("Bienvenido al simulador de la Marcha de Jarvis.")
    # Aquí irá el texto de introducción

elif pagina in ["🗺️ Escenario", "💥 Algoritmo", "🛠️ Consecuencias"]:

    if "p" not in st.session_state:
        st.info("👈 Configura los parámetros en el menú lateral y haz clic en 'Ejecutar Algoritmo' para empezar.")
    else:
        # 1. Recuperar variables comunes
        p = st.session_state["p"]
        CH = st.session_state["CH"]
        dist_usada, n_usado = st.session_state["params"]
        rang_incendio = st.session_state["rango_incendio"]
        tiempo_ms = st.session_state["tiempo_ms"]
        semilla_usada = st.session_state["semilla"]

        # 2. UI específica de cada página antes del mapa
        if pagina == "💥 Algoritmo":
            pasos = st.slider("Pasos algoritmo Jarvis", min_value=1, max_value=len(CH), value=1)
        elif pagina == "🛠️ Consecuencias":
            col1, col2, col3 = st.columns(3)
            col1.metric("🔵 Focos Activos", len(p))
            col2.metric("🟢 Vértices Envolvente", len(CH))
            col3.metric("⏱️ Tiempo de Cálculo", f"{tiempo_ms:.2f} ms")

        texto_semilla = f", semilla {semilla_usada}" if semilla_usada != 0 else ""
        st.caption(f"Mostrando: {n_usado} puntos, distribución {dist_usada}, zona de {rang_incendio}x{rang_incendio} km{texto_semilla}")
        st.divider()

        # 3. Gráfica Base (Común)
        fig = go.Figure()

        x_puntos = [punto[0]*rang_incendio for punto in p]
        y_puntos = [punto[1]*rang_incendio for punto in p]

        fig.add_trace(go.Scatter(
            x=x_puntos, y=y_puntos,
            mode='markers', name='Focos de calor',
            marker=dict(color="#f42008", size=8, opacity=0.7),
            hovertemplate="Este: %{x:.2f} km<br>Norte: %{y:.2f} km<extra></extra>",
            showlegend=True
        ))

        # 4. Trazos dinámicos según página
        if pagina == "💥 Algoritmo":
            x_env = [punto[0]*rang_incendio for punto in CH[:pasos]]
            y_env = [punto[1]*rang_incendio for punto in CH[:pasos]]

            if pasos == len(CH):
                x_env.append(CH[0][0]*rang_incendio)
                y_env.append(CH[0][1]*rang_incendio)

            fig.add_trace(go.Scatter(
                x=x_env, y=y_env, mode='lines+markers', name='Progreso de Jarvis',
                line=dict(color="#1A9F0B", width=3), marker=dict(color="#1A9F0B", size=10, symbol='diamond'),
                hovertemplate="Vértice Este: %{x:.2f} km<br>Vértice Norte: %{y:.2f} km<extra></extra>"
            ))
            fig.add_trace(go.Scatter(
                x=[x_env[-1]], y=[y_env[-1]], mode='markers', name='Vértice Activo',
                marker=dict(color="#FFD700", size=16, symbol='star', line=dict(color='black', width=2)),
                hoverinfo="skip"
            ))

        elif pagina == "🛠️ Consecuencias":
            x_env = [punto[0]*rang_incendio for punto in CH] + [CH[0][0]*rang_incendio]
            y_env = [punto[1]*rang_incendio for punto in CH] + [CH[0][1]*rang_incendio]

            fig.add_trace(go.Scatter(
                x=x_env, y=y_env, mode='lines+markers', name='Perímetro del incendio',
                line=dict(color="#062003", width=3), marker=dict(color="#062003", size=10, symbol='diamond'),
                hovertemplate="Vértice Este: %{x:.2f} km<br>Vértice Norte: %{y:.2f} km<extra></extra>"
            ))

        # 5. Configuración visual unificada (márgenes simétricos, ejes, fondo)
        margen = rang_incendio * 0.05

        img_fondo = cargar_fondo()
        if img_fondo is not None:
            fig.add_layout_image(dict(
                source=img_fondo, xref="x", yref="y",
                x=-margen, y=-margen,
                sizex=rang_incendio + 2 * margen, sizey=rang_incendio + 2 * margen,
                xanchor="left", yanchor="bottom", sizing="stretch", opacity=1, layer="below"
            ))

        fig.update_layout(
            height=650,
            hovermode="closest", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Este-Oeste (km)", showgrid=True, gridcolor='rgba(200,200,200,0.3)', zeroline=False,
                       range=[-margen, rang_incendio + margen], constrain="domain"),
            yaxis=dict(title="Norte-Sur (km)", showgrid=True, gridcolor='rgba(200,200,200,0.3)', zeroline=False,
                       range=[-margen, rang_incendio + margen], constrain="domain", scaleanchor="x", scaleratio=1),
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

# Resto de páginas (Placeholders)
elif pagina in ["📈 Evolución", "📊 Análisis"]:
    st.subheader(pagina[2:])
    st.write("Esta sección está en construcción.")