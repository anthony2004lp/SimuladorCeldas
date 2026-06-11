# Arquitectura del Simulador de Distribucion de Pesos

## Vista General

Aplicacion de escritorio desarrollada en Python con **tkinter** para la interfaz grafica.
El backend de calculo se mantiene separado de la presentacion siguiendo una arquitectura
de capas simple.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              app.py                                      │
│                   (Punto de entrada - Interfaz tkinter)                  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │                       SimuladorCeldas (clase)                     │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐   │   │
│  │  │ Canvas      │  │ Panel de     │  │ Panel Puerto Serial    │   │   │
│  │  │ (dibujo)    │  │ Control      │  │ + Protocolo HBM        │   │   │
│  │  └─────────────┘  │ - Peso apl.  │  └────────────────────────┘   │   │
│  │                   │ - Tara        │                               │   │
│  │  ┌─────────────────────────────┐  │                               │   │
│  │  │     Panel de Resultados     │  │                               │   │
│  │  │  Pesos x esquina + colores  │  │                               │   │
│  │  │  Total medido (suma real)   │  │                               │   │
│  │  └─────────────────────────────┘  │                               │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                        │                  │                              │
│          ┌─────────────┼─────────────┐    │                              │
│          ▼             ▼             ▼    ▼                              │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────────┐    │
│  │ WeightService│ │ Serial   │ │ SerialService│ │ CellProtocol     │    │
│  │ (simulacion) │ │ (datos)  │ │ (hardware)   │ │ (HBM C16iC3 virt)│    │
│  │ - bilineal   │ │          │ │              │ │ - MSV?/IDN?/ADR  │    │
│  │ - ruido      │ │          │ │              │ │ - 4 celdas S00-3 │    │
│  │ - tara       │ │          │ │              │ └──────────────────┘    │
│  │ - total real │ │          │ │              │                         │
│  └──────────────┘ └──────────┘ └──────────────┘                         │
└──────────────────────────────────────────────────────────────────────────┘
```

## Estructura del Proyecto

```
SimuladorCeldas/
├── app.py                        # Punto de entrada, interfaz grafica tkinter
├── requirements.txt              # Dependencias (NumPy, pyserial, cx_Freeze)
├── README.md                     # Documentacion basica
├── setup.py                      # Empaquetado con cx_Freeze
├── .gitignore
├── icon.ico                      # Icono de la aplicacion
├── config/
│   ├── constans.py               # Constantes del sistema
│   └── settings.json             # Configuracion de simulacion y serial
├── src/
│   └── backend/
│       ├── models/
│       │   └── weight_models.py       # Modelo de datos WeightDistribution
│       └── services/
│           ├── weight_services.py     # Logica de interpolacion, ruido y tara
│           ├── serial_service.py      # Comunicacion serial con balanza
│           └── cell_protocol.py       # Protocolo HBM C16iC3 (celdas virtuales)
├── docs/
│   ├── cambios.md                # Registro de cambios de realismo
│   ├── requerimientos.md         # Requerimientos funcionales y no funcionales
│   ├── protocolo_comunicacion.md # Documentacion del protocolo HBM
│   └── arquitectura.md           # Este documento
├── build/                        # Output de empaquetado
└── dist/                         # Instalador MSI
```

## Capas de la Aplicacion

### 1. Capa de Presentacion (app.py)
- **Tecnologia**: tkinter (biblioteca estandar de Python)
- **Clase principal**: `SimuladorCeldas` en `app.py`
- **Componentes visuales**:
  - `Canvas`: Dibuja el area cuadrada de 400x400px, cuadricula, marcas de esquinas y la bola roja
  - `Panel de Control`: Entrada de peso aplicado (spinbox 0-160.000 kg), boton "Poner peso en 0 kg", boton **"Tara"** (alterna activacion de tara con indicador visual), informacion de posicion (X, Y), boton de reinicio de posicion
  - `Panel Puerto Serial`: Selector de puerto, baudios, boton conectar/desconectar, estado, checkbox de reenvio de datos, feedback visual de comandos HBM
  - `Panel de Resultados`: Muestra los pesos de cada esquina con colores (verde/azul/rojo) y botones "Llevar" para mover la bola a esa esquina. Incluye **Total medido** (suma real de las 4 celdas) separado por una linea horizontal
- **Modos de operacion**:
  - **Simulacion** (por defecto): la bola se arrastra con el mouse y los pesos se calculan por interpolacion bilineal con ruido gaussiano
  - **Datos reales** (serial conectado): los pesos llegan del puerto serial y la bola se posiciona segun los valores reales
- **Eventos**: Mouse (Button-1, B1-Motion, ButtonRelease-1) para arrastrar la bola

### 2. Capa de Comunicacion Serial
- **Clase**: `SerialService` en `src/backend/services/serial_service.py`
- **Funciones**:
  - `list_available_ports()`: Escanea puertos COM/tty disponibles
  - `connect(port, baudrate)`: Conecta al puerto especificado
  - `disconnect()`: Desconecta del puerto
  - `start_reading(data_callback, error_callback)`: Inicia hilo en segundo plano para lectura continua
  - `send_data(data)`: Envia datos al puerto
- **Formato de datos soportado**:
  - **JSON**: `{"top-left": 25, "top-right": 25, "bottom-left": 25, "bottom-right": 25}`
  - **CSV**: `25.0,25.0,25.0,25.0` (4 valores separados por coma)
  - **Numeros libres**: Extrae los primeros 4 numeros de la linea con regex
- **Protocolo HBM**: Detecta automaticamente comandos del protocolo HBM C16iC3 y los delega a `CellProtocol`, enviando la respuesta de vuelta al puerto
- **Lectura**: Hilo en segundo plano con buffer de linea, parsea cada linea completa

### 3. Capa de Protocolo HBM
- **Clase**: `CellProtocol` en `src/backend/services/cell_protocol.py`
- **Funcion**: Simula 4 celdas de carga HBM C16iC3/40t con direcciones S00-S03
- **Comandos soportados**: `MSV?` (peso), `IDN?` (identificacion), `ADR` (reasignar direccion), `TDD1` (guardar EEPROM)
- **Formatos**: Multi-linea (S98 -> comando -> Sxx) y clasico (Sxx;MSV?;)
- **Integracion**: Los pesos se actualizan desde `WeightService` en simulacion o desde datos seriales en modo real

### 4. Capa de Logica de Negocio (WeightService)
- **Clase**: `WeightService` en `src/backend/services/weight_services.py`
- **Responsabilidades**:
  - Distribucion del peso aplicado mediante interpolacion bilineal inversa
  - Simulacion de **offsets fijos** por celda (error de cero del sensor)
  - Generacion de **ruido gaussiano** ±2 kg en cada lectura
  - Sistema de **Tara** (captura/restaura de offsets)
  - Calculo del **total medido** como suma real de las 4 celdas
- **Metodo principal**: `calculate_corner_weights(x, y, total_weight)`
  1. Normaliza coordenadas a rango [0, 1]
  2. Aplica interpolacion bilineal inversa:
     - `top_left = (1 - nx) * (1 - ny)`
     - `top_right = nx * (1 - ny)`
     - `bottom_left = (1 - nx) * ny`
     - `bottom_right = nx * ny`
  3. Normaliza para que la suma sea 1
  4. Multiplica por el peso aplicado
  5. Agrega offset fijo por celda (generado al iniciar el servicio)
  6. Agrega ruido gaussiano independiente por celda
  7. Si la tara esta activa, resta la linea base capturada
- **Tara**: `tare()` captura offsets como baseline; `clear_tare()` los restaura; `is_tared` indica estado
- **Total medido**: `get_measured_total(corner_weights)` retorna la suma real de las 4 celdas
- **Color**: `get_weight_color(weight, total_weight)` determina color verde/azul/rojo segun porcentaje respecto al total medido

### 5. Capa de Modelos (Models)
- **Clase**: `WeightDistribution` en `src/backend/models/weight_models.py`
- **Atributos**: peso total (ahora se actualiza con el total medido, no el aplicado), posicion (x, y), tamano del cuadrado, pesos por esquina
- **Metodos**: `to_dict()` (serializacion), `update_position()` (con limites)

### 6. Capa de Configuracion
- **`config/settings.json`**: Frecuencia de actualizacion, metodo de interpolacion, configuracion serial por defecto
- **`config/constans.py`**: Tamano del cuadrado (400px), peso maximo (160.000 kg = 4 celdas de 40t), minimo (0kg), coordenadas de esquinas, colores

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
Usuario arrastra bola con el mouse  o  cambia peso aplicado  o  presiona Tara
        │
        ▼
_calcular_y_actualizar()
  - Obtiene peso aplicado del spinbox
  - Llama a WeightService.calculate_corner_weights()
        │
        ▼
WeightService.calculate_corner_weights()
  1. Normaliza coordenadas
  2. Aplica interpolacion bilineal inversa
  3. Multiplica por peso aplicado
  4. Agrega offset fijo por celda
  5. Agrega ruido gaussiano individual
  6. Si tara activa: resta baseline
  7. Retorna pesos por esquina
        │
        ▼
_calcular_y_actualizar() (continuacion)
  - Obtiene total medido = suma real de las 4 celdas
  - Actualiza modelo WeightDistribution con total medido
  - Actualiza labels de peso con colores (referencia = total medido)
  - Actualiza label de total medido
  - Actualiza label de posicion
  - Actualiza protocolo HBM
```

### Modo Datos Reales (Serial)

```
Usuario conecta puerto serial
        │
        ▼
_toggle_serial()
  - SerialService.connect(port, baud)
  - Inicia SerialService.start_reading(data_callback, error_callback)
        │
        ▼
SerialService._read_loop()  [hilo separado]
  - Lee datos del puerto en bucle
  - Acumula en buffer hasta encontrar \n
  - Parsea cada linea completa
  - Si es comando HBM: CellProtocol.handle_command(), envia respuesta
  - Si son datos: llama al callback con {top-left, top-right, ...}
        │
        ▼
_on_serial_data(weights)
  - Programa actualizacion en hilo principal
        │
        ▼
_actualizar_con_datos_reales(weights)
  - Calcula posicion de la bola desde los 4 pesos
  - Actualiza labels de peso con colores
  - Actualiza label de total medido
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
4. Multiplicar cada peso relativo por `peso_aplicado`
5. Agregar offset fijo de cada celda
6. Agregar ruido gaussiano ±2 kg
7. Si tara activa, restar baseline capturado

### Ejemplo

Bola en el centro (200, 200) con peso aplicado 100 kg y tara activa:

- `nx = 0.5`, `ny = 0.5`
- Cada esquina: `0.5 * 0.5 = 0.25` → 25 kg + ruido
- Total medido ≈ 100 kg

Bola cerca de esquina superior izquierda (50, 50) con peso aplicado 100 kg:

- `nx = 0.125`, `ny = 0.125`
- Superior izquierda: `(0.875 * 0.875) = 0.766` → ~76.6 kg + ruido
- Superior derecha: `(0.125 * 0.875) = 0.109` → ~10.9 kg + ruido
- Inferior izquierda: `(0.875 * 0.125) = 0.109` → ~10.9 kg + ruido
- Inferior derecha: `(0.125 * 0.125) = 0.016` → ~1.6 kg + ruido

La esquina mas cercana recibe la mayor parte del peso.

## Ejecucion

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python app.py
```

## Tara de Celdas

El sistema de tara permite compensar los offsets fijos de las celdas:

1. **Antes de tarar**: Las celdas muestran sus valores con offsets incluidos. Tipicamente TL y BR aparecen negativos (~ -95 a -100 kg) debido a los offsets negativos asignados
2. **Al presionar Tara**: Se capturan los offsets actuales como linea base y se restan de todas las lecturas futuras
3. **Con tara activa**: Las lecturas reflejan solo el peso aplicado + ruido gaussiano, comportandose como una balanza real calibrada
4. **Al presionar Tara otra vez**: Se desactiva la tara y los offsets vuelven a aparecer

El indicador "Tara activa" aparece debajo de la posicion en el panel de control mientras la compensacion esta activa.

## Conexion Serial

1. Conecte la balanza al puerto USB/RS232
2. En la aplicacion, haga clic en **Escanear** para detectar puertos
3. Seleccione el puerto (ej: COM3) y los baudios (ej: 9600)
4. Haga clic en **Conectar**
5. Los datos comenzaran a leerse en tiempo real
6. La aplicacion cambia automaticamente a modo "Datos reales"

### Formato de datos esperado

La balanza debe enviar lineas de texto terminadas en `\n` con uno de estos formatos:

| Formato | Ejemplo |
|---------|---------|
| JSON | `{"top-left": 25.0, "top-right": 31.2, "bottom-left": 18.8, "bottom-right": 25.0}` |
| CSV | `25.0,31.2,18.8,25.0` |
| Numeros | `TL:25.0 TR:31.2 BL:18.8 BR:25.0` (extrae los primeros 4 numeros) |

### Formato de envio

La aplicacion tambien puede **enviar datos** al puerto serial usando `SerialService.send_data()`.
