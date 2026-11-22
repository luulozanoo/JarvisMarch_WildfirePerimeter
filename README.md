# 🔥 Jarvis March Wildfire Perimeter

Aplicación web interactiva hecha con **Streamlit** que aplica la **marcha de Jarvis** (*gift wrapping*) para calcular la **envolvente convexa** de un conjunto de puntos, usando como caso real la estimación del **perímetro de un incendio forestal** a partir de focos de calor.

<!-- Añade aquí una captura de la app: ![Captura de la aplicación](docs/captura.png) -->

---

## 📖 El problema

Cuando hay un incendio activo, nadie ve la zona afectada completa. Lo que se tiene son **detecciones puntuales** (satélites, drones con cámara térmica, sensores o avisos con coordenadas GPS): una nube de puntos (x, y).

Quien coordina la emergencia necesita convertir esa nube en algo útil: **¿qué zona está afectada y qué hay dentro o cerca de ella?**

La **envolvente convexa** de los focos es el polígono más pequeño, sin entrantes, que los contiene a todos. Se puede imaginar como una goma elástica estirada alrededor de la nube de puntos, y sirve para:

- Delimitar el perímetro del incendio con un único polígono.
- Calcular el área afectada y la longitud del perímetro.
- Decidir qué poblaciones o infraestructuras quedan dentro o cerca de la zona.

> ⚠️ Los datos de la aplicación son **simulados**. No se usan datos reales de incendios.

---

## 🧮 El algoritmo: marcha de Jarvis

La marcha de Jarvis construye la envolvente "envolviendo" la nube de puntos, como si se atara una cuerda a un punto extremo y se fuera girando alrededor de ella hasta cerrar el contorno.

**Implementación de este proyecto:**

1. Se parte del punto más bajo (menor `y`), que seguro pertenece a la envolvente.
2. Desde el vértice actual, se ordenan todos los puntos por **ángulo** alrededor de él.
3. El siguiente vértice de la envolvente es el que sigue, en ese orden angular, al vértice del que venimos.
4. Se repite hasta volver al punto inicial.

**Complejidad:**


| Jarvis  | O(n · h) |


Donde `n` es el número de focos y `h` el número de vértices de la envolvente. En el mejor caso (pocos vértices, como en un incendio compacto) el algoritmo es rápido. En el peor caso, cuando casi todos los puntos están en la envolvente (`h ≈ n`), el coste crece mucho. La distribución **Anillo** reproduce justo ese caso.

---

## ✨ Funcionalidades actuales

- **Seis distribuciones de focos**, pensadas para contar situaciones distintas:

  | Distribución | Qué representa |
  |---|---|
  | Viento (Direccional) | Incendio alargado que avanza en una dirección, con flancos estrechos |
  | Múltiples Focos | Varios grupos separados; muestra por qué una sola envolvente une zonas lejanas |
  | Frente de Fuego | Focos casi alineados a lo largo de una línea; caso límite para el algoritmo |
  | Gaussiana (Centro) | Un único foco de ignición que se extiende en todas direcciones |
  | Anillo | Fuego activo solo en el borde; peor caso del algoritmo (`h ≈ n`) |
  | Uniforme | Caso de referencia |

- **Parámetros ajustables:** número de focos (3 a 1000), tamaño de la zona (1 a 10 km de lado) y **semilla aleatoria** para repetir exactamente el mismo incendio.
- **Mapa interactivo (Plotly)** con ejes en kilómetros, escala 1:1 y coordenadas al pasar el ratón. Todos los puntos generados quedan siempre dentro de la zona del mapa.
- **Sección Algoritmo:** slider que muestra cómo la envolvente se va construyendo vértice a vértice.
- **Sección Consecuencias:** perímetro completo del incendio y métricas (focos, vértices de la envolvente y tiempo de cálculo en ms).
- **Imagen de fondo opcional** para dar contexto visual de bosque.

---

## 🚀 Instalación y uso

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/jarvis-march-wildfire-perimeter.git
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

Se abrirá en el navegador (por defecto en `http://localhost:8501`).

### Cómo usarla

1. En la barra lateral, elige la **distribución**, el **número de focos**, el **tamaño de la zona** y, si quieres, una **semilla**.
2. Pulsa **🚀 Ejecutar Algoritmo**.
3. Cambia de sección en el selector de la barra lateral. Todas muestran el **mismo incendio** hasta que vuelvas a pulsar el botón.

> 💡 El fondo del mapa se carga desde `mapa_bosque.jpeg`, que debe estar en la misma carpeta que el script. Si no existe, la aplicación funciona igual, sin fondo.

---

## 📁 Estructura del proyecto

```
.
├── pagina_interactiva_proyecto.py   # Aplicación Streamlit (algoritmo, generador de focos y visualización)
├── mapa_bosque.jpeg                 # Imagen de fondo del mapa (opcional)
└── README.md
```

---

## ⚠️ Limitaciones conocidas

- **Un incendio real rara vez es convexo.** Con viento o con barreras naturales (ríos, barrancos) el contorno tiene entrantes, y la envolvente convexa **sobreestima** el área afectada. Es una cota superior conservadora, algo razonable en una evacuación, pero no un contorno ajustado.
- **Varios incendios lejanos** quedan unidos en un único polígono. La distribución *Múltiples Focos* lo ilustra.
- Los focos son **simulados** y las coordenadas se generan en un cuadrado unidad que luego se escala a kilómetros.

---

## 🗺️ Próximos pasos

- [x] Generador de focos con distintas distribuciones y semilla
- [x] Marcha de Jarvis implementada desde cero
- [x] Mapa interactivo con escala en kilómetros
- [x] Visualización paso a paso de la envolvente
- [ ] Área en hectáreas y perímetro en kilómetros
- [ ] Poblaciones con aviso de evacuación y margen de seguridad
- [ ] Paso a paso con explicación y candidatos evaluados
- [ ] Evolución temporal del incendio y velocidad de propagación
- [ ] Análisis de tiempos (mejor y peor caso, comparación con otras implementaciones)
- [ ] Agrupar focos para calcular una envolvente por incendio
- [ ] Contornos no convexos como alternativa (*alpha shapes*)

---

## 🛠️ Tecnologías

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/python/)
- [Pillow](https://python-pillow.org/)

---

## 👥 Autoría

**Jorge Ois de Pascual**  
**Gonzalo Velasco Lucas**  
**Lucía Lozano Isac**  
- Estudiantes de Ingeniería Matemáticas e Inteligencia Artificial
