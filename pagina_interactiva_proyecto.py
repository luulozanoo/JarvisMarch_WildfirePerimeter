#########################
## IMPORTAR LIBRERÍAS
#########################

import os
import math
import time
import random
import streamlit as st
import plotly.graph_objects as go
from PIL import Image

#########################
## CONFIGURACIÓN DE PÁGINA
#########################
st.set_page_config(
    page_title="Proyecto Geo",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

MARGEN_EVACUACION_KM = 1.5

#########################
## FUNCIONES JARVIS
#########################
def angulo(u, v):
    denom = math.sqrt(u[0]**2 + u[1]**2) * math.sqrt(v[0]**2 + v[1]**2)
    if denom == 0:
        return 0.0
    c = (u[0] * v[0] + u[1] * v[1]) / denom
    return math.acos(max(-1.0, min(1.0, c)))


def minimo_angular(p, actual, d):
    mejor = None
    mejor_ang = None
    mejor_dist = None
    for q in p:
        if q == actual:
            continue
        v = (q[0] - actual[0], q[1] - actual[1])
        ang = angulo(d, v)
        dist = v[0]**2 + v[1]**2
        if mejor is None or ang < mejor_ang or (ang == mejor_ang and dist > mejor_dist):
            mejor, mejor_ang, mejor_dist = q, ang, dist
    return mejor


def y_min(p):
    p_select = p[0]
    for punto in p:
        if (punto[1] == p_select[1] and punto[0] < p_select[0]) or punto[1] < p_select[1]:
            p_select = punto
    return p_select


def Jarvis(S):
    # Eliminar duplicados exactos conservando orden
    puntos_unicos = []
    for pt in S:
        if not any(abs(pt[0] - u[0]) < 1e-9 and abs(pt[1] - u[1]) < 1e-9 for u in puntos_unicos):
            puntos_unicos.append(pt)

    if len(puntos_unicos) < 3:
        return puntos_unicos

    minimo = y_min(puntos_unicos)
    envolvente = [minimo]
    i = 1
    max_iter = len(puntos_unicos) + 5

    while i < max_iter:
        if i == 1:
            d = (1, 0)
        else:
            d = (
                envolvente[i - 1][0] - envolvente[i - 2][0],
                envolvente[i - 1][1] - envolvente[i - 2][1],
            )
        siguiente = minimo_angular(puntos_unicos, envolvente[i - 1], d)
        if siguiente is None or siguiente == minimo:
            break
        envolvente.append(siguiente)
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

DESCRIPCIONES_DISTRIBUCION = {
    "Uniforme": "Fuego descontrolado y esparcido de forma aleatoria.",
    "Gaussiana (Centro)": "Incendio estándar concéntrico, muy intenso en el origen.",
    "Anillo": "Incendio donde el centro ya se ha quemado (zona muerta).",
    "Viento (Direccional)": "Incendio direccional empujado fuertemente por rachas de viento.",
    "Múltiples Focos": "Fuego provocado o pavesas que saltan creando focos secundarios.",
    "Frente de Fuego": "Avance en línea apoyado en un río, carretera o cordillera.",
}


def generar_puntos(num, distribucion):
    semillas = []
    if distribucion == "Múltiples Focos":
        num_focos = random.randint(3, 4)
        semillas = [
            [random.uniform(0.15, 0.85), random.uniform(0.15, 0.85)]
            for _ in range(num_focos)
        ]

    p = []
    while len(p) < num:
        if distribucion == "Uniforme":
            x, y = random.random(), random.random()
        elif distribucion == "Gaussiana (Centro)":
            x, y = random.gauss(0.5, 0.15), random.gauss(0.5, 0.15)
        elif distribucion == "Anillo":
            ang = random.uniform(0, 2 * math.pi)
            radio = random.uniform(0.3, 0.5)
            x = 0.5 + radio * math.cos(ang)
            y = 0.5 + radio * math.sin(ang)
        elif distribucion == "Viento (Direccional)":
            x = abs(random.gauss(0.2, 0.25))
            y = random.gauss(0.5, 0.05)
        elif distribucion == "Múltiples Focos":
            foco = random.choice(semillas)
            x = random.gauss(foco[0], 0.03)
            y = random.gauss(foco[1], 0.03)
        elif distribucion == "Frente de Fuego":
            x = random.random()
            y = x + random.gauss(0, 0.05)
        else:
            raise ValueError(f"Distribución desconocida: {distribucion}")

        if 0 <= x <= 1 and 0 <= y <= 1:
            p.append([x, y])

    return p


#########################
## FUNCIONES DE IMPACTO (Consecuencias)
#########################
def calcular_area_perimetro(CH, rang_incendio):
    area = 0.0
    perimetro = 0.0
    n = len(CH)
    for i in range(n):
        j = (i + 1) % n
        xi, yi = CH[i][0] * rang_incendio, CH[i][1] * rang_incendio
        xj, yj = CH[j][0] * rang_incendio, CH[j][1] * rang_incendio

        # Área: Fórmula de Gauss (Shoelace)
        area += (xi * yj) - (xj * yi)
        # Perímetro: Distancia Euclidiana
        perimetro += math.hypot(xj - xi, yj - yi)

    area = abs(area) / 2.0
    hectareas = area * 100  # 1 km² = 100 hectáreas
    return hectareas, perimetro


def punto_en_poligono(punto, poligono):
    """Algoritmo de Ray Casting para saber si un punto está dentro de un polígono."""
    if len(poligono) < 3:
        return False
    x, y = punto
    dentro = False
    j = len(poligono) - 1
    for i in range(len(poligono)):
        xi, yi = poligono[i]
        xj, yj = poligono[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            dentro = not dentro
        j = i
    return dentro


def distancia_punto_segmento(px, py, ax, ay, bx, by):
    """Distancia euclidiana mínima entre un punto P y un segmento AB."""
    abx, aby = bx - ax, by - ay
    long_cuad = abx * abx + aby * aby
    if long_cuad == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / long_cuad))
    cx = ax + t * abx
    cy = ay + t * aby
    return math.hypot(px - cx, py - cy)


def evaluar_evacuacion(punto, poligono, rang_incendio, margen_km=MARGEN_EVACUACION_KM):
    """
    Devuelve (evacuar, dentro, dist_km):
    - evacuar: True si el punto está dentro de la CH o a <= margen_km de cualquier arista.
    - dentro: True si está estrictamente dentro del polígono.
    - dist_km: Distancia mínima en km al perímetro (0.0 si está dentro).
    """
    if not poligono:
        return False, False, float("inf")

    if punto_en_poligono(punto, poligono):
        return True, True, 0.0

    px, py = punto[0] * rang_incendio, punto[1] * rang_incendio
    n = len(poligono)
    if n == 1:
        dist_min = math.hypot(px - poligono[0][0] * rang_incendio, py - poligono[0][1] * rang_incendio)
    else:
        dist_min = min(
            distancia_punto_segmento(
                px, py,
                poligono[i][0] * rang_incendio, poligono[i][1] * rang_incendio,
                poligono[(i + 1) % n][0] * rang_incendio, poligono[(i + 1) % n][1] * rang_incendio,
            )
            for i in range(n)
        )

    return dist_min <= margen_km, False, dist_min


# Poblaciones estáticas para evaluar las evacuaciones (coordenadas relativas 0-1)
PUEBLOS = [
    {"nombre": "San Pedro", "coords": [0.15, 0.30]},
    {"nombre": "Valleverde", "coords": [0.75, 0.95]},
    {"nombre": "Villa Alta", "coords": [0.50, 0.85]},
    {"nombre": "El Puente", "coords": [0.70, 0.50]},
]


def simular_propagacion(p_inicial, num_turnos, dir_viento_rad, fuerza_viento, tasa_expansion, rang_incendio, estado_interno):
    """Simula la propagación estocástica del incendio por turnos temporales."""
    rng = random.Random(estado_interno)

    vx_viento = fuerza_viento * math.cos(dir_viento_rad) if dir_viento_rad is not None else 0.0
    vy_viento = fuerza_viento * math.sin(dir_viento_rad) if dir_viento_rad is not None else 0.0

    historial = []

    # Turno 0: Focos iniciales
    puntos_actuales = [list(pt) for pt in p_inicial]
    ch_0 = Jarvis(puntos_actuales)
    ha_0, per_0 = calcular_area_perimetro(ch_0, rang_incendio)
    pueblos_0 = [
        p["nombre"] for p in PUEBLOS
        if evaluar_evacuacion(p["coords"], ch_0, rang_incendio)[0]
    ]

    historial.append({
        "turno": 0,
        "focos_acumulados": [list(pt) for pt in puntos_actuales],
        "focos_nuevos": [list(pt) for pt in puntos_actuales],
        "CH": ch_0,
        "hectareas": ha_0,
        "perimetro_km": per_0,
        "nuevas_hectareas": ha_0,
        "pueblos_afectados": pueblos_0,
    })

    factor_hijos = 1 if tasa_expansion == "Lenta" else (2 if tasa_expansion == "Moderada" else 3)

    for t in range(1, num_turnos + 1):
        frentes = historial[-1]["CH"] if historial[-1]["CH"] else puntos_actuales
        otros = historial[-1]["focos_acumulados"]

        candidatos = frentes + (rng.sample(otros, min(len(otros), max(3, len(frentes)))) if otros else [])
        nuevos_de_este_turno = []

        for pt in candidatos:
            num_hijos = rng.randint(1, factor_hijos)
            for _ in range(num_hijos):
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
        pueblos_t = [
            p["nombre"] for p in PUEBLOS
            if evaluar_evacuacion(p["coords"], ch_t, rang_incendio)[0]
        ]

        historial.append({
            "turno": t,
            "focos_acumulados": [list(pt) for pt in puntos_actuales],
            "focos_nuevos": nuevos_de_este_turno,
            "CH": ch_t,
            "hectareas": ha_t,
            "perimetro_km": per_t,
            "nuevas_hectareas": delta_ha,
            "pueblos_afectados": pueblos_t,
        })

    return historial


#########################
## IMAGEN DE FONDO Y ESTILO DE MAPAS
#########################
@st.cache_resource
def cargar_fondo():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapa_bosque.jpeg")
    if os.path.exists(ruta):
        return Image.open(ruta).convert("RGB")
    return None


def aplicar_estilo_mapa(fig, rang_incendio):
    margen = rang_incendio * 0.05
    img_fondo = cargar_fondo()
    if img_fondo is not None:
        fig.add_layout_image(dict(
            source=img_fondo, xref="x", yref="y", x=-margen, y=-margen,
            sizex=rang_incendio + 2 * margen, sizey=rang_incendio + 2 * margen,
            xanchor="left", yanchor="bottom", sizing="stretch", opacity=1, layer="below"
        ))

    fig.update_layout(
        height=650,
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            title="Este-Oeste (km)", showgrid=True, gridcolor="rgba(200,200,200,0.3)",
            zeroline=False, range=[-margen, rang_incendio + margen], constrain="domain"
        ),
        yaxis=dict(
            title="Norte-Sur (km)", showgrid=True, gridcolor="rgba(200,200,200,0.3)",
            zeroline=False, range=[-margen, rang_incendio + margen], constrain="domain",
            scaleanchor="x", scaleratio=1
        ),
        margin=dict(l=0, r=0, t=30, b=0),
    )


def agregar_trazas_pueblos(fig, ch, rang_incendio, sufijo_hover=""):
    for pueblo in PUEBLOS:
        evacuar, dentro, dist_km = evaluar_evacuacion(pueblo["coords"], ch, rang_incendio)
        color = "#FF0000" if evacuar else "#0055FF"
        simbolo = "x-open" if evacuar else "pentagon"

        if dentro:
            estado = "EVACUAR (en zona afectada)"
        elif evacuar:
            estado = f"EVACUAR (a {dist_km:.2f} km de la CH)"
        else:
            estado = f"A salvo (a {dist_km:.2f} km)"

        fig.add_trace(go.Scatter(
            x=[pueblo["coords"][0] * rang_incendio],
            y=[pueblo["coords"][1] * rang_incendio],
            mode="markers+text",
            name=f"{pueblo['nombre']} ({'EVACUAR' if evacuar else 'A salvo'})",
            text=[pueblo["nombre"]],
            textposition="top center",
            marker=dict(color=color, size=14, symbol=simbolo, line=dict(color="white", width=1.5)),
            hovertemplate=f"<b>{pueblo['nombre']}</b><br>Estado{sufijo_hover}: {estado}<extra></extra>",
        ))


#########################
## CONTENIDO PRINCIPAL Y SIDEBAR
#########################
st.title("🔥 Envolvente Convexa: JARVIS MARCH")
st.divider()

with st.sidebar:
    st.title("⚙️ CONTENIDOS")
    st.divider()

    pagina = st.selectbox(
        "Páginas disponibles",
        ["🏡 Inicio", "🗺️ Escenario", "💥 Algoritmo", "🛠️ Consecuencias", "📈 Evolución"]
    )

    st.divider()

    st.subheader("Parámetros del Algoritmo")
    distribucion = st.selectbox("Distribución de puntos", DISTRIBUCIONES)
    num_puntos = st.slider(
        "Número de puntos a generar", min_value=3, max_value=1000, value=50,
        help="Selecciona el número de focos de calor para la simulación"
    )
    rang_incendio = st.slider(
        "Rango en km del incendio", min_value=1, max_value=10, value=10,
        help="Selecciona el tamaño en km del área de simulación"
    )

    st.divider()
    ejecutar = st.button("🚀 Ejecutar Algoritmo", use_container_width=True, type="primary")
    st.divider()


########################
## BLOQUE A: GENERAR Y GUARDAR
########################
if ejecutar:
    p = generar_puntos(num_puntos, distribucion)
    tiempo_inicio = time.perf_counter()
    CH = Jarvis(p)
    tiempo_ms = (time.perf_counter() - tiempo_inicio) * 1000

    st.session_state["p"] = p
    st.session_state["CH"] = CH
    st.session_state["tiempo_ms"] = tiempo_ms
    st.session_state["params"] = (distribucion, num_puntos)
    st.session_state["rango_incendio"] = rang_incendio
    st.session_state["estado_sim"] = random.randint(1, 10**6)


#########################
## BLOQUE B Y C: ENRUTAMIENTO Y DIBUJO
#########################
if pagina == "🏡 Inicio":
    st.markdown("### Tenemos cientos de focos de calor sueltos: ¿cuál es el perímetro del incendio?")
    st.write(
        "La **envolvente convexa** es la solución matemática a este problema. Es el perímetro mínimo que abarca "
        "todos los focos de calor, garantizando que todos los puntos queden contenidos dentro del menor polígono convexo posible."
    )
    st.write(
        "Para calcularla usamos la **Marcha de Jarvis**, un método que funciona como si estuviéramos "
        "envolviendo un regalo, buscando siempre el vértice más exterior hasta cerrar el polígono."
    )

    st.info(
        "📌 **Cómo usar el simulador en 3 pasos:**\n"
        "1. **Configura el incendio:** Elige la distribución y el número de focos en el menú lateral.\n"
        "2. **Genera los datos:** Pulsa el botón **🚀 Ejecutar Algoritmo**.\n"
        "3. **Recorre la historia:** Usa el selector superior para navegar por las secciones en orden."
    )

    with st.expander("📖 ¿Qué encontrarás en cada página?"):
        st.markdown(
            "- **🗺️ Escenario:** El problema real y el origen de los datos.\n"
            "- **💥 Algoritmo:** El paso a paso de la Marcha de Jarvis en acción.\n"
            "- **🛠️ Consecuencias:** La traducción de la geometría a decisiones operativas y evacuaciones.\n"
            "- **📈 Evolución:** Simulación temporal de la propagación del fuego con viento y pavesas."
        )

    st.caption(
        "⚠️ **Nota:** Esta aplicación utiliza datos simulados con fines puramente académicos. "
        "Desarrollado por Gonzalo Velasco, Jorge Ois y Lucía Lozano para Geometría Computacional, ICAI."
    )

elif pagina in ["🗺️ Escenario", "💥 Algoritmo", "🛠️ Consecuencias"]:
    # Contenido visible SIEMPRE (antes y después de pulsar "Ejecutar Algoritmo")
    if pagina == "🗺️ Escenario":
        st.write(
            "Los puntos rojos que se ven en el mapa representan **focos de calor** detectados mediante "
            "imágenes de satélite, drones con cámaras térmicas, sensores terrestres y avisos por GPS."
        )
        st.write(
            "El reto: no se puede acotar terreno si se tienen muchos puntos sueltos sin conexión alguna. "
            "Necesitamos delimitar la zona afectada calculando su **perímetro** (la envolvente convexa) para "
            "estimar el impacto del fuego y gestionar posibles evacuaciones."
        )

        with st.expander("🔍 Tipos de Incendio (Distribuciones)", expanded=("p" not in st.session_state)):
            filas = "\n".join(f"| **{k}** | {v} |" for k, v in DESCRIPCIONES_DISTRIBUCION.items())
            st.markdown(f"| Distribución | Tipo de Incendio simulado |\n| :--- | :--- |\n{filas}")

    elif pagina == "💥 Algoritmo":
        st.info(
            f"🔥 **Distribución del fuego seleccionada:** **{distribucion}** — "
            f"{DESCRIPCIONES_DISTRIBUCION[distribucion]}"
        )

    if "p" not in st.session_state:
        st.warning("👈 Configura los parámetros en el menú lateral y haz clic en **🚀 Ejecutar Algoritmo** para visualizar el mapa.")
    else:
        p = st.session_state["p"]
        CH = st.session_state["CH"]
        dist_usada, n_usado = st.session_state["params"]
        rang_usado = st.session_state["rango_incendio"]
        tiempo_ms = st.session_state["tiempo_ms"]

        st.caption(f"Mostrando simulación ejecutada: {n_usado} focos · distribución {dist_usada} · zona de {rang_usado} × {rang_usado} km")
        if pagina == "💥 Algoritmo" and dist_usada != distribucion:
            st.caption("ℹ️ Has cambiado la distribución en el menú lateral. Pulsa **🚀 Ejecutar Algoritmo** si deseas actualizar el mapa.")
        st.divider()

        # Textos e Interfaz PRE-MAPA (solo lo que depende de la simulación)
        if pagina == "🗺️ Escenario":
            st.success(
                f"📍 **Situación actual:** Incendio simulado con distribución **{dist_usada}** "
                f"en una zona operativa de **{rang_usado} × {rang_usado} km**."
            )

        elif pagina == "💥 Algoritmo":
            st.write(
                "Para transformar los focos aislados en un perímetro cerrado, el algoritmo actúa como si fuéramos "
                "tensando una cuerda alrededor de la nube de puntos, apoyándonos siempre en los vértices más extremos."
            )
            with st.expander("🛠️ Cómo funciona nuestro código (Paso a paso)"):
                st.markdown(
                    "1. **Punto de anclaje:** Empezamos buscando el foco situado más al sur (valor mínimo en el eje Y).\n"
                    "2. **Búsqueda polar:** Calculamos el ángulo de todos los demás focos respecto al vértice actual.\n"
                    "3. **El salto:** Elegimos el foco que requiera el menor giro.\n"
                    "4. **Cierre:** Repetimos el proceso hasta que el siguiente salto nos devuelve al punto de partida.\n\n"
                    "*Nota técnica: Los puntos alineados (misma pendiente) se resuelven favoreciendo el más lejano para evitar vértices redundantes.*"
                )

            pasos = st.slider("Pasos algoritmo Jarvis", min_value=1, max_value=len(CH), value=1)
            x_env_prog = [punto[0] * rang_usado for punto in CH[:pasos]]
            y_env_prog = [punto[1] * rang_usado for punto in CH[:pasos]]

            st.markdown(
                f"**Vértice {pasos} de {len(CH)}** — Evaluando desde las coordenadas "
                f"`(Este: {x_env_prog[-1]:.2f} km, Norte: {y_env_prog[-1]:.2f} km)`."
            )

        elif pagina == "🛠️ Consecuencias":
            hectareas, perimetro_km = calcular_area_perimetro(CH, rang_usado)

            pueblos_afectados = [
                pueblo for pueblo in PUEBLOS
                if evaluar_evacuacion(pueblo["coords"], CH, rang_usado)[0]
            ]

            st.write(
                "El algoritmo ha terminado. El perímetro geométrico nos permite acotar la zona de exclusión "
                f"y activar protocolos de evacuación para cualquier población situada dentro de la envolvente "
                f"o a menos de **{MARGEN_EVACUACION_KM} km** de cualquiera de sus lados."
            )

            st.success(
                f"🚨 **Balance de Daños:** Área estimada de **{hectareas:.1f} hectáreas**, "
                f"contenida en un perímetro de **{perimetro_km:.1f} km**."
            )

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔵 Focos Activos", len(p))
            col2.metric("🟢 Vértices CH", len(CH))
            col3.metric("🔥 Hectáreas", f"{hectareas:.1f} ha")
            col4.metric("🏘️ Evacuaciones", f"{len(pueblos_afectados)} / {len(PUEBLOS)}")

        # Construcción de la gráfica base
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[punto[0] * rang_usado for punto in p],
            y=[punto[1] * rang_usado for punto in p],
            mode="markers",
            name="Focos de calor",
            marker=dict(color="#f42008", size=8, opacity=0.7),
            hovertemplate="Este: %{x:.2f} km<br>Norte: %{y:.2f} km<extra></extra>",
        ))

        if pagina == "💥 Algoritmo":
            if pasos == len(CH):
                x_env_prog.append(CH[0][0] * rang_usado)
                y_env_prog.append(CH[0][1] * rang_usado)

            fig.add_trace(go.Scatter(
                x=x_env_prog, y=y_env_prog, mode="lines+markers", name="Progreso de Jarvis",
                line=dict(color="#1A9F0B", width=3),
                marker=dict(color="#1A9F0B", size=10, symbol="diamond"),
                hovertemplate="Vértice Este: %{x:.2f} km<br>Vértice Norte: %{y:.2f} km<extra></extra>"
            ))
            fig.add_trace(go.Scatter(
                x=[x_env_prog[-1]], y=[y_env_prog[-1]], mode="markers", name="Vértice Activo",
                marker=dict(color="#FFD700", size=16, symbol="star", line=dict(color="black", width=2)),
                hoverinfo="skip"
            ))

        elif pagina == "🛠️ Consecuencias":
            x_env_full = [punto[0] * rang_usado for punto in CH] + [CH[0][0] * rang_usado]
            y_env_full = [punto[1] * rang_usado for punto in CH] + [CH[0][1] * rang_usado]

            fig.add_trace(go.Scatter(
                x=x_env_full, y=y_env_full, mode="lines+markers", name="Perímetro / Área afectada",
                line=dict(color="#062003", width=3),
                marker=dict(color="#062003", size=10, symbol="diamond"),
                fill="toself", fillcolor="rgba(255, 69, 0, 0.25)",
                hovertemplate="Vértice Este: %{x:.2f} km<br>Vértice Norte: %{y:.2f} km<extra></extra>"
            ))
            agregar_trazas_pueblos(fig, CH, rang_usado)

        aplicar_estilo_mapa(fig, rang_usado)
        st.plotly_chart(fig, use_container_width=True)

        # Textos POST-MAPA
        if pagina == "🗺️ Escenario":
            st.info("👉 Esto es lo que ve el equipo de emergencias en el primer minuto: puntos sueltos. Ve a **💥 Algoritmo** para ver cómo la matemática construye el perímetro.")

        elif pagina == "💥 Algoritmo":
            with st.expander("⏱️ Complejidad y Rendimiento"):
                st.markdown(
                    "El tiempo de ejecución de la Marcha de Jarvis depende tanto del número total de focos ($n$) "
                    "como de los vértices que forman el perímetro final ($h$).\n\n"
                    "- **Complejidad del bucle de Jarvis:** $O(n \\cdot h)$, ya que en cada uno de los $h$ vértices se recorren los $n$ puntos buscando el mínimo angular en tiempo lineal.\n"
                    f"- **⏳ Tiempo real medido en esta ejecución:** `{tiempo_ms:.2f} ms`."
                )
            st.info("👉 Ahora que tenemos el polígono geométrico, ve a **🛠️ Consecuencias** para traducir esta matemática en decisiones operativas.")

        elif pagina == "🛠️ Consecuencias":
            with st.expander("⚠️ Limitaciones de la Envolvente Convexa"):
                st.write("Aunque es excelente para establecer una zona de exclusión rápida, conviene tener en cuenta sus límites geométricos:")
                st.markdown(
                    "- **Cota Superior Conservadora:** Si el incendio tiene forma cóncava (p. ej., herradura), la envolvente incluirá zonas interiores no quemadas.\n"
                    "- **Focos Múltiples:** Si hay dos focos muy separados, el algoritmo los unirá en un solo polígono grande."
                )
            st.info("✅ **Simulación completada.** Puedes cambiar los parámetros en el menú lateral y pulsar de nuevo **🚀 Ejecutar Algoritmo** para probar otro escenario.")


elif pagina == "📈 Evolución":
    if "p" not in st.session_state:
        st.warning("👈 Configura los parámetros en el menú lateral y haz clic en **🚀 Ejecutar Algoritmo** para empezar la simulación.")
    else:
        p = st.session_state["p"]
        rang_usado = st.session_state["rango_incendio"]
        estado_sim = st.session_state.get("estado_sim", 42)

        st.markdown("### 📈 Propagación Dinámica del Incendio (Evolución Temporal)")
        st.write(
            "En un incendio real, el avance del fuego es **dinámico y estocástico**. "
            "Turno a turno, los focos perimetrales generan nuevos frentes y las pavesas arrastradas por el viento provocan saltos. "
            f"Se ordena la evacuación de todo pueblo dentro de la envolvente o a menos de **{MARGEN_EVACUACION_KM} km** de sus lados."
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
                    "Rachas extremas (60 km/h)": 2.5,
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

        if origen_sim == "Núcleo inicial de ignición (Centro)":
            cx = sum(pt[0] for pt in p) / len(p)
            cy = sum(pt[1] for pt in p) / len(p)
            p_ordenados = sorted(p, key=lambda pt: (pt[0] - cx)**2 + (pt[1] - cy)**2)
            p_inicio_sim = p_ordenados[:max(4, min(8, len(p)))]
        else:
            p_inicio_sim = p[:min(len(p), 40)]

        historial_sim = simular_propagacion(
            p_inicio_sim,
            num_turnos,
            dir_viento_rad,
            fuerza_viento_val,
            tasa_exp,
            rang_usado,
            estado_sim,
        )

        st.divider()

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
            delta=f"🚨 +{len(pueblos_nuevos_ahora)} nuevo(s)" if pueblos_nuevos_ahora else None,
            delta_color="inverse"
        )

        fig_sim = go.Figure()

        # Isolíneas de perímetros anteriores
        for t_ant in range(turno_sel):
            ch_ant = historial_sim[t_ant]["CH"]
            if len(ch_ant) >= 3:
                x_ant = [pt[0] * rang_usado for pt in ch_ant] + [ch_ant[0][0] * rang_usado]
                y_ant = [pt[1] * rang_usado for pt in ch_ant] + [ch_ant[0][1] * rang_usado]
                fig_sim.add_trace(go.Scatter(
                    x=x_ant, y=y_ant, mode="lines",
                    line=dict(color="rgba(110, 110, 110, 0.45)", width=1.5, dash="dot"),
                    name="Perímetros anteriores",
                    hoverinfo="skip",
                    showlegend=(t_ant == 0)
                ))

        # Focos antiguos
        if turno_sel > 0:
            focos_previos = historial_sim[turno_sel - 1]["focos_acumulados"]
            fig_sim.add_trace(go.Scatter(
                x=[pt[0] * rang_usado for pt in focos_previos],
                y=[pt[1] * rang_usado for pt in focos_previos],
                mode="markers", name="Focos previos (brasas)",
                marker=dict(color="#B22222", size=6, opacity=0.45),
                hovertemplate="Foco activo previo<br>Este: %{x:.2f} km<br>Norte: %{y:.2f} km<extra></extra>"
            ))

        # Focos nuevos
        fig_sim.add_trace(go.Scatter(
            x=[pt[0] * rang_usado for pt in focos_nuevos],
            y=[pt[1] * rang_usado for pt in focos_nuevos],
            mode="markers", name=f"Nuevos focos (Turno {turno_sel})",
            marker=dict(color="#FFD700", size=9, line=dict(color="#D50000", width=1.5)),
            hovertemplate="Nuevo foco activo<br>Este: %{x:.2f} km<br>Norte: %{y:.2f} km<extra></extra>"
        ))

        # Envolvente convexa actual
        if len(ch_turno) >= 3:
            x_env = [pt[0] * rang_usado for pt in ch_turno] + [ch_turno[0][0] * rang_usado]
            y_env = [pt[1] * rang_usado for pt in ch_turno] + [ch_turno[0][1] * rang_usado]
            fig_sim.add_trace(go.Scatter(
                x=x_env, y=y_env, mode="lines+markers", name=f"Perímetro Jarvis (t={turno_sel})",
                line=dict(color="#062003", width=3),
                marker=dict(color="#062003", size=9, symbol="diamond"),
                fill="toself", fillcolor="rgba(255, 69, 0, 0.28)",
                hovertemplate="Vértice Este: %{x:.2f} km<br>Vértice Norte: %{y:.2f} km<extra></extra>"
            ))

        agregar_trazas_pueblos(fig_sim, ch_turno, rang_usado, sufijo_hover=f" en t={turno_sel}")
        aplicar_estilo_mapa(fig_sim, rang_usado)
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
                x=turnos_x, y=areas_y, mode="lines+markers",
                line=dict(color="#FF4500", width=3), marker=dict(size=8),
                name="Área acumulada"
            ))
            fig_area.add_trace(go.Scatter(
                x=[turno_sel], y=[areas_y[turno_sel]], mode="markers",
                marker=dict(color="#FFD700", size=14, symbol="star", line=dict(color="black", width=2)),
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
                "1. **Anisotropía por viento:** Cuando la fuerza del viento es notable, los focos y la envolvente convexa se elongan en la dirección de sotavento.\n"
                "2. **Saltos de pavesas:** Focos que saltan por delante del frente crean nuevos vértices extremos en la envolvente, provocando saltos bruscos en el área.\n"
                "3. **Planificación de emergencias:** Conocer la velocidad de avance ($\\Delta \\text{Área}/\\Delta t$) y aplicar el margen de seguridad de 1,5 km permite anticipar evacuaciones."
            )