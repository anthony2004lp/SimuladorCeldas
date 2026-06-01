# Simulador de Distribucion de Pesos

Aplicacion de escritorio interactiva que visualiza la distribucion de peso entre 4 celdas de carga en las esquinas de un area cuadrada. Soporta dos modos:

- **Simulacion**: arrastra la bola con el mouse y los pesos se calculan por interpolacion bilineal inversa
- **Datos reales**: conecta una balanza via puerto serial y visualiza las lecturas en tiempo real

```
┌─────────────────────────────────────────────────────┐
│  Simulador de Distribucion de Pesos                 │
├──────────┬──────────────────────────────────────────┤
│          │  Control          Puerto Serial          │
│  ┌──────┐│  Peso: [100]      COM3  [9600]           │
│  │  TL  ││  Pos: (200,200)   [Conectar]             │
│  │      ││  [Reiniciar]      Desconectado           │
│  │  ●   ││                                          │
│  │      ││  Modo: Simulacion                        │
│  │  BL  ││                                          │
│  └──────┘│                                          │
├──────────┴──────────────────────────────────────────┤
│  Distribucion de Pesos                              │
│  Superior Izquierda: 25.0 kg  Superior Der: 25.0 kg │
│  Inferior Izquierda: 25.0 kg  Inferior Der: 25.0 kg │
└─────────────────────────────────────────────────────┘
```

## Requisitos

- Python 3.8 o superior
- tkinter (incluido con Python)
- NumPy 1.26
- pyserial 3.5

## Instalacion y ejecucion

```bash
pip install -r requirements.txt
python app.py
```

## Como usar

### Modo Simulacion
1. **Arrastrar la bola roja** dentro del cuadrado con el mouse
2. **Ajustar el peso total** (0-500 kg, pasos de 10)
3. Los pesos en las esquinas se actualizan en tiempo real con colores:
   - Verde (< 33%): peso bajo
   - Amarillo (33-66%): peso medio
   - Rojo (> 66%): peso alto

### Modo Datos Reales (Serial)
1. Conecte la balanza al puerto USB/RS232
2. Haga clic en **Escanear** para detectar puertos disponibles
3. Seleccione el puerto (ej: COM3) y los baudios
4. Haga clic en **Conectar**
5. La aplicacion cambia automaticamente a modo datos reales
6. La bola se posiciona segun los valores de las celdas

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
├── .gitignore
├── config/
│   ├── constans.py               # Constantes del sistema
│   └── settings.json             # Configuracion
├── src/backend/
│   ├── models/
│   │   └── weight_models.py      # Modelo de datos
│   └── services/
│       ├── weight_services.py    # Logica de interpolacion bilineal
│       └── serial_service.py     # Comunicacion serial
├── docs/
│   ├── arquitectura.md           # Arquitectura detallada
│   └── requerimientos.md         # Requerimientos
└── README.md
```

## Tecnologias

- **Python 3** con **tkinter** para la interfaz de escritorio
- **NumPy** para operaciones numericas
- **pyserial** para comunicacion con balanzas via puerto serial
