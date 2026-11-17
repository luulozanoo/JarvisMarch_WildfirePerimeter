#########################
## IMPORTAR LIBRERÍAS
#########################

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
DISTRIBUCIONES = [
    "Viento (Direccional)",
    "Múltiples Focos",
    "Frente de Fuego",
    "Gaussiana (Centro)",
    "Anillo",
    "Uniforme",
]

def generar_puntos(num, distribucion):
    semillas = []
    if distribucion == "Múltiples Focos": #Generamos islas alrededor de ciertos números
        num_focos = random.randint(3, 4)
        semillas = [[random.uniform(0.15, 0.85), random.uniform(0.15, 0.85)]
                    for _ in range(num_focos)]

    p = []
    while len(p) < num:
        if distribucion == "Uniforme": #Generamos puntos aleatorios
            x, y = random.random(), random.random()
        elif distribucion == "Gaussiana (Centro)": #Generamos puntos alrededor del centro
            x, y = random.gauss(0.5, 0.15), random.gauss(0.5, 0.15)
        elif distribucion == "Anillo": #Generamos puntos en forma de anillo, teniendo en cuenta el ángulo y radio del anillo
            angulo = random.uniform(0, 2 * math.pi)
            radio = random.uniform(0.3, 0.5)
            x = 0.5 + radio * math.cos(angulo)
            y = 0.5 + radio * math.sin(angulo)
        elif distribucion == "Viento (Direccional)": #Generamos puntos en una dirección (afectados por el viento)
            x = abs(random.gauss(0.2, 0.25)) #Dirección de la x
            y = random.gauss(0.5, 0.05)
        elif distribucion == "Múltiples Focos": #Generamos tantos focos como semillas generadas
            foco = random.choice(semillas)
            x = random.gauss(foco[0], 0.03) #Generamos puntos alrededor de los focos
            y = random.gauss(foco[1], 0.03)
        elif distribucion == "Frente de Fuego": #Generamos un caso especial que van en diagonal
            x = random.random()
            y = x + random.gauss(0, 0.05)
        else:
            raise ValueError(f"Distribución desconocida: {distribucion}") #Encapsulamos caso desconocido

        if 0 <= x <= 1 and 0 <= y <= 1: #Solo queremos puntos entre 0 y 1, luego los escalaremos a la escala correspondiente en función del rango de incendio
            p.append([x, y])
    return p

#########################
## FUNCIONES DE IMPACTO (Consecuencias)
#########################
def calcular_area_perimetro(CH, rang_incendio): #Ayuda CHAT para más profesionalidad
    area = 0.0
    perimetro = 0.0
    n = len(CH)
    for i in range(n):
        j = (i + 1) % n
        # Convertimos las coordenadas relativas a kilómetros reales
        xi, yi = CH[i][0] * rang_incendio, CH[i][1] * rang_incendio
        xj, yj = CH[j][0] * rang_incendio, CH[j][1] * rang_incendio
        
        # 1. Área: Fórmula de Gauss (Shoelace)
        area += (xi * yj) - (xj * yi)
        
        # 2. Perímetro: Distancia Euclidiana
        perimetro += math.sqrt((xj - xi)**2 + (yj - yi)**2)
        
    area = abs(area) / 2.0
    hectareas = area * 100 # 1 km² = 100 hectáreas
    return hectareas, perimetro

def punto_en_poligono(punto, poligono): #Sirve para saber si los pueblos están o no en peligro
    """Algoritmo de Ray Casting para saber si un punto está dentro de un polígono"""
    x, y = punto
    dentro = False
    j = len(poligono) - 1
    for i in range(len(poligono)):
        xi, yi = poligono[i]
        xj, yj = poligono[j]
        # Tira un "rayo" horizontal y cuenta cuántas aristas cruza
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            dentro = not dentro
        j = i
    return dentro

# Poblaciones estáticas para evaluar las evacuaciones (coordenadas relativas 0-1)
PUEBLOS = [
    {"nombre": "San Pedro", "coords": [0.15, 0.30]},
    {"nombre": "Valleverde", "coords": [0.75, 0.95]},
    {"nombre": "Villa Alta", "coords": [0.50, 0.85]},
    {"nombre": "El Puente", "coords": [0.70, 0.50]}
]

#########################
## IMAGEN DE FONDO
#########################
@st.cache_resource
def cargar_fondo():
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

    pagina = st.selectbox(
        "Páginas disponibles",
        ["🏡 Inicio","🗺️ Escenario", "💥 Algoritmo", "🛠️ Consecuencias", "📈 Evolución", "📊 Análisis"]
    )

    st.divider()

    st.subheader("Parámetros del Algoritmo")
    distribucion = st.selectbox("Distribución de puntos", DISTRIBUCIONES)
    num_puntos = st.slider("Número de puntos a generar", min_value=3, max_value=1000, value=50, help = "Selecciona el número de focos de calor para la simulación")
    rang_incendio = st.slider("Rango en Km del incendio", min_value=1, max_value=10, value=10, help = "Selecciona el tamaño en km del incendio")
    semilla = st.number_input(
        "Semilla (0 = aleatoria)", min_value=0, value=0, step=1,
        help="Con la misma semilla y los mismos parámetros se obtiene siempre el mismo incendio."
    )

    st.divider()
    ejecutar = st.button("🚀 Ejecutar Algoritmo", use_container_width=True, type="primary")
    st.divider()


########################
## BLOQUE A: GENERAR Y GUARDAR
########################
if ejecutar: #Guardamos el caso en memoria
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
    st.markdown("### Tenemos cientos de focos de calor sueltos: ¿cuál es el perímetro del incendio?")
    st.write(
        "La **envolvente convexa** es la solución matemática a este problema. Es el perímetro mínimo que, en nuestro caso, abarca todos los focos de calor. " \
        "Dicha envolvente garantiza que sea lo más pequeño posible y que todos los puntos estén contenidos. "
        "La forma geométrica que adopta es el perímetro del incendio."
    )
    st.write(
        "Para calcularla usamos la **Marcha de Jarvis**, un método que funciona como si estuviéramos "
        "envolviendo un regalo, buscando siempre el vértice más exterior hasta cerrar el polígono."
    )

    st.info(
        "📌 **Cómo usar el simulador en 3 pasos:**\n"
        "1. **Configura el incendio:** Elige la distribución y el número de focos en el menú lateral.\n"
        "2. **Genera los datos:** Pulsa el botón rojo **🚀 Ejecutar Algoritmo** (¡imprescindible para empezar!).\n"
        "3. **Recorre la historia:** Usa el selector superior para navegar por las secciones en orden."
    )

    with st.expander("📖 ¿Qué encontrarás en cada página?"):
        st.markdown(
            "- **🗺️ Escenario:** El problema real y el origen de los datos.\n"
            "- **💥 Algoritmo:** El paso a paso de la Marcha de Jarvis en acción.\n"
            "- **🛠️ Consecuencias:** La traducción de la geometría a decisiones operativas."
        )

    st.caption(
        "⚠️ **Nota:** Esta aplicación utiliza datos simulados con fines puramente académicos. "
        "Desarrollado por Gonzalo Velasco, Jorge Ois, Lucía Lozano para Geometría Computacional, ICAI."
    )

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

        texto_semilla = f", semilla {semilla_usada}" if semilla_usada != 0 else ""
        st.caption(f"Mostrando: {n_usado} puntos, distribución {dist_usada}, zona de {rang_incendio}x{rang_incendio} km{texto_semilla}")
        st.divider()

        # 2. Textos e Interfaz PRE-MAPA
        if pagina == "🗺️ Escenario":
            st.write(
                "Los puntos rojos que se ven en el mapa representan **focos de calor** reales detectados mediante "
                "imágenes de satélite, drones con cámaras térmicas, sensores terrestres y avisos por GPS."
            )
            st.write(
                "El reto: no se puede acotar terreno si se tienen muchos puntos sueltos sin conexión alguna. "
                "Necesitamos delimitar la zona afectada calculando su **perímetro** (la envolvente convexa) para "
                "estimar el impacto del fuego y gestionar posibles evacuaciones."
            )

            with st.expander("🔍 Tipos de Incendio (Distribuciones)"):
                st.markdown(
                    "| Distribución | Tipo de Incendio simulado |\n"
                    "| :--- | :--- |\n"
                    "| **Uniforme** | Fuego descontrolado y esparcido de forma aleatoria. |\n"
                    "| **Gaussiana** | Incendio estándar concéntrico, muy intenso en el origen. |\n"
                    "| **Anillo** | Incendio donde el centro ya se ha quemado (zona muerta). |\n"
                    "| **Viento** | Incendio direccional empujado fuertemente por rachas de viento. |\n"
                    "| **Múltiples Focos** | Fuego provocado o pavesas que saltan creando focos secundarios. |\n"
                    "| **Frente de Fuego** | Avance en línea apoyado en un río, carretera o cordillera. |"
                )

            st.success(f"📍 **Situación actual:** Estás viendo un incendio simulado con distribución **{dist_usada}** en una zona operativa de **{rang_incendio} × {rang_incendio} km**.")

        elif pagina == "💥 Algoritmo":
            st.write(
                "Para transformar los focos aislados en un perímetro cerrado, el algoritmo actúa como si fuéramos "
                "tensando una cuerda alrededor de la nube de puntos, apoyándonos siempre en los vértices más extremos."
            )
            with st.expander("🛠️ Cómo funciona nuestro código (Paso a paso)"):
                st.markdown(
                    "1. **Punto de anclaje:** Empezamos buscando el foco situado más al sur (el valor mínimo en el eje Y).\n"
                    "2. **Búsqueda polar:** Calculamos el ángulo de todos los demás focos respecto al vértice actual.\n"
                    "3. **El salto:** Elegimos el foco que requiera el menor giro hacia la derecha.\n"
                    "4. **Cierre:** Repetimos el proceso hasta que el siguiente salto nos devuelve al punto de partida.\n\n"
                    "*Nota técnica: Tratamos de forma especial los puntos alineados (misma pendiente) favoreciendo el más lejano, para evitar vértices redundantes en la misma arista.*"
                )
            
            pasos = st.slider("Pasos algoritmo Jarvis", min_value=1, max_value=len(CH), value=1)
            # Definimos estas variables aquí para poder usarlas en el texto dinámico y luego en la gráfica
            x_env_prog = [punto[0]*rang_incendio for punto in CH[:pasos]]
            y_env_prog = [punto[1]*rang_incendio for punto in CH[:pasos]]
            
            st.markdown(f"**Vértice {pasos} de {len(CH)}** — El algoritmo está evaluando el entorno desde las coordenadas `(Este: {x_env_prog[-1]:.2f} km, Norte: {y_env_prog[-1]:.2f} km)`.")

        elif pagina == "🛠️ Consecuencias":
            # Cálculos matemáticos en tiempo real
            hectareas, perimetro_km = calcular_area_perimetro(CH, rang_incendio)
            
            pueblos_afectados = []
            pueblos_salvo = []
            for pueblo in PUEBLOS:
                if punto_en_poligono(pueblo["coords"], CH):
                    pueblos_afectados.append(pueblo)
                else:
                    pueblos_salvo.append(pueblo)

            # Interfaz de la página
            st.write(
                "El algoritmo ha terminado. Ya no tenemos una nube de puntos desordenada, sino una delimitación clara. "
                "El perímetro geométrico nos permite acotar la zona de exclusión y empezar a tomar decisiones."
            )
            
            st.success(
                f"🚨 **Balance de Daños:** El incendio ha calcinado un área estimada de **{hectareas:.1f} hectáreas**, "
                f"contenida en un perímetro de **{perimetro_km:.1f} km**."
            )
            
            # Métricas ampliadas
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔵 Focos Activos", len(p))
            col2.metric("🟢 Vértices", len(CH))
            col3.metric("🔥 Hectáreas", f"{hectareas:.1f} ha")
            col4.metric("🏘️ Evacuaciones", len(pueblos_afectados))


        # 3. CONSTRUCCIÓN DE LA GRÁFICA BASE
        fig = go.Figure()
        x_puntos = [punto[0]*rang_incendio for punto in p]
        y_puntos = [punto[1]*rang_incendio for punto in p]

        fig.add_trace(go.Scatter(
            x=x_puntos, y=y_puntos, mode='markers', name='Focos de calor',
            marker=dict(color="#f42008", size=8, opacity=0.7),
            hovertemplate="Este: %{x:.2f} km<br>Norte: %{y:.2f} km<extra></extra>",
            showlegend=True
        ))

        # Añadir trazados dinámicos según la página
        if pagina == "💥 Algoritmo":
            if pasos == len(CH):
                x_env_prog.append(CH[0][0]*rang_incendio)
                y_env_prog.append(CH[0][1]*rang_incendio)

            fig.add_trace(go.Scatter(
                x=x_env_prog, y=y_env_prog, mode='lines+markers', name='Progreso de Jarvis',
                line=dict(color="#1A9F0B", width=3), marker=dict(color="#1A9F0B", size=10, symbol='diamond'),
                hovertemplate="Vértice Este: %{x:.2f} km<br>Vértice Norte: %{y:.2f} km<extra></extra>"
            ))
            fig.add_trace(go.Scatter(
                x=[x_env_prog[-1]], y=[y_env_prog[-1]], mode='markers', name='Vértice Activo',
                marker=dict(color="#FFD700", size=16, symbol='star', line=dict(color='black', width=2)),
                hoverinfo="skip"
            ))

        elif pagina == "🛠️ Consecuencias":
            # 1. Perímetro con relleno (fill='toself')
            x_env_full = [punto[0]*rang_incendio for punto in CH] + [CH[0][0]*rang_incendio]
            y_env_full = [punto[1]*rang_incendio for punto in CH] + [CH[0][1]*rang_incendio]

            fig.add_trace(go.Scatter(
                x=x_env_full, y=y_env_full, mode='lines+markers', name='Perímetro / Área afectada',
                line=dict(color="#062003", width=3), marker=dict(color="#062003", size=10, symbol='diamond'),
                fill='toself', fillcolor='rgba(255, 69, 0, 0.25)', # Sombreado naranja translúcido
                hovertemplate="Vértice Este: %{x:.2f} km<br>Vértice Norte: %{y:.2f} km<extra></extra>"
            ))
            
            # 2. Dibujar los pueblos
            for pueblo in PUEBLOS:
                afectado = punto_en_poligono(pueblo["coords"], CH)
                color = "#FF0000" if afectado else "#0000FF"
                simbolo = "x-open" if afectado else "pentagon"
                estado = "EVACUAR" if afectado else "A salvo"
                
                fig.add_trace(go.Scatter(
                    x=[pueblo["coords"][0] * rang_incendio], 
                    y=[pueblo["coords"][1] * rang_incendio],
                    mode='markers+text', name=f'{pueblo["nombre"]} ({estado})',
                    text=[pueblo["nombre"]], textposition="top center",
                    marker=dict(color=color, size=14, symbol=simbolo, line=dict(color='white', width=1)),
                    hovertemplate=f"<b>{pueblo['nombre']}</b><br>Estado: {estado}<extra></extra>"
                ))

        # Configuración visual del layout
        margen = rang_incendio * 0.05
        img_fondo = cargar_fondo()
        if img_fondo is not None:
            fig.add_layout_image(dict(
                source=img_fondo, xref="x", yref="y", x=-margen, y=-margen,
                sizex=rang_incendio + 2 * margen, sizey=rang_incendio + 2 * margen,
                xanchor="left", yanchor="bottom", sizing="stretch", opacity=1, layer="below"
            ))

        fig.update_layout(
            height=650, hovermode="closest", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Este-Oeste (km)", showgrid=True, gridcolor='rgba(200,200,200,0.3)', zeroline=False, range=[-margen, rang_incendio + margen], constrain="domain"),
            yaxis=dict(title="Norte-Sur (km)", showgrid=True, gridcolor='rgba(200,200,200,0.3)', zeroline=False, range=[-margen, rang_incendio + margen], constrain="domain", scaleanchor="x", scaleratio=1),
            margin=dict(l=0, r=0, t=30, b=0)
        )

        # 4. RENDERIZADO DEL MAPA
        st.plotly_chart(fig, use_container_width=True)

        # 5. Textos POST-MAPA
        if pagina == "🗺️ Escenario":
            st.info("👉 Esto es lo que ve el equipo de emergencias en el primer minuto: puntos sueltos. Ve a la página **💥 Algoritmo** para ver cómo la matemática construye el perímetro.")
        
        elif pagina == "💥 Algoritmo":
            with st.expander("⏱️ Complejidad y Rendimiento"):
                st.markdown(
                    "El tiempo de ejecución de la Marcha de Jarvis depende tanto del número total de focos ($n$) "
                    "como de los vértices que acaben formando el perímetro final ($h$).\n\n"
                    "- **Complejidad Clásica:** $O(n \cdot h)$\n"
                    "- **Nuestra implementación:** Debido a la forma en que ordenamos los ángulos internamente usando `sorted()` en cada iteración, el coste temporal actual es $O(h \cdot n \log n)$.\n\n"
                    f"⏳ **Tiempo real medido en esta ejecución:** `{tiempo_ms:.2f} milisegundos`."
                )
            st.info("👉 Ahora que tenemos el polígono geométrico, ve a **🛠️ Consecuencias** para traducir esta matemática en decisiones operativas.")
        
        elif pagina == "🛠️ Consecuencias":
            with st.expander("⚠️ Limitaciones de la Envolvente Convexa"):
                st.write("Aunque es excelente para establecer una zona de exclusión rápida, hay que saber interpretar sus límites geométricos frente a un incendio real:")
                st.markdown(
                    "- **Cota Superior Conservadora:** La envolvente siempre asume la forma más exterior. Si el incendio tiene forma de herradura (es cóncavo), el polígono incluirá zonas interiores que no están quemadas, sobreestimando la gravedad.\n"
                    "- **Problema de los Focos Múltiples:** Si hay dos grupos de llamas separados por varios kilómetros, el algoritmo los unirá en un solo polígono gigante, 'quemando' digitalmente el terreno que hay entre medias."
                )
            st.info("✅ **Simulación completada.** Puedes volver al menú lateral, cambiar el tipo de incendio o el número de focos, y pulsar de nuevo 'Ejecutar Algoritmo' para generar un escenario totalmente distinto.")


# Resto de páginas (Placeholders)
elif pagina in ["📈 Evolución", "📊 Análisis"]:
    st.subheader(pagina[2:])
    st.write("Esta sección está en construcción.")