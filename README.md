# Simulador de Distribucion de Pesos

Aplicacion de escritorio interactiva que simula como se distribuye un peso total entre 4 sensores ubicados en las esquinas de un area cuadrada, utilizando interpolacion bilineal inversa. Arrastra la bola con el mouse y observa los cambios en tiempo real.

## Captura

```
┌─────────────────────────────────────────┐
│  Simulador de Distribucion de Pesos     │
├──────────┬──────────────────────────────┤
│          │  Control                     │
│  ┌──────┐│  Peso Total (kg):            │
│  │  TL  ││  [100]                       │
│  │      ││                              │
│  │  ●   ││  Posicion: (200, 200)        │
│  │      ││                              │
│  │  BL  ││  [Reiniciar posicion]        │
│  └──────┘│                              │
├──────────┴──────────────────────────────┤
│  Distribucion de Pesos                  │
│  Superior Izquierda: 25.0 kg  (verde)   │
│  Superior Derecha:   25.0 kg  (verde)   │
│  Inferior Izquierda: 25.0 kg  (verde)   │
│  Inferior Derecha:   25.0 kg  (verde)   │
└─────────────────────────────────────────┘
```

## Requisitos

- Python 3.8 o superior
- tkinter (incluido con Python)
- NumPy 1.26 (`pip install numpy==1.26.0`)

## Instalacion y ejecucion

```bash
# 1. Clonar o descargar el proyecto
# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
python app.py
```

No requiere servidor web ni conexion a internet. Se abre directamente una ventana de escritorio.

## Como usar

1. **Arrastrar la bola roja** dentro del cuadrado con el mouse
2. **Ajustar el peso total** con el control numerico (0-500 kg, pasos de 10)
3. **Observar los pesos** en cada esquina: se actualizan en tiempo real con colores:
   - Verde (< 33%): peso bajo
   - Amarillo (33-66%): peso medio
   - Rojo (> 66%): peso alto
4. **Reiniciar posicion** con el boton para volver la bola al centro

## Estructura del proyecto

```
SimuladorCeldas/
├── app.py                        # Punto de entrada - interfaz grafica (tkinter)
├── requirements.txt              # Dependencias
├── config/
│   ├── constans.py               # Constantes: tamano, pesos, colores
│   └── settings.json             # Configuracion de simulacion
├── src/
│   └── backend/
│       ├── models/
│       │   └── weight_models.py       # Modelo de datos
│       └── services/
│           └── weight_services.py     # Logica de interpolacion bilineal
├── docs/
│   ├── arquitectura.md           # Documentacion de arquitectura
│   └── requerimientos.md         # Requerimientos funcionales
└── README.md
```

## Algoritmo

La distribucion de pesos usa interpolacion bilineal inversa:

1. La posicion de la bola se normaliza a coordenadas (nx, ny) en rango [0, 1]
2. Cada esquina recibe un peso proporcional al area rectangular opuesta
3. Los pesos se normalizan para que sumen el peso total ingresado

A menor distancia a una esquina, mayor peso recibe esa esquina.

## Tecnologias

- **Python 3** con **tkinter** para la interfaz de escritorio
- **NumPy** para operaciones numericas
- Sin dependencias web, sin servidor, sin frameworks externos
