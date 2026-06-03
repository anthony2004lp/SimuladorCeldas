# Constantes del sistema
SQUARE_SIZE = 400  # Tamano del cuadrado en pixeles
MAX_WEIGHT = 50000000   # Peso maximo en kg
MIN_WEIGHT = 0     # Peso minimo en kg

# Puntos de las esquinas (coordenadas relativas 0-1)
CORNERS = {
    'top-left': {'x': 0, 'y': 0},      # Esquina superior izquierda
    'top-right': {'x': 1, 'y': 0},     # Esquina superior derecha
    'bottom-left': {'x': 0, 'y': 1},   # Esquina inferior izquierda
    'bottom-right': {'x': 1, 'y': 1}   # Esquina inferior derecha
}

# Colores de visualizacion
COLORS = {
    'light_weight': '#4CAF50',   # Verde - peso bajo
    'medium_weight': "#005EEC",  # Amarillo - peso medio
    'heavy_weight': '#F44336'    # Rojo - peso alto
}
