# Arquitectura del Simulador de Distribucion de Pesos

## Vista General

Aplicacion de escritorio desarrollada en Python con **tkinter** para la interfaz grafica.
El backend de calculo se mantiene separado de la presentacion siguiendo una arquitectura
de capas simple.

```
┌─────────────────────────────────────────────────────────────┐
│                        app.py                               │
│           (Punto de entrada - Interfaz tkinter)             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               SimuladorCeldas (clase)                │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐   │   │
│  │  │ Canvas      │  │ Panel de     │  │ Panel de   │   │   │
│  │  │ (dibujo)    │  │ Control      │  │ Resultados │   │   │
│  │  └─────────────┘  └──────────────┘  └────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                    │
│                        ▼                                    │
│            ┌──────────────────────┐                         │
│            │   WeightService      │                         │
│            │   (logica de calculo)│                         │
│            └──────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Estructura del Proyecto

```
SimuladorCeldas/
├── app.py                        # Punto de entrada, interfaz grafica tkinter
├── requirements.txt              # Dependencias (NumPy)
├── README.md                     # Documentacion basica
├── config/
│   ├── constans.py               # Constantes del sistema
│   └── settings.json             # Configuracion de simulacion
├── src/
│   └── backend/
│       ├── models/
│       │   └── weight_models.py       # Modelo de datos
│       └── services/
│           └── weight_services.py     # Logica de negocio
└── docs/
    ├── requerimientos.md          # Requerimientos funcionales y no funcionales
    └── arquitectura.md            # Este documento
```

## Capas de la Aplicacion

### 1. Capa de Presentacion (app.py)
- **Tecnologia**: tkinter (biblioteca estandar de Python)
- **Clase principal**: `SimuladorCeldas` en `app.py`
- **Componentes visuales**:
  - `Canvas`: Dibuja el area cuadrada, cuadricula, marcas de esquinas y la bola roja
  - `Panel de Control`: Entrada de peso total, informacion de posicion, boton de reinicio
  - `Panel de Resultados`: Muestra los pesos calculados para cada esquina con colores
- **Eventos**: Mouse (Button-1, B1-Motion, ButtonRelease-1) para arrastrar la bola

### 2. Capa de Logica de Negocio (Services)
- **Clase**: `WeightService` en `src/backend/services/weight_services.py`
- **Metodo principal**: `calculate_corner_weights(x, y, total_weight)`
  - Normaliza coordenadas a rango [0, 1]
  - Aplica interpolacion bilineal inversa:
    - `top_left = (1 - nx) * (1 - ny)`
    - `top_right = nx * (1 - ny)`
    - `bottom_left = (1 - nx) * ny`
    - `bottom_right = nx * ny`
  - Normaliza para que la suma sea 1
  - Multiplica por el peso total
- **Color**: `get_weight_color(weight, total_weight)` determina color verde/amarillo/rojo

### 3. Capa de Modelos (Models)
- **Clase**: `WeightDistribution` en `src/backend/models/weight_models.py`
- **Atributos**: peso total, posicion (x, y), tamano del cuadrado, pesos por esquina
- **Metodos**: `to_dict()` (serializacion), `update_position()` (con limites)

### 4. Capa de Configuracion
- **`config/settings.json`**: Frecuencia de actualizacion, metodo de interpolacion
- **`config/constans.py`**: Tamano del cuadrado (400px), peso maximo (100kg), minimo (0kg), coordenadas de esquinas, colores

## Flujo de Datos

```
Usuario inicia la aplicacion
        │
        ▼
app.py main()
  - Crea ventana tkinter (root)
  - Instancia SimuladorCeldas(root)
        │
        ▼
SimuladorCeldas.__init__()
  - Inicializa servicios y modelo
  - Construye interfaz grafica
  - Realiza primer calculo
        │
        ▼
Usuario arrastra bola con el mouse
        │
        ▼
_on_mouse_move(event)
  - Actualiza ball_x, ball_y
  - Llama a _dibujar_canvas()
  - Llama a _calcular_y_actualizar()
        │
        ▼
_calcular_y_actualizar()
  - Obtiene peso total del control
  - Llama a WeightService.calculate_corner_weights()
        │
        ▼
WeightService.calculate_corner_weights()
  - Normaliza coordenadas
  - Aplica interpolacion bilineal inversa
  - Distribuye peso proporcionalmente
  - Retorna pesos por esquina
        │
        ▼
_calcular_y_actualizar() (continuacion)
  - Actualiza modelo WeightDistribution
  - Actualiza labels de peso con colores
  - Actualiza label de posicion
```

## Algoritmo: Interpolacion Bilineal Inversa

El calculo de distribucion de pesos simula 4 sensores en las esquinas.
Cuando la bola se coloca cerca de una esquina, esa esquina recibe mas peso.

### Formula

Dado un punto (x, y) dentro del cuadrado de tamano S:

1. Normalizar: `nx = x / S`, `ny = y / S`
2. Calcular pesos relativos:
   - Superior izquierda: `(1 - nx) * (1 - ny)`
   - Superior derecha: `nx * (1 - ny)`
   - Inferior izquierda: `(1 - nx) * ny`
   - Inferior derecha: `nx * ny`
3. Normalizar para que sumen 1 (dividir cada peso entre la suma total)
4. Multiplicar cada peso relativo por `total_weight`

### Ejemplo

Bola en el centro (200, 200) con peso total 100 kg:

- `nx = 0.5`, `ny = 0.5`
- Cada esquina recibe: `0.5 * 0.5 = 0.25` → 25 kg cada una

Bola cerca de esquina superior izquierda (50, 50) con peso total 100 kg:

- `nx = 0.125`, `ny = 0.125`
- Superior izquierda: `(0.875 * 0.875) = 0.766` → 76.6 kg
- Superior derecha: `(0.125 * 0.875) = 0.109` → 10.9 kg
- Inferior izquierda: `(0.875 * 0.125) = 0.109` → 10.9 kg
- Inferior derecha: `(0.125 * 0.125) = 0.016` → 1.6 kg

La esquina mas cercana recibe la mayor parte del peso.

## Ejecucion

```bash
python app.py
# Se abre una ventana de escritorio
# Arrastrar la bola roja para ver la distribucion de pesos
```
