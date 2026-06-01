# Protocolo de Comunicacion con Celdas de Carga

## Descripcion General

El simulador implementa un protocolo de comunicacion bidireccional compatible
con balanzas y celdas de carga **HBM C16iC3**. A traves del puerto serial,
un sistema externo puede enviar comandos para consultar peso, identificar
dispositivos, asignar direcciones y guardar configuracion.

El programa actua como un conjunto de **4 celdas de carga virtuales**,
cada una con su propia direccion y numero de serie. Los pesos se actualizan
en tiempo real segun la simulacion visual (arrastre de la bola) o los datos
reales recibidos por el puerto serial.

## Direcciones de las Celdas

Por defecto, las 4 celdas virtuales tienen las siguientes direcciones:

| Direccion | Numero de Serie | Esquina Asociada        |
|-----------|-----------------|-------------------------|
| S00       | M64701          | Superior Izquierda (TL) |
| S01       | M64702          | Superior Derecha (TR)   |
| S02       | M64703          | Inferior Izquierda (BL) |
| S03       | M64704          | Inferior Derecha (BR)   |

Las direcciones pueden reasignarse mediante el comando `ADR`.

## Comandos Soportados

### 1. Consultar Peso - `Sxx;MSV?`

Solicita el peso actual de la celda en la direccion especificada.

**Formato:**
```
Sxx;MSV?
```

**Ejemplo:**
```
S01;MSV?
```

**Respuesta:**
```
-0010236
```

Formato de la respuesta: `SGGGGGGG` (signo + 7 digitos)
- El peso se expresa en decimas de kilogramo (0.1 kg = 1 unidad)
- Ejemplo: `-0010236` = -1023.6 kg, ` 0000250` = 25.0 kg
- Si la direccion no existe: `?S00`

**Implementacion:** `VirtualCell.get_weight_response()` en `cell_protocol.py:46`

### 2. Consultar Identificacion - `Sxx;IDN?`

Solicita el modelo, numero de serie y version de firmware de la celda.

**Formato:**
```
Sxx;IDN?
```

**Ejemplo:**
```
S02;IDN?
```

**Respuesta:**
```
HBM,C16iC3/40t     ,M64702 ,P52
```

Formato de la respuesta: `HBM,MODELO          ,SERIAL   ,VERSION`
- MODELO: `C16iC3/40t` (14 caracteres con espacios)
- SERIAL: Numero de serie (7 caracteres con espacios)
- VERSION: `P52` (version de firmware)
- Si la direccion no existe: `?S00`

**Implementacion:** `VirtualCell.get_id_response()` en `cell_protocol.py:57`

### 3. Asignar Direccion - `ADR`

Asigna una nueva direccion a una celda identificada por su numero de serie.

**Formato:**
```
ADR<nueva_direccion>,"<numero_serie>"
```

**Ejemplo:**
```
ADR2,"M64702"
```

Este comando asigna la direccion `S02` a la celda con numero de serie `M64702`.

**Respuesta:**
```
OK M64702 -> S02
```

- Si el numero de serie no existe: `?M64702`

**Nota:** El cambio es inmediato en memoria. Para hacerlo permanente, debe
enviarse el comando `TDD1` a la celda correspondiente.

**Implementacion:** `CellProtocol.handle_command()` en `cell_protocol.py:131`

### 4. Guardar en EEPROM - `Sxx;TDD1`

Guarda la configuracion actual (direccion asignada) en la memoria permanente
de la celda.

**Formato:**
```
Sxx;TDD1
```

**Ejemplo:**
```
S02;TDD1
```

**Respuesta:**
```
OK
```

- Si la direccion no existe: `?S00`

**Nota:** En el simulador, este comando es una operacion virtual (no persiste
entre sesiones). Al reiniciar la aplicacion, las celdas vuelven a sus
direcciones por defecto.

## Ejemplos de Uso

### Ejemplo 1: Consultar peso de todas las celdas

```
S00;MSV?
 0000125
S01;MSV?
 0000312
S02;MSV?
 0000188
S03;MSV?
 0000250
```

### Ejemplo 2: Cambiar direccion y verificar

```
ADR2,"M64702"
OK M64702 -> S02
S02;IDN?
HBM,C16iC3/40t     ,M64702 ,P52
S02;TDD1
OK
```

### Ejemplo 3: Consultar seriales de todas las celdas

```
S00;IDN?
HBM,C16iC3/40t     ,M64701 ,P52
S01;IDN?
HBM,C16iC3/40t     ,M64702 ,P52
S02;IDN?
HBM,C16iC3/40t     ,M64703 ,P52
S03;IDN?
HBM,C16iC3/40t     ,M64704 ,P52
```

## Arquitectura de la Implementacion

### Componentes

```
┌──────────────────────────────────────────────────────────┐
│                      app.py                              │
│  ┌─────────────────────────────────────────────────┐     │
│  │  SimuladorCeldas                                │     │
│  │  - cell_protocol: CellProtocol                  │     │
│  │  - serial_service: SerialService(protocol)      │     │
│  │  - Actualiza pesos en protocolo                 │     │
│  │  - Muestra feedback de comandos en UI           │     │
│  └──────────────┬──────────────────────────────────┘     │
│                 │                                        │
└─────────────────┼────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────────────┐
│ Serial   │ │ Weight   │ │ CellProtocol     │
│ Service  │ │ Service  │ │ - Tabla celdas   │
│ - Lee    │ │ - Calcs  │ │ - parsea cmd     │
│ - cmd?   │ │          │ │ - genera rta     │
│ - parse  │ │          │ │ - ADR, TDD       │
└──────────┘ └──────────┘ └──────────────────┘
```

### Flujo de Procesamiento de Comandos

```
1. Sistema externo envia comando por puerto serial
         │
         ▼
2. SerialService._read_loop() recibe la linea
         │
         ▼
3. Se verifica si la linea es un comando:
   - CellProtocol.is_command(line)
         │
         ├── SI: Es comando ───────────────────────────┐
         │                                             │
         ▼                                             ▼
4a. CellProtocol.handle_command()              4b. _parse_line() extrae
    - Identifica tipo (MSV?, IDN?, ADR, TDD)       pesos (JSON/CSV/num)
    - Busca celda por direccion o serial         - Actualiza UI con datos
    - Genera respuesta formateada                   reales
         │
         ▼
5. SerialService.send_data(respuesta)
   - Envia respuesta al puerto serial
   - Notifica a UI via callback
         │
         ▼
6. app.py muestra feedback:
   "CMD: S01;MSV? => -0010236"
```

### Actualizacion de Pesos en las Celdas Virtuales

Los pesos de las celdas virtuales se actualizan automaticamente desde
dos fuentes:

|    Fuente    |                          Metodo                                         |                  Cuando                   |
|--------------|-------------------------------------------------------------------------|-------------------------------------------|
| Simulacion   | `_calcular_y_actualizar()` → `cell_protocol.update_all_weights()`       | Al arrastrar la bola o cambiar peso total |
| Datos reales | `_actualizar_con_datos_reales()` → `cell_protocol.update_all_weights()` | Al recibir datos del puerto serial        |

## Archivos Modificados/Creados

### Nuevo archivo

- `src/backend/services/cell_protocol.py` - Logica completa del protocolo:
  - Clase `VirtualCell`: Representa una celda con direccion, serial y peso
  - Clase `CellProtocol`: Gestiona la tabla de celdas y procesa comandos
  - Expresiones regulares para validar cada tipo de comando
  - Generacion de respuestas con formato compatible HBM

### Archivos modificados

- `src/backend/services/serial_service.py`:
  - `__init__()` acepta parametro `protocol` (instancia de CellProtocol)
  - `_read_loop()` verifica si cada linea es comando antes de parsear pesos
  - Nuevo callback `on_command_response` para feedback en UI

- `app.py`:
  - Importa y crea `CellProtocol`
  - Pasa protocolo a `SerialService`
  - Actualiza pesos en protocolo desde simulacion y datos reales
  - Muestra ultimo comando/respuesta en la interfaz
  - Nuevos metodos: `_on_protocol_command()`, `_mostrar_comando_protocolo()`

## Pruebas

Para probar el protocolo manualmente:

1. Conecte un emulador de puerto serial (ej: com0com) o un cable null-modem
2. Configure dos aplicaciones: el simulador y un terminal serial
3. En el terminal serial, envie comandos terminados con `\n`

### Escenario de prueba 1: Consulta de peso

```
Enviar:    S01;MSV?
Recibir:   0000312            (depende de la posicion de la bola)
```

### Escenario de prueba 2: Identificacion

```
Enviar:    S02;IDN?
Recibir:   HBM,C16iC3/40t     ,M64702 ,P52
```

### Escenario de prueba 3: Reasignacion de direccion

```
Enviar:    ADR5,"M64703"
Recibir:   OK M64703 -> S05
Enviar:    S05;IDN?
Recibir:   HBM,C16iC3/40t     ,M64703 ,P52
```

### Escenario de prueba 4: Error - direccion inexistente

```
Enviar:    S99;MSV?
Recibir:   ?S00
```
