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
def angulo(u, v):
    c = (u[0]*v[0] + u[1]*v[1]) / (math.sqrt(u[0]**2 + u[1]**2) * math.sqrt(v[0]**2 + v[1]**2))
    return math.acos(max(-1, min(1, c)))

def minimoAngular(p, actual, d):
    mejor = None
    mejor_ang = None
    mejor_dist = None
    for q in p:
        if q == actual:
            continue
        v = (q[0]-actual[0], q[1]-actual[1])
        ang = angulo(d, v)
        dist = v[0]**2 + v[1]**2
        if mejor is None or ang < mejor_ang or (ang == mejor_ang and dist > mejor_dist):
            mejor, mejor_ang, mejor_dist = q, ang, dist
    return mejor

def Ymin(p):
    p_select=p[0]
    
    for i in range(len(p)):
        if (p[i][1]==p_select[1] and p[i][0]<p_select[0]) or p[i][1]<p_select[1]:
            p_select=p[i]

    return p_select



def Jarvis(S):
    # Eliminar duplicados exactos conservando orden
    puntos_unicos = []
    for pt in S:
        if not any(abs(pt[0]-u[0]) < 1e-9 and abs(pt[1]-u[1]) < 1e-9 for u in puntos_unicos):
            puntos_unicos.append(pt)
    if len(puntos_unicos) < 3:
        return puntos_unicos

    minimo = Ymin(puntos_unicos)
    envolvente = [minimo]
    i = 1
    max_iter = len(puntos_unicos) + 5
    while i < max_iter:
        if i == 1:
            d = (1, 0)
        else:
            d = (envolvente[i-1][0]-envolvente[i-2][0], envolvente[i-1][1]-envolvente[i-2][1])
        minimo_angular = minimoAngular(puntos_unicos, envolvente[i-1], d)
        if minimo_angular is None or minimo_angular == minimo:
            break
        envolvente.append(minimo_angular)
        i += 1
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

def simular_propagacion(p_inicial, num_turnos, dir_viento_rad, fuerza_viento, tasa_expansion, semilla, rang_incendio):
    """Simula la propagación estocástica del incendio por turnos temporales."""
    rng = random.Random(semilla if semilla != 0 else 42)

    vx_viento = fuerza_viento * math.cos(dir_viento_rad) if dir_viento_rad is not None else 0.0
    vy_viento = fuerza_viento * math.sin(dir_viento_rad) if dir_viento_rad is not None else 0.0

    historial = []

    # Turno 0: Focos iniciales
    puntos_actuales = [list(pt) for pt in p_inicial]
    ch_0 = Jarvis(puntos_actuales)
    ha_0, per_0 = calcular_area_perimetro(ch_0, rang_incendio)
    pueblos_0 = [p["nombre"] for p in PUEBLOS if punto_en_poligono(p["coords"], ch_0)]

    historial.append({
        "turno": 0,
        "focos_acumulados": [list(pt) for pt in puntos_actuales],
        "focos_nuevos": [list(pt) for pt in puntos_actuales],
        "CH": ch_0,
        "hectareas": ha_0,
        "perimetro_km": per_0,
        "nuevas_hectareas": ha_0,
        "pueblos_afectados": pueblos_0
    })

    factor_hijos = 1 if tasa_expansion == "Lenta" else (2 if tasa_expansion == "Moderada" else 3)

    for t in range(1, num_turnos + 1):
        frentes = historial[-1]["CH"] if len(historial[-1]["CH"]) > 0 else puntos_actuales
        otros = historial[-1]["focos_acumulados"]

        # Priorizamos propagación desde el perímetro (frente de fuego)
        candidatos = frentes + (rng.sample(otros, min(len(otros), max(3, len(frentes)))) if otros else [])
        nuevos_de_este_turno = []

        for pt in candidatos:
            num_hijos = rng.randint(1, factor_hijos)
            for _ in range(num_hijos):
                # Dispersión aleatoria radial con deriva de viento
                dist = rng.uniform(0.015, 0.045)
                ang = rng.uniform(0, 2 * math.pi)
                dx = dist * math.cos(ang) + vx_viento * 0.03
                dy = dist * math.sin(ang) + vy_viento * 0.03

                # Salto de pavesa (foco secundario arrojado por el viento)
                if rng.random() < 0.15 and fuerza_viento > 0:
                    dx += vx_viento * rng.uniform(0.04, 0.09)
                    dy += vy_viento * rng.uniform(0.04, 0.09)

                nx = max(0.0, min(1.0, pt[0] + dx))
                ny = max(0.0, min(1.0, pt[1] + dy))
                nuevos_de_este_turno.append([round(nx, 4), round(ny, 4)])

        puntos_actuales.extend(nuevos_de_este_turno)
        ch_t = Jarvis(puntos_actuales)
        ha_t, per_t = calcular_area_perimetro(ch_t, rang_incendio)
        delta_ha = max(0.0, ha_t - historial[-1]["hectareas"])
        pueblos_t = [p["nombre"] for p in PUEBLOS if punto_en_poligono(p["coords"], ch_t)]

        historial.append({
            "turno": t,
            "focos_acumulados": [list(pt) for pt in puntos_actuales],
            "focos_nuevos": nuevos_de_este_turno,
            "CH": ch_t,
            "hectareas": ha_t,
            "perimetro_km": per_t,
            "nuevas_hectareas": delta_ha,
            "pueblos_afectados": pueblos_t
        })

    return historial

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
        ["🏡 Inicio","🗺️ Escenario", "💥 Algoritmo", "🛠️ Consecuencias", "📈 Evolución"]
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


# Resto de páginas
elif pagina == "📈 Evolución":
    if "p" not in st.session_state:
        st.info("👈 Configura los parámetros en el menú lateral y haz clic en '🚀 Ejecutar Algoritmo' para empezar la simulación.")
    else:
        # Recuperar variables comunes de la sesión
        p = st.session_state["p"]
        dist_usada, n_usado = st.session_state["params"]
        rang_incendio = st.session_state["rango_incendio"]
        semilla_usada = st.session_state["semilla"]

        st.markdown("### 📈 Propagación Dinámica del Incendio (Evolución Temporal)")
        st.write(
            "En un incendio real, el avance del fuego es un fenómeno **dinámico y estocástico**. "
            "A medida que pasan las horas (turnos), los focos perimetrales activos generan nuevos frentes de llama "
            "y las pavesas arrastradas por el viento provocan saltos de fuego a favor de la corriente. "
            "En esta sección puedes simular cómo la **envolvente convexa de Jarvis** evoluciona y se expande turno a turno."
        )

        with st.expander("⚙️ Parámetros de Propagación del Viento y Terreno", expanded=True):
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                dir_viento_opciones = {
                    "Sin viento (Calma)": None,
                    "Noreste ↗ (45°)": math.pi / 4,
                    "Norte ↑ (90°)": math.pi / 2,
                    "Noroeste ↖ (135°)": 3 * math.pi / 4,
                    "Oeste ← (180°)": math.pi,
                    "Suroeste ↙ (225°)": -3 * math.pi / 4,
                    "Sur ↓ (270°)": -math.pi / 2,
                    "Sureste ↘ (315°)": -math.pi / 4,
                    "Este → (0°)": 0.0,
                }
                dir_viento_label = st.selectbox("Dirección del Viento", list(dir_viento_opciones.keys()), index=1)
                dir_viento_rad = dir_viento_opciones[dir_viento_label]

            with col_v2:
                fuerza_viento_opciones = {
                    "Calma (0 km/h)": 0.0,
                    "Brisa moderada (15 km/h)": 0.8,
                    "Viento fuerte (35 km/h)": 1.6,
                    "Rachas extremas (60 km/h)": 2.5
                }
                fuerza_viento_label = st.selectbox("Intensidad del Viento", list(fuerza_viento_opciones.keys()), index=2)
                fuerza_viento_val = fuerza_viento_opciones[fuerza_viento_label]

            with col_v3:
                num_turnos = st.slider("Horas / Turnos a simular", min_value=2, max_value=8, value=5)

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                tasa_exp = st.select_slider("Tasa de propagación del frente", options=["Lenta", "Moderada", "Rápida"], value="Moderada")
            with col_sub2:
                origen_sim = st.radio(
                    "Punto de partida de la propagación:",
                    ["Núcleo inicial de ignición (Centro)", "Focos actuales del escenario"],
                    horizontal=True
                )

        # Selección de focos de partida
        if origen_sim == "Núcleo inicial de ignición (Centro)":
            cx = sum(pt[0] for pt in p) / len(p)
            cy = sum(pt[1] for pt in p) / len(p)
            p_ordenados = sorted(p, key=lambda pt: (pt[0]-cx)**2 + (pt[1]-cy)**2)
            p_inicio_sim = p_ordenados[:max(4, min(8, len(p)))]
        else:
            p_inicio_sim = p[:min(len(p), 40)]

        # Simular propagación temporal
        semilla_sim = (semilla_usada + 101) if semilla_usada != 0 else 42
        historial_sim = simular_propagacion(
            p_inicio_sim,
            num_turnos,
            dir_viento_rad,
            fuerza_viento_val,
            tasa_exp,
            semilla_sim,
            rang_incendio
        )

        st.divider()

        # Selector interactivo de turno temporal
        turno_sel = st.slider(
            "⏱️ Línea temporal: Selecciona el Turno / Hora para ver la propagación",
            min_value=0,
            max_value=num_turnos,
            value=num_turnos,
            help="Desplaza el slider para visualizar la expansión del fuego paso a paso"
        )

        datos_turno = historial_sim[turno_sel]
        ch_turno = datos_turno["CH"]
        focos_acum = datos_turno["focos_acumulados"]
        focos_nuevos = datos_turno["focos_nuevos"]

        # Evacuaciones y alertas de este turno
        pueblos_evac = datos_turno["pueblos_afectados"]
        pueblos_turno_anterior = historial_sim[turno_sel - 1]["pueblos_afectados"] if turno_sel > 0 else []
        pueblos_nuevos_ahora = [pb for pb in pueblos_evac if pb not in pueblos_turno_anterior]

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("⏱️ Turno Evaluado", f"Hora +{turno_sel}")
        col_m2.metric("🔵 Focos Totales", f"{len(focos_acum)}", f"+{len(focos_nuevos)} nuevos" if turno_sel > 0 else None)
        col_m3.metric("🔥 Área Calcinada", f"{datos_turno['hectareas']:.1f} ha", f"+{datos_turno['nuevas_hectareas']:.1f} ha/h" if turno_sel > 0 else None)
        col_m4.metric(
            "🏘️ Pueblos Evacuados",
            f"{len(pueblos_evac)} de {len(PUEBLOS)}",
            delta=f"🚨 +{len(pueblos_nuevos_ahora)} nuevo(s)" if len(pueblos_nuevos_ahora) > 0 else None,
            delta_color="inverse"
        )

        # Mapa interactivo de la simulación
        fig_sim = go.Figure()

        # 1. Anillos / Isolíneas de perímetros anteriores
        for t_ant in range(turno_sel):
            ch_ant = historial_sim[t_ant]["CH"]
            if len(ch_ant) >= 3:
                x_ant = [pt[0]*rang_incendio for pt in ch_ant] + [ch_ant[0][0]*rang_incendio]
                y_ant = [pt[1]*rang_incendio for pt in ch_ant] + [ch_ant[0][1]*rang_incendio]
                fig_sim.add_trace(go.Scatter(
                    x=x_ant, y=y_ant, mode='lines',
                    line=dict(color="rgba(110, 110, 110, 0.45)", width=1.5, dash='dot'),
                    name=f"Perímetro Turno {t_ant}",
                    hoverinfo="skip",
                    showlegend=(t_ant == 0)
                ))

        # 2. Focos antiguos (brasas previas)
        if turno_sel > 0:
            focos_previos = historial_sim[turno_sel - 1]["focos_acumulados"]
            fig_sim.add_trace(go.Scatter(
                x=[pt[0]*rang_incendio for pt in focos_previos],
                y=[pt[1]*rang_incendio for pt in focos_previos],
                mode='markers', name='Focos previos (brasas)',
                marker=dict(color="#B22222", size=6, opacity=0.45),
                hovertemplate="Foco activo previo<br>Este: %{x:.2f} km<br>Norte: %{y:.2f} km<extra></extra>"
            ))

        # 3. Focos nuevos de este turno
        fig_sim.add_trace(go.Scatter(
            x=[pt[0]*rang_incendio for pt in focos_nuevos],
            y=[pt[1]*rang_incendio for pt in focos_nuevos],
            mode='markers', name=f'Nuevos focos (Turno {turno_sel})',
            marker=dict(color="#FFD700", size=9, line=dict(color="#D50000", width=1.5)),
            hovertemplate="Nuevo foco activo<br>Este: %{x:.2f} km<br>Norte: %{y:.2f} km<extra></extra>"
        ))

        # 4. Envolvente convexa actual de este turno
        if len(ch_turno) >= 3:
            x_env = [pt[0]*rang_incendio for pt in ch_turno] + [ch_turno[0][0]*rang_incendio]
            y_env = [pt[1]*rang_incendio for pt in ch_turno] + [ch_turno[0][1]*rang_incendio]
            fig_sim.add_trace(go.Scatter(
                x=x_env, y=y_env, mode='lines+markers', name=f'Perímetro Jarvis (t={turno_sel})',
                line=dict(color="#062003", width=3),
                marker=dict(color="#062003", size=9, symbol='diamond'),
                fill='toself', fillcolor='rgba(255, 69, 0, 0.28)',
                hovertemplate="Vértice Este: %{x:.2f} km<br>Vértice Norte: %{y:.2f} km<extra></extra>"
            ))

        # 5. Pueblos y estado de evacuación en este turno
        for pueblo in PUEBLOS:
            afectado = punto_en_poligono(pueblo["coords"], ch_turno)
            color = "#FF0000" if afectado else "#0000FF"
            simbolo = "x-open" if afectado else "pentagon"
            estado = "EVACUAR" if afectado else "A salvo"
            fig_sim.add_trace(go.Scatter(
                x=[pueblo["coords"][0] * rang_incendio],
                y=[pueblo["coords"][1] * rang_incendio],
                mode='markers+text', name=f'{pueblo["nombre"]} ({estado})',
                text=[pueblo["nombre"]], textposition="top center",
                marker=dict(color=color, size=14, symbol=simbolo, line=dict(color='white', width=1)),
                hovertemplate=f"<b>{pueblo['nombre']}</b><br>Estado en t={turno_sel}: {estado}<extra></extra>"
            ))

        # Ajuste de layout con imagen de fondo si existe
        margen = rang_incendio * 0.05
        img_fondo = cargar_fondo()
        if img_fondo is not None:
            fig_sim.add_layout_image(dict(
                source=img_fondo, xref="x", yref="y", x=-margen, y=-margen,
                sizex=rang_incendio + 2 * margen, sizey=rang_incendio + 2 * margen,
                xanchor="left", yanchor="bottom", sizing="stretch", opacity=1, layer="below"
            ))

        fig_sim.update_layout(
            height=650, hovermode="closest", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Este-Oeste (km)", showgrid=True, gridcolor='rgba(200,200,200,0.3)', zeroline=False, range=[-margen, rang_incendio + margen], constrain="domain"),
            yaxis=dict(title="Norte-Sur (km)", showgrid=True, gridcolor='rgba(200,200,200,0.3)', zeroline=False, range=[-margen, rang_incendio + margen], constrain="domain", scaleanchor="x", scaleratio=1),
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig_sim, use_container_width=True)

        # Gráficas de análisis temporal
        st.subheader("📊 Métricas de Propagación en el Tiempo")
        col_g1, col_g2 = st.columns(2)

        turnos_x = [h["turno"] for h in historial_sim]
        areas_y = [h["hectareas"] for h in historial_sim]
        deltas_y = [h["nuevas_hectareas"] for h in historial_sim]

        with col_g1:
            fig_area = go.Figure()
            fig_area.add_trace(go.Scatter(
                x=turnos_x, y=areas_y, mode='lines+markers',
                line=dict(color="#FF4500", width=3),
                marker=dict(size=8),
                name="Área acumulada"
            ))
            fig_area.add_trace(go.Scatter(
                x=[turno_sel], y=[areas_y[turno_sel]], mode='markers',
                marker=dict(color="#FFD700", size=14, symbol='star', line=dict(color='black', width=2)),
                name="Turno actual"
            ))
            fig_area.update_layout(
                title="Área Total Afectada (ha) vs Tiempo",
                xaxis_title="Turno (Horas)", yaxis_title="Hectáreas (ha)",
                height=320, margin=dict(l=30, r=20, t=40, b=30)
            )
            st.plotly_chart(fig_area, use_container_width=True)

        with col_g2:
            fig_delta = go.Figure()
            fig_delta.add_trace(go.Bar(
                x=turnos_x[1:] if len(turnos_x) > 1 else [0],
                y=deltas_y[1:] if len(deltas_y) > 1 else [0],
                marker_color="#FF8C00",
                name="Velocidad (ha/turno)"
            ))
            fig_delta.update_layout(
                title="Velocidad de Expansión (ha ganadas por turno)",
                xaxis_title="Turno (Horas)", yaxis_title="Δ Hectáreas / hora",
                height=320, margin=dict(l=30, r=20, t=40, b=30)
            )
            st.plotly_chart(fig_delta, use_container_width=True)

        with st.expander("📖 Interpretación Geométrica de la Propagación"):
            st.markdown(
                "1. **Anisotropía por viento:** Cuando la fuerza del viento es notable, los focos y la envolvente convexa se elongan en la dirección de sotavento, modelando una elipse de propagación.\n"
                "2. **Saltos de pavesas:** Focos que saltan por delante del frente crean nuevos vértices extremos en la envolvente, provocando saltos bruscos en el área contenida.\n"
                "3. **Planificación de emergencias:** Conocer la velocidad de avance ($\Delta \text{Área}/\Delta t$) y la dirección permite anticipar con qué margen de tiempo ordenar la evacuación de las poblaciones en la trayectoria."
            )