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

| Direccion | Numero de Serie | Esquina Asociada |
|-----------|-----------------|-------------------|
| S00       | M64701          | Superior Izquierda (TL) |
| S01       | M64702          | Superior Derecha (TR)   |
| S02       | M64703          | Inferior Izquierda (BL) |
| S03       | M64704          | Inferior Derecha (BR)   |

Las direcciones pueden reasignarse mediante el comando `ADR`.

## Formato de Comandos

El protocolo soporta **dos formatos** de comandos:

### Formato Multi-Linea (nuevo)

Los comandos se envian en **tres mensajes consecutivos**:

```
S98                     # 1) Llamada a grupo (todas las celdas, no responden)
MSV?                    # 2) Comando a ejecutar (case insensitive)
S02                     # 3) Celda destino a consultar
```

Cada mensaje debe terminar con salto de linea (`\n`, `\r\n` o `\r`).
Los pasos intermedios (S98 y el comando) **no generan respuesta**,
solo el ultimo paso (la celda destino) devuelve el resultado.

### Formato Clasico (una linea)

```
Sxx;MSV?;
Sxx;IDN?;
ADRx,"SERIAL";
Sxx;TDD1;
```

Ambos formatos coexisten y pueden usarse indistintamente.

## Comandos Soportados

### 1. Consultar Peso - `MSV?`

Solicita el peso actual de la celda especificada.

**Formato multi-linea:**
```
S98
MSV?  (o msv?)
S01
```

**Formato clasico:**
```
S01;MSV?;
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

### 2. Consultar Identificacion - `IDN?`

Solicita el modelo, numero de serie y version de firmware de la celda.

**Formato multi-linea:**
```
S98
IDN?  (o idn?)
S02
```

**Formato clasico:**
```
S02;IDN?;
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

**Implementacion:** `VirtualCell.get_id_response()` en `cell_protocol.py:59`

### 3. Asignar Direccion - `ADR`

Asigna una nueva direccion a una celda identificada por su numero de serie.
Solo disponible en formato clasico (una linea).

**Formato:**
```
ADR<nueva_direccion>,"<numero_serie>"
```

**Ejemplo:**
```
ADR2,"M64702"
```

Asigna la direccion `S02` a la celda con numero de serie `M64702`.
Si la direccion ya estaba ocupada, las celdas intercambian direcciones.

**Respuesta:**
```
OK M64702 -> S02
```

- Si el numero de serie no existe: `?M64702`

**Nota:** El cambio es inmediato en memoria. Para hacerlo permanente, debe
enviarse el comando `TDD1` a la celda correspondiente.

**Implementacion:** `CellProtocol.handle_command()` en `cell_protocol.py:192`

### 4. Guardar en EEPROM - `TDD1`

Guarda la configuracion actual (direccion asignada) en la memoria permanente
de la celda.

**Formato multi-linea:**
```
S98
TDD1  (o tdd1)
S02
```

**Formato clasico:**
```
S02;TDD1;
```

**Respuesta:**
```
OK
```

- Si la direccion no existe: `?S00`

**Nota:** En el simulador, este comando es una operacion virtual (no persiste
entre sesiones). Al reiniciar la aplicacion, las celdas vuelven a sus
direcciones por defecto.

## Casos de Uso

### Ejemplo 1: Consultar peso de todas las celdas (multi-linea)

```
S98
MSV?
S00
 0000766
S98
MSV?
S01
 0000109
S98
MSV?
S02
 0000109
S98
MSV?
S03
 0000016
```

### Ejemplo 2: Consultar con minusculas (multi-linea)

```
S98
msv?
S01
 0000109
```

### Ejemplo 3: Identificacion de celda (multi-linea)

```
S98
idn?
S02
HBM,C16iC3/40t     ,M64703 ,P52
```

### Ejemplo 4: Cambiar direccion y verificar (formato clasico)

```
ADR2,"M64702"
OK M64702 -> S02
S02;IDN?;
HBM,C16iC3/40t     ,M64702 ,P52
S02;TDD1;
OK
```

### Ejemplo 5: Error - celda inexistente

```
S98
msv?
S99
?S00
```

## Arquitectura de la Implementacion

### Maquina de Estados (Protocolo Multi-Linea)

```
                S98
    ┌──────────────────────────┐
    │                          │
    ▼           MSV?/IDN?/TDD1 │          Sxx
  IDLE ──────────────────► GROUP ───────────► CMD ──────────► IDLE
  (0)     S98 recibido    (1)    comando     (2)   ejecutar   (0)
                                  recibido    │     comando
                                              │
                                              │ (error)
                                              ▼
                                            IDLE (0)
```

### Flujo de Procesamiento

```
1. Sistema externo envia 3 lineas por puerto serial
         │
         ▼
2. SerialService._read_loop() recibe cada linea
         │
         ▼
3. CellProtocol.is_command(line)
         │
         ├── S98 ──► handle_command("S98") ──► state=GROUP, no response
         ├── MSV? ─► handle_command("MSV?") ─► state=CMD, no response
         ├── Sxx ──► handle_command("Sxx") ──► ejecuta, envia respuesta
         │
         ▼
4. Respuesta enviada de vuelta al puerto serial
```

## Archivos

| Archivo | Proposito |
|---------|-----------|
| `src/backend/services/cell_protocol.py` | Logica completa del protocolo |
| `src/backend/services/serial_service.py` | Integracion del protocolo en lectura serial |
| `app.py` | Feedback visual de comandos en la UI |

## Pruebas

### Escenario 1: Consulta de peso (multi-linea, Hercules)

Configurar Hercules para enviar sin salto de linea automatico,
y enviar estas 3 lineas una por una:

```
S98
msv?
S01
```

Respuesta esperada: ` 0000312` (depende de la posicion de la bola)

### Escenario 2: Consulta de peso (formato clasico)

Enviar en una sola linea:

```
S01;MSV?;
```

Respuesta esperada: ` 0000312`

### Escenario 3: Las 3 lineas juntas

Si el sistema externo envia las 3 lineas en un solo bloque:

```
S98
msv?
S01
```

El programa las procesa en orden y responde solo al final con el peso.

### Escenario 4: Comando invalido

```
S98
INVALIDO
```

Respuesta: `?` (error, transaccion cancelada)
