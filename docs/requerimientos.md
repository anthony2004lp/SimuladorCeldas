# Requerimientos del Simulador de Distribucion de Pesos

## Descripcion General
Simulador interactivo de escritorio que muestra como se distribuye un peso
aplicado entre 4 sensores ubicados en las esquinas de un area cuadrada, utilizando
interpolacion bilineal inversa con ruido gaussiano y compensacion de tara.
El usuario puede arrastrar una bola con el mouse (modo simulacion) o conectar
una balanza real via puerto serial (modo datos reales) para visualizar las
lecturas de las celdas de carga en tiempo real.

## Requerimientos Funcionales

### RF01 - Visualizacion del Area de Simulacion
- Mostrar un cuadrado de 400x400 pixeles que representa el area de simulacion.
- Dibujar una cuadricula divisoria (5 lineas horizontales y 5 verticales).
- Mostrar bordes delimitadores resaltados.
- Mostrar etiquetas en las 4 esquinas (TL, TR, BL, BR).

### RF02 - Interaccion con la Bola
- El usuario debe poder hacer clic y arrastrar una bola roja dentro del cuadrado.
- La bola no debe salir de los limites del area de simulacion (margen de 15px del borde).
- La posicion de la bola debe actualizarse en tiempo real mientras se arrastra.
- La visualizacion y los calculos deben actualizarse al mismo tiempo.

### RF03 - Control de Peso Aplicado
- El usuario debe poder ingresar el peso aplicado (lo que se coloca sobre la plataforma) en kg mediante un control numerico (Spinbox).
- El rango permitido es de 0 a 160.000 kg, con incremento de 1.000 kg.
- El valor por defecto es 100 kg.
- Los calculos se actualizan automaticamente al cambiar el valor.

### RF04 - Calculo de Distribucion con Ruido
- El sistema debe calcular como se distribuye el peso aplicado entre las 4 esquinas.
- El calculo debe usar interpolacion bilineal inversa: a mayor proximidad a una esquina, mayor peso en esa esquina.
- Cada celda debe tener un **offset fijo** generado al inicio de la sesion (simula error de cero del sensor).
- Cada lectura debe incluir **ruido gaussiano** con media 0 y desviacion estandar 2 kg (simula ruido electrico/termico).
- La suma de los pesos de las 4 celdas (total medido) debe calcularse como la suma real de las lecturas individuales, no como un valor independiente.

### RF05 - Sistema de Tara
- Debe existir un boton **Tara** que al presionarse capture los offsets actuales como linea base.
- Con la tara activa, los offsets deben restarse de todas las lecturas futuras, mostrando solo el peso aplicado + ruido.
- Al presionar el boton nuevamente, la tara debe desactivarse y los offsets deben restaurarse.
- Debe existir un indicador visual que muestre si la tara esta activa o no.
- La tara debe estar deshabilitada en modo datos reales.

### RF06 - Visualizacion de Resultados
- Mostrar el peso calculado para cada esquina en kg con 2 decimales.
- Mostrar cada peso con un color semaforo segun su proporcion respecto al **total medido** (suma real de las 4 celdas):
  - Verde (< 33%): peso bajo
  - Azul (33-66%): peso medio
  - Rojo (> 66%): peso alto
- Mostrar el **Total medido** como la suma real de las 4 celdas, separado visualmente de los pesos individuales.

### RF07 - Informacion de Posicion
- Mostrar las coordenadas (X, Y) actuales de la bola dentro del area.
- Las coordenadas se muestran en pixeles (0-400).

### RF08 - Reinicio de Peso a Cero
- Debe existir un boton para poner el peso aplicado en 0 kg.
- Al presionarlo, el control de peso aplicado debe mostrar 0 y recalcular la distribucion.

### RF09 - Botones "Llevar" a Esquina
- Debe existir un boton "Llevar" junto a cada esquina en el panel de resultados.
- Al presionarlo, la bola debe moverse a esa esquina y recalcularse la distribucion.

### RF10 - Reinicio de Posicion
- Debe existir un boton para reiniciar la posicion de la bola al centro del cuadrado.

### RF11 - Conexion Serial
- El usuario debe poder escanear los puertos serial disponibles del sistema.
- El usuario debe poder seleccionar un puerto y velocidad de baudios para conectar.
- Debe existir un boton para conectar/desconectar del puerto serial.
- Debe mostrar el estado de la conexion en tiempo real.
- Al conectar, la aplicacion debe cambiar automaticamente a modo "Datos reales".

### RF12 - Lectura de Datos Seriales
- El sistema debe leer datos del puerto serial en segundo plano sin bloquear la interfaz.
- Debe soportar formato JSON, CSV y extraccion de numeros libres.
- Los pesos recibidos deben mostrarse en la interfaz en tiempo real.
- La posicion de la bola debe calcularse a partir de los 4 pesos reales.
- Debe detectar y responder automaticamente a comandos del protocolo HBM C16iC3.

### RF13 - Protocolo HBM C16iC3
- El sistema debe simular 4 celdas de carga virtuales compatibles con HBM C16iC3.
- Debe soportar los comandos: `MSV?` (consultar peso), `IDN?` (identificar), `ADR` (reasignar direccion), `TDD1` (guardar en EEPROM).
- Debe soportar dos formatos: multi-linea (S98 -> comando -> Sxx) y clasico (Sxx;MSV?;).
- Las celdas virtuales deben tener direcciones S00-S03 y numeros de serie M64701-M64704.
- Los pesos deben actualizarse en tiempo real segun la simulacion o datos seriales.

### RF14 - Modos de Operacion
- **Modo Simulacion**: la bola se arrastra con el mouse, los pesos se calculan por interpolacion con ruido y offsets compensables via tara.
- **Modo Datos Reales**: los pesos provienen del puerto serial, la bola refleja la posicion real.
- La aplicacion debe indicar visualmente que modo esta activo.
- En modo datos reales, se debe deshabilitar el arrastre de la bola y los botones de simulacion (Tara, Llevar, Reiniciar).

### RF15 - Reenvio de Datos
- Debe existir un checkbox para habilitar el reenvio de datos de peso a otro programa a traves del puerto serial.
- Cuando esta activo, los valores de las 4 celdas se envian en formato CSV por el puerto conectado.

## Requerimientos No Funcionales

### RNF01 - Tecnologia
- Interfaz grafica: tkinter (biblioteca estandar de Python, sin dependencias externas).
- Logica de negocio: Python puro con modulo `random` para ruido gaussiano y generacion de offsets.
- Comunicacion serial: pyserial 3.5.
- Comunicacion: llamadas directas a metodos (no hay red, es aplicacion de escritorio).

### RNF02 - Rendimiento
- Actualizacion en tiempo real mientras se arrastra la bola o se reciben datos seriales.
- Lectura serial en hilo separado para no bloquear la interfaz.
- El ruido gaussiano debe generarse sin depender de NumPy (usa `random.gauss` de la biblioteca estandar).

### RNF03 - Compatibilidad
- Compatible con Windows, Linux y macOS (al ser Python puro con tkinter).
- No requiere conexion a internet ni servidor web.
- Soporta cualquier balanza que envie datos por puerto serial en formato texto.

### RNF04 - Configuracion
- Constantes del sistema (tamano, pesos maximos/minimos, colores) en `config/constans.py`.
- Parametros de simulacion y serial en `config/settings.json`.

### RNF05 - Dependencias
- Python 3.8 o superior.
- NumPy (opcional, solo como dependencia declarada).
- pyserial 3.5.
- cx_Freeze 8.6.4 (para empaquetado).
- tkinter (incluido con Python).
