# Arquitectura del Simulador de Distribucion de Pesos

## Vista General

Aplicacion de escritorio desarrollada en Python con **tkinter** para la interfaz grafica.
El backend de calculo se mantiene separado de la presentacion siguiendo una arquitectura
de capas simple.

```
┌──────────────────────────────────────────────────────────────────┐
│                        app.py                                    │
│           (Punto de entrada - Interfaz tkinter)                  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │               SimuladorCeldas (clase)                     │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │   │
│  │  │ Canvas      │  │ Panel de     │  │ Panel Puerto   │   │   │
│  │  │ (dibujo)    │  │ Control      │  │ Serial         │   │   │
│  │  └─────────────┘  └──────────────┘  └────────────────┘   │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │            Panel de Resultados                     │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                        │                                         │
│          ┌─────────────┼─────────────┐                           │
│          ▼             ▼             ▼                           │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐                 │
│  │ WeightService│ │ Serial   │ │ SerialService│                 │
│  │ (simulacion) │ │ (datos)  │ │ (hardware)   │                 │
│  └──────────────┘ └──────────┘ └──────────────┘                 │
└──────────────────────────────────────────────────────────────────┘
```

## Estructura del Proyecto

```
SimuladorCeldas/
├── app.py                        # Punto de entrada, interfaz grafica tkinter
├── requirements.txt              # Dependencias (NumPy, pyserial)
├── README.md                     # Documentacion basica
├── .gitignore                    # Exclusiones para control de versiones
├── config/
│   ├── constans.py               # Constantes del sistema
│   └── settings.json             # Configuracion de simulacion y serial
├── src/
│   └── backend/
│       ├── models/
│       │   └── weight_models.py       # Modelo de datos
│       └── services/
│           ├── weight_services.py     # Logica de interpolacion bilineal
│           └── serial_service.py      # Comunicacion serial con balanza
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
  - `Panel Puerto Serial`: Selector de puerto, baudios, boton conectar/desconectar, estado
  - `Panel de Resultados`: Muestra los pesos de cada esquina con colores
- **Modos de operacion**:
  - **Simulacion** (por defecto): la bola se arrastra con el mouse y los pesos se calculan por interpolacion
  - **Datos reales** (serial conectado): los pesos llegan del puerto serial y la bola se posiciona segun los valores reales
- **Eventos**: Mouse (Button-1, B1-Motion, ButtonRelease-1) para arrastrar la bola

### 2. Capa de Comunicacion Serial
- **Clase**: `SerialService` en `src/backend/services/serial_service.py`
- **Funciones**:
  - `list_available_ports()`: Escanea puertos COM/tty disponibles
  - `connect(port, baudrate)`: Conecta al puerto especificado
  - `disconnect()`: Desconecta del puerto
  - `start_reading(callback)`: Inicia hilo en segundo plano para lectura continua
  - `send_data(data)`: Envia datos al puerto
- **Formato de datos soportado**:
  - **JSON**: `{"top-left": 25, "top-right": 25, "bottom-left": 25, "bottom-right": 25}`
  - **CSV**: `25.0,25.0,25.0,25.0` (4 valores separados por coma)
  - **Numeros libres**: Extrae los primeros 4 numeros de la linea con regex
- **Lectura**: Hilo en segundo plano con buffer de linea, parsea cada linea completa

### 3. Capa de Logica de Negocio (Services)
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

### 4. Capa de Modelos (Models)
- **Clase**: `WeightDistribution` en `src/backend/models/weight_models.py`
- **Atributos**: peso total, posicion (x, y), tamano del cuadrado, pesos por esquina
- **Metodos**: `to_dict()` (serializacion), `update_position()` (con limites)

### 5. Capa de Configuracion
- **`config/settings.json`**: Frecuencia de actualizacion, metodo de interpolacion, configuracion serial por defecto
- **`config/constans.py`**: Tamano del cuadrado (400px), peso maximo (100kg), minimo (0kg), coordenadas de esquinas, colores

## Flujo de Datos

La aplicacion tiene dos modos de operacion: **simulacion** y **datos reales (serial)**.

### Modo Simulacion

```
Usuario inicia la aplicacion
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

### Modo Datos Reales (Serial)

```
Usuario conecta puerto serial
        │
        ▼
_toggle_serial()
  - SerialService.connect(port, baud)
  - Inicia SerialService.start_reading(callback)
        │
        ▼
SerialService._read_loop()  [hilo separado]
  - Lee datos del puerto en bucle
  - Acumula en buffer hasta encontrar \\n
  - Parsea cada linea completa
  - Llama al callback con {top-left, top-right, ...}
        │
        ▼
_on_serial_data(weights)
  - Programa actualizacion en hilo principal
        │
        ▼
_actualizar_con_datos_reales(weights)
  - Calcula posicion de la bola desde los 4 pesos
  - Actualiza labels de peso con colores
  - Actualiza posicion en canvas
  - Mueve la bola segun los valores reales
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
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python app.py
```

## Conexion Serial

1. Conecte la balanza al puerto USB/RS232
2. En la aplicacion, haga clic en **Escanear** para detectar puertos
3. Seleccione el puerto (ej: COM3) y los baudios (ej: 9600)
4. Haga clic en **Conectar**
5. Los datos comenzaran a leerse en tiempo real
6. La aplicacion cambia automaticamente a modo "Datos reales"

### Formato de datos esperado

La balanza debe enviar lineas de texto terminadas en `\\n` con uno de estos formatos:

| Formato | Ejemplo |
|---------|---------|
| JSON | `{"top-left": 25.0, "top-right": 31.2, "bottom-left": 18.8, "bottom-right": 25.0}` |
| CSV | `25.0,31.2,18.8,25.0` |
| Numeros | `TL:25.0 TR:31.2 BL:18.8 BR:25.0` (extrae los primeros 4 numeros) |

### Formato de envio

La aplicacion tambien puede **enviar datos** al puerto serial usando `SerialService.send_data()`.
