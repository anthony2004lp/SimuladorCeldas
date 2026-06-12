# Simulador de Distribucion de Pesos

Aplicacion de escritorio interactiva que visualiza la distribucion de peso entre 4 celdas de carga en las esquinas de un area cuadrada. Soporta dos modos:

- **Simulacion**: arrastra la bola con el mouse y los pesos se calculan por interpolacion bilineal inversa
- **Datos reales**: conecta una balanza via puerto serial y visualiza las lecturas en tiempo real

```
┌─────────────────────────────────────────────────────┐
│  Simulador de Distribucion de Pesos                 │
├──────────┬──────────────────────────────────────────┤
│          │  Control          Puerto Serial          │
│  ┌──────┐│  Peso aplicado:   COM3  [9600]           │
│  │  TL  ││  [100]            [Conectar]             │
│  │      ││  [0 kg]  [Tara]   Desconectado           │
│  │  ●   ││  Pos: (200,200)                          │
│  │      ││  [Reiniciar]                             │
│  │  BL  ││  Modo: Simulacion                        │
│  └──────┘│                                          │
├──────────┴──────────────────────────────────────────┤
│  Distribucion de Pesos                              │
│  Sup Izq: 25.0 [Llevar]  Sup Der: 25.0 [Llevar]     │
│  Inf Izq: 25.0 [Llevar]  Inf Der: 25.0 [Llevar]     │
└─────────────────────────────────────────────────────┘
```

## Requisitos

- Python 3.8 o superior
- tkinter (incluido con Python)
- NumPy 2.4
- pyserial 3.5
- cx_Freeze==8.6.4

## Instalacion y ejecucion

```bash
pip install -r requirements.txt
python app.py
```
## Empaquetado de programa

```bash
python setup.py build (.exe)
python setup.py bdist_msi (instalador)
```
## Como usar

### Modo Simulacion
1. **Arrastrar la bola roja** dentro del cuadrado con el mouse
2. **Ajustar el peso aplicado** (0-160.000 kg) que se coloca sobre la plataforma
3. Use **Poner peso en 0 kg** para llevar el peso aplicado a cero
4. Use **Tara** para compensar los offsets de las celdas (las lecturas negativas desaparecen)
5. Use **Reiniciar posicion** para centrar la bola
6. Use **Llevar** en cada esquina para mover la bola directamente a esa posicion
7. Los pesos en las esquinas se actualizan en tiempo real con colores:
   - Verde (< 33%): peso bajo
   - Azul (33-66%): peso medio
   - Rojo (> 66%): peso alto
8. El **Total medido** es la suma real de las 4 celdas (incluye ruido gaussiano ±2 kg)
9. Cada celda tiene una variacion fija (offset) que se compensa con la tara

### Modo Datos Reales (Serial)
1. Conecte la balanza al puerto USB/RS232
2. Haga clic en **Escanear** para detectar puertos disponibles
3. Seleccione el puerto (ej: COM3) y los baudios
4. Haga clic en **Conectar**
5. La aplicacion cambia automaticamente a modo datos reales
6. La bola se posiciona segun los valores de las celdas

### Tara de celdas

Las celdas de carga tienen **offsets fijos** que simulan errores de cero del sensor real. Al iniciar la app:
- **Superior Izquierda** e **Inferior Derecha**: valores negativos (~ -95 a -100 kg)
- **Superior Derecha** e **Inferior Izquierda**: valores positivos (~ 30 kg)
- **Total medido**: puede diferir del peso aplicado por la suma de los offsets

Para compensar, presione **Tara** — el sistema captura los offsets y los resta de todas las lecturas, comportandose como una balanza real tarada.

### Formato de datos serial esperado
Lineas de texto terminadas en `\n`:
- **JSON**: `{"top-left": 25.0, "top-right": 31.2, "bottom-left": 18.8, "bottom-right": 25.0}`
- **CSV**: `25.0,31.2,18.8,25.0`
- **Numeros**: extrae los primeros 4 numeros de cualquier formato

## Estructura del proyecto

```
SimuladorCeldas/
├── app.py                        # Interfaz grafica (tkinter)
├── requirements.txt              # Dependencias
├── setup.py                      # Empaquetado de carpetas/archivos
├── .gitignore
├── config/
│   ├── constans.py               # Constantes del sistema
│   └── settings.json             # Configuracion
├── src/backend/
│   ├── models/
│   │   └── weight_models.py      # Modelo de datos
│   └── services/
│       ├── weight_services.py    # Logica de interpolacion bilineal, ruido y tara
│       ├── serial_service.py     # Comunicacion serial
│       └── cell_protocol.py      # Protocolo HBM C16iC3 (celdas virtuales)
├── docs/
│   ├── cambios.md                # Registro de cambios de realismo
│   ├── arquitectura.md           # Arquitectura detallada
│   ├── protocolo_comunicacion.md # Protocolo de celdas HBM
│   └── requerimientos.md         # Requerimientos
└── README.md
```

## Tecnologias

- **Python 3** con **tkinter** para la interfaz de escritorio
- **NumPy** para operaciones numericas
- **pyserial** para comunicacion con balanzas via puerto serial
- **cx_Freeze** para más control sobre el proceso de empaquetado
