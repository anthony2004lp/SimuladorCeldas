# Requerimientos del Simulador de Distribucion de Pesos

## Descripcion General
Simulador interactivo de escritorio que muestra como se distribuye un peso total
entre 4 sensores ubicados en las esquinas de un area cuadrada, utilizando
interpolacion bilineal inversa. El usuario arrastra una bola con el mouse y ve
en tiempo real como cambian los pesos en cada esquina.

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

## Requerimientos No Funcionales

### RNF01 - Tecnologia
- Interfaz grafica: tkinter (biblioteca estandar de Python, sin dependencias externas).
- Logica de negocio: Python puro con NumPy para operaciones numericas.
- Comunicacion: llamadas directas a metodos (no hay red, es aplicacion de escritorio).

### RNF02 - Rendimiento
- Actualizacion en tiempo real mientras se arrastra la bola.
- Sin latencia perceptible: todo el calculo es local.

### RNF03 - Compatibilidad
- Compatible con Windows, Linux y macOS (al ser Python puro con tkinter).
- No requiere conexion a internet ni servidor web.

### RNF04 - Configuracion
- Constantes del sistema (tamano, pesos maximos/minimos, colores) en `config/constans.py`.
- Parametros de simulacion en `config/settings.json`.

### RNF05 - Dependencias
- Python 3.8 o superior.
- NumPy 1.26 (para operaciones numericas, aunque el calculo principal no lo requiere).
- tkinter (incluido con Python).
