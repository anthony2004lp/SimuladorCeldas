# Requerimientos del Simulador de Distribucion de Pesos

## Descripcion General
Simulador interactivo de escritorio que muestra como se distribuye un peso total
entre 4 sensores ubicados en las esquinas de un area cuadrada, utilizando
interpolacion bilineal inversa. El usuario puede arrastrar una bola con el mouse
(modo simulacion) o conectar una balanza real via puerto serial (modo datos reales)
para visualizar las lecturas de las celdas de carga en tiempo real.

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

### RF03 - Control de Peso Total
- El usuario debe poder ingresar el peso total en kg mediante un control numerico (Spinbox).
- El rango permitido es de 0 a 500 kg, con pasos de 10 kg.
- El valor por defecto es 100 kg.
- Los calculos se actualizan automaticamente al cambiar el valor.

### RF04 - Calculo de Distribucion
- El sistema debe calcular como se distribuye el peso total entre las 4 esquinas.
- El calculo debe usar interpolacion bilineal inversa: a mayor proximidad a una esquina, mayor peso en esa esquina.
- La suma de los pesos de las 4 esquinas debe ser igual al peso total.

### RF05 - Visualizacion de Resultados
- Mostrar el peso calculado para cada esquina en kg con 2 decimales.
- Mostrar cada peso con un color semaforo segun su proporcion respecto al total:
  - Verde (< 33%): peso bajo
  - Amarillo (33-66%): peso medio
  - Rojo (> 66%): peso alto

### RF06 - Informacion de Posicion
- Mostrar las coordenadas (X, Y) actuales de la bola dentro del area.
- Las coordenadas se muestran en pixeles (0-400).

### RF07 - Reinicio de Posicion
- Debe existir un boton para reiniciar la posicion de la bola al centro del cuadrado.

### RF08 - Conexion Serial
- El usuario debe poder escanear los puertos serial disponibles del sistema.
- El usuario debe poder seleccionar un puerto y velocidad de baudios para conectar.
- Debe existir un boton para conectar/desconectar del puerto serial.
- Debe mostrar el estado de la conexion en tiempo real.
- Al conectar, la aplicacion debe cambiar automaticamente a modo "Datos reales".

### RF09 - Lectura de Datos Seriales
- El sistema debe leer datos del puerto serial en segundo plano sin bloquear la interfaz.
- Debe soportar formato JSON, CSV y extraccion de numeros libres.
- Los pesos recibidos deben mostrarse en la interfaz en tiempo real.
- La posicion de la bola debe calcularse a partir de los 4 pesos reales.

### RF10 - Modos de Operacion
- **Modo Simulacion**: la bola se arrastra con el mouse, los pesos se calculan por interpolacion.
- **Modo Datos Reales**: los pesos provienen del puerto serial, la bola refleja la posicion real.
- La aplicacion debe indicar visualmente que modo esta activo.
- En modo datos reales, se debe deshabilitar el arrastre de la bola.

## Requerimientos No Funcionales

### RNF01 - Tecnologia
- Interfaz grafica: tkinter (biblioteca estandar de Python, sin dependencias externas).
- Logica de negocio: Python puro con NumPy para operaciones numericas.
- Comunicacion serial: pyserial 3.5.
- Comunicacion: llamadas directas a metodos (no hay red, es aplicacion de escritorio).

### RNF02 - Rendimiento
- Actualizacion en tiempo real mientras se arrastra la bola o se reciben datos seriales.
- Lectura serial en hilo separado para no bloquear la interfaz.

### RNF03 - Compatibilidad
- Compatible con Windows, Linux y macOS (al ser Python puro con tkinter).
- No requiere conexion a internet ni servidor web.
- Soporta cualquier balanza que envie datos por puerto serial en formato texto.

### RNF04 - Configuracion
- Constantes del sistema (tamano, pesos maximos/minimos, colores) en `config/constans.py`.
- Parametros de simulacion y serial en `config/settings.json`.

### RNF05 - Dependencias
- Python 3.8 o superior.
- NumPy 1.26.
- pyserial 3.5.
- tkinter (incluido con Python).
