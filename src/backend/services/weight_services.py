import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from config.constans import SQUARE_SIZE, MAX_WEIGHT, MIN_WEIGHT, CORNERS


class WeightService:
    """Servicio para calculos de distribucion de pesos"""

    def __init__(self):
        """Inicializa el servicio con el tamano del cuadrado"""
        self.square_size = SQUARE_SIZE

    def calculate_corner_weights(self, position_x, position_y, total_weight=100):
        """
        Calcula los pesos en las 4 esquinas usando interpolacion bilineal inversa

        La interpolacion bilineal asigna peso a cada esquina de forma inversamente
        proporcional a la distancia desde la posicion de la bola.

        Args:
            position_x: Posicion X de la bola (0 - square_size)
            position_y: Posicion Y de la bola (0 - square_size)
            total_weight: Peso total en kg

        Returns:
            dict: Pesos en cada esquina (top-left, top-right, bottom-left, bottom-right)
        """
        # Normalizar coordenadas a rango [0, 1]
        nx = position_x / self.square_size
        ny = position_y / self.square_size

        # Interpolacion bilineal inversa
        # El peso en cada esquina es inversamente proporcional a la distancia
        top_left = (1 - nx) * (1 - ny)       # Peso en esquina superior izquierda
        top_right = nx * (1 - ny)             # Peso en esquina superior derecha
        bottom_left = (1 - nx) * ny           # Peso en esquina inferior izquierda
        bottom_right = nx * ny                # Peso en esquina inferior derecha

        # Normalizar para que la suma sea 1
        total = top_left + top_right + bottom_left + bottom_right

        if total > 0:
            top_left /= total
            top_right /= total
            bottom_left /= total
            bottom_right /= total

        # Aplicar peso total y redondear a 2 decimales
        return {
            'top-left': round(top_left * total_weight, 2),
            'top-right': round(top_right * total_weight, 2),
            'bottom-left': round(bottom_left * total_weight, 2),
            'bottom-right': round(bottom_right * total_weight, 2)
        }

    def get_weight_color(self, weight, total_weight=MAX_WEIGHT):
        """
        Determina el color segun el porcentaje de peso
        Verde: menos del 33%, Amarillo: entre 33% y 66%, Rojo: mas del 66%
        """
        percentage = (weight / total_weight) * 100

        if percentage < 33:
            return '#4CAF50'  # Verde - peso bajo
        elif percentage < 66:
            return '#FFC107'  # Amarillo - peso medio
        else:
            return '#F44336'  # Rojo - peso alto

    def validate_position(self, x, y):
        """Valida que la posicion este dentro del cuadrado"""
        return 0 <= x <= self.square_size and 0 <= y <= self.square_size
