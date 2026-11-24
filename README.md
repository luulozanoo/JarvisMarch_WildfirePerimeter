# 🔥 Jarvis March Wildfire Perimeter

Aplicación web interactiva hecha con **Streamlit** que aplica la **marcha de Jarvis** (*gift wrapping*) para calcular la **envolvente convexa** de un conjunto de puntos, usando como caso práctico la estimación del **perímetro de un incendio forestal** a partir de focos de calor.

<!-- Añade aquí una captura de la app: ![Captura de la aplicación](docs/captura.png) -->

---

## 📖 El problema

Cuando hay un incendio activo, nadie ve la zona afectada completa. Lo que se tiene son **detecciones puntuales** (satélites, drones con cámara térmica, sensores o avisos con coordenadas GPS): una nube de puntos $(x, y)$.

Quien coordina la emergencia necesita convertir esa nube en algo útil: **¿qué zona está afectada, cómo está evolucionando y qué poblaciones están en peligro?**

La **envolvente convexa** de los focos es el polígono más pequeño, sin entrantes, que los contiene a todos. Se puede imaginar como una goma elástica estirada alrededor de la nube de puntos, y sirve para:

- Delimitar el perímetro del incendio con un único polígono.
- Calcular el área afectada (en hectáreas) y la longitud del perímetro (en kilómetros).
- Evaluar qué poblaciones quedan dentro de la zona afectada o demasiado cerca de sus flancos.

> ⚠️ Los datos de la aplicación son **simulados** con fines académicos. No se usan datos reales de incendios.

---

## 🧮 El algoritmo: marcha de Jarvis

La marcha de Jarvis construye la envolvente "envolviendo" la nube de puntos, como si se atara una cuerda a un punto extremo y se fuera girando alrededor de ella hasta cerrar el contorno.

**Implementación en este proyecto:**

1. Se filtran posibles puntos duplicados (con tolerancia numérica de `1e-9`).
2. Se parte del punto más bajo (menor `y`, desempatando por menor `x`), que siempre pertenece a la envolvente.
3. En cada iteración, se recorren todos los puntos buscando de forma lineal el que forma el **menor ángulo** respecto al vector de dirección de la arista anterior (inicialmente `(1, 0)`). En caso de puntos colineales (mismo ángulo), se elige el **más lejano** para evitar vértices redundantes.
4. Se repite el proceso hasta volver al punto inicial.

**Complejidad:**

$$O(n \cdot h)$$

Donde $n$ es el número de focos y $h$ el número de vértices de la envolvente. En el mejor caso (pocos vértices, como en un incendio compacto) el algoritmo es muy rápido. En el peor caso, cuando casi todos los puntos pertenecen a la envolvente ($h \approx n$), el coste tiende a $O(n^2)$. La distribución **Anillo** reproduce precisamente este escenario.

---

## ✨ Funcionalidades

### Configuración y distribuciones
- **Parámetros ajustables** en la barra lateral: tipo de distribución, número de focos (3 a 1000) y tamaño de la zona operativa (1 a 10 km de lado).
- **Seis distribuciones de focos**, pensadas para modelar comportamientos distintos:

  | Distribución | Qué representa |
  | :--- | :--- |
  | **Viento (Direccional)** | Incendio alargado empujado por rachas de viento, con flancos estrechos. |
  | **Múltiples Focos** | Varios grupos separados; ilustra por qué una sola envolvente une zonas lejanas. |
  | **Frente de Fuego** | Focos casi alineados en diagonal; caso límite para el algoritmo. |
  | **Gaussiana (Centro)** | Un único foco de ignición concéntrico que se extiende desde el origen. |
  | **Anillo** | Fuego activo solo en el borde exterior (zona interior quemada); peor caso ($h \approx n$). |
  | **Uniforme** | Fuego descontrolado y esparcido de forma aleatoria (caso de referencia). |

### Navegación por páginas
1. **🏡 Inicio:** Explicación conceptual de la envolvente convexa, resumen de la marcha de Jarvis y guía rápida de uso.
2. **🗺️ Escenario:** Contexto del problema, tabla descriptiva de las distribuciones (visible incluso antes de ejecutar la simulación) y mapa interactivo con la nube inicial de focos.
3. **💥 Algoritmo:** Muestra en tiempo real la distribución seleccionada, explicación paso a paso del código, slider interactivo para construir la envolvente vértice a vértice (marcando el vértice activo) y desplegable con la complejidad teórica y el tiempo real de ejecución en milisegundos.
4. **🛠️ Consecuencias:**
   - Cálculo del **área afectada en hectáreas** (fórmula de Gauss / *Shoelace*) y del **perímetro en kilómetros**.
   - Evaluación automática de evacuación para 4 poblaciones (*San Pedro*, *Valleverde*, *Villa Alta* y *El Puente*) mediante **Ray Casting** y distancia mínima punto-segmento: se ordena evacuar cualquier pueblo situado **dentro de la envolvente o a $\le 1,5\text{ km}$ de cualquiera de sus lados**.
   - Mapa con sombreado de la zona afectada, estado de cada población y distancia exacta al perímetro al pasar el cursor.
5. **📈 Evolución:**
   - Simulación estocástica de propagación temporal (de 2 a 8 turnos/horas) con configuración de **dirección e intensidad del viento**, **tasa de propagación** (*Lenta*, *Moderada*, *Rápida*), **saltos de pavesas** y punto de partida (*núcleo central* o *focos actuales*).
   - Línea temporal interactiva con isolíneas de perímetros anteriores, diferenciación entre brasas previas y focos nuevos, y alertas de nuevas evacuaciones aplicando el margen de $1,5\text{ km}$.
   - Gráficas temporales de **área total afectada (ha)** y **velocidad de expansión ($\Delta\text{ha/hora}$)**.

- **Visualización:** Mapas interactivos en **Plotly** con ejes en kilómetros, relación de aspecto 1:1 e **imagen de fondo opcional** (`mapa_bosque.jpeg`).

---

## 🚀 Instalación y uso

### 1. Clonar el repositorio

```bash
git clone [https://github.com/](https://github.com/)<tu-usuario>/jarvis-march-wildfire-perimeter.git
cd jarvis-march-wildfire-perimeter
```

### 2. Instalar las dependencias

```bash
pip install streamlit plotly pillow
```

### 3. Ejecutar la aplicación

```bash
streamlit run pagina_interactiva_proyecto.py
```

> 💡 **Nota (si `streamlit` no se reconoce como comando en Windows/PowerShell):**  
> Puedes ejecutarlo directamente a través del módulo de Python:  
> ```bash
> python -m streamlit run pagina_interactiva_proyecto.py
> ```

Se abrirá en el navegador (por defecto en `http://localhost:8501`).

### Cómo usarla

1. En la barra lateral, elige la **distribución**, el **número de focos** y el **tamaño de la zona (km)**.
2. Pulsa **🚀 Ejecutar Algoritmo**.
3. Navega por las secciones (`Inicio`, `Escenario`, `Algoritmo`, `Consecuencias` y `Evolución`). Todas trabajan sobre el **mismo incendio** hasta que vuelvas a pulsar el botón de ejecutar.

> 💡 El fondo del mapa se carga desde `mapa_bosque.jpeg`, que debe estar en la misma carpeta que el script. Si no existe, la aplicación funciona igual sin imagen de fondo.

---

## 📁 Estructura del proyecto

```text
.
├── pagina_interactiva_proyecto.py   # Aplicación Streamlit (Jarvis, generador, impacto, evolución y UI)
├── mapa_bosque.jpeg                 # Imagen de fondo del mapa (opcional)
└── README.md
```

---

## ⚠️ Limitaciones conocidas

- **Un incendio real rara vez es convexo.** Con viento o barreras naturales (ríos, barrancos) el contorno tiene entrantes, por lo que la envolvente convexa **sobreestima** el área quemada. Es una cota superior conservadora útil para evacuaciones, pero no un contorno ajustado.
- **Varios incendios lejanos** quedan unidos en un único polígono, como ilustra la distribución *Múltiples Focos*.
- Los focos y la propagación son **simulados** sobre un cuadrado unidad escalado posteriormente a kilómetros, sin relieve topográfico ni tipos de vegetación reales.

---

## 🗺️ Estado del proyecto y posibles mejoras

- [x] Generador de focos con seis distribuciones distintas
- [x] Marcha de Jarvis implementada desde cero (con manejo de duplicados y colinealidad)
- [x] Mapa interactivo con escala 1:1 en kilómetros y fondo opcional
- [x] Visualización paso a paso de la envolvente y medición de tiempo de ejecución
- [x] Cálculo de área en hectáreas y perímetro en kilómetros
- [x] Evaluación de poblaciones con aviso de evacuación (interior + margen de seguridad de 1,5 km)
- [x] Simulación temporal de propagación con viento, pavesas y gráficas de evolución
- [ ] Visualización de los rayos/candidatos evaluados en cada salto del paso a paso
- [ ] Comparativa empírica de tiempos frente a otros algoritmos (Graham Scan, Andrew's Monotone Chain)
- [ ] Agrupación (*clustering*) para calcular una envolvente independiente por cada foco separado
- [ ] Contornos no convexos como alternativa (*alpha shapes* / envolvente cóncava)

---

## 🛠️ Tecnologías

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/python/)
- [Pillow](https://python-pillow.org/)

---

## 👥 Autoría

- **Jorge Ois de Pascual**
- **Gonzalo Velasco Lucas**
- **Lucía Lozano Isac**

*Estudiantes de Ingeniería Matemática e Inteligencia Artificial — Geometría Computacional (ICAI).*

---

## 📬 Contacto

¿Tienes alguna duda sobre el algoritmo, el código o el funcionamiento de la aplicación? Puedes ponerte en contacto a través de cualquiera de estos medios:

- **Correo electrónico:** [lucia.lozano110@gmail.com](lucia.lozano110@gmail.com)
- **GitHub:** [@luulozanoo](https://github.com/luu-lozanoo)
- **Issues del repositorio:** Abre una incidencia en la pestaña [Issues](https://github.com/<tu-usuario>/jarvis-march-wildfire-perimeter/issues) para reportar errores o proponer mejoras.
