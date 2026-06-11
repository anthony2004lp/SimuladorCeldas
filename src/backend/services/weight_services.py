import sys
import os
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from config.constans import SQUARE_SIZE, MAX_WEIGHT, MIN_WEIGHT, CORNERS


class WeightService:
    """Servicio para calculos de distribucion de pesos con comportamiento realista"""

    def __init__(self):
        self.square_size = SQUARE_SIZE

        # Offset fijo por celda (simula error de cero de cada sensor)
        # Antes de tarar, algunas celdas pueden mostrar valores negativos
        self._corner_offsets = {
            'top-left': round(random.uniform(-130, -120), 2),
            'top-right': round(random.uniform(0, 9), 2),
            'bottom-left': round(random.uniform(0, 9), 2),
            'bottom-right': round(random.uniform(-130, -120), 2)
        }

        # Tara: captura el offset como linea base y lo resta de lecturas futuras
        self._tare_baseline = None

        # Ruido gaussiano: desviacion estandar en kg (simula ruido electrico del sensor)
        self._noise_std = 2.0

    # ------------------------------------------------------------------ #
    # Tara
    # ------------------------------------------------------------------ #

    def tare(self):
        """Captura los offsets actuales como linea base para tara

        Una vez tarado, los valores negativos desaparecen y el sistema
        mide solo el peso aplicado + ruido, como una balanza real.
        """
        self._tare_baseline = {
            corner: offset for corner, offset in self._corner_offsets.items()
        }

    def clear_tare(self):
        """Limpia la tara, restaurando los offsets originales"""
        self._tare_baseline = None

    @property
    def is_tared(self):
        """Indica si la tara esta activa"""
        return self._tare_baseline is not None

    # ------------------------------------------------------------------ #
    # Ruido
    # ------------------------------------------------------------------ #

    def _get_noise(self):
        """Genera ruido gaussiano con media 0 y std _noise_std

        Simula el ruido electrico y termico inherente a las celdas de carga.
        """
        return round(random.gauss(0, self._noise_std), 2)

    # ------------------------------------------------------------------ #
    # Calculo de pesos
    # ------------------------------------------------------------------ #

    def calculate_corner_weights(self, position_x, position_y, total_weight=100):
        """Calcula los pesos en las 4 esquinas usando interpolacion bilineal inversa

        El flujo realista es:
        1. Distribucion ideal del peso aplicado segun posicion (bilineal)
        2. Se agrega el offset fijo de cada celda (error de cero del sensor)
        3. Se agrega ruido gaussiano (simula ruido de medicion)
        4. Si la tara esta activa, se resta la linea base capturada

        Args:
            position_x: Posicion X de la bola (0 - square_size)
            position_y: Posicion Y de la bola (0 - square_size)
            total_weight: Peso aplicado sobre la plataforma en kg

        Returns:
            dict: Pesos en cada esquina (top-left, top-right, bottom-left, bottom-right)
        """
        # Normalizar coordenadas a rango [0, 1]
        nx = position_x / self.square_size
        ny = position_y / self.square_size

        # Interpolacion bilineal inversa
        raw_tl = (1 - nx) * (1 - ny)
        raw_tr = nx * (1 - ny)
        raw_bl = (1 - nx) * ny
        raw_br = nx * ny

        # Normalizar para que la suma sea 1
        total = raw_tl + raw_tr + raw_bl + raw_br
        if total > 0:
            raw_tl /= total
            raw_tr /= total
            raw_bl /= total
            raw_br /= total

        # Peso ideal en cada celda (distribucion del peso aplicado)
        base = {
            'top-left': raw_tl * total_weight,
            'top-right': raw_tr * total_weight,
            'bottom-left': raw_bl * total_weight,
            'bottom-right': raw_br * total_weight,
        }

        result = {}
        for corner in ['top-left', 'top-right', 'bottom-left', 'bottom-right']:
            # Peso ideal + offset fijo del sensor + ruido de medicion
            value = base[corner] + self._corner_offsets[corner] + self._get_noise()

            # Si la tara esta activa, restar la linea base (offset capturado)
            if self._tare_baseline is not None:
                value -= self._tare_baseline[corner]

            result[corner] = round(value, 2)

        return result

    def get_measured_total(self, corner_weights):
        """Calcula el peso total medido como suma de las 4 celdas

        En una balanza real, el peso total es la suma de las celdas,
        NO un valor independiente. Diferencia clave con la version anterior.
        """
        return round(sum(corner_weights.values()), 2)

    def get_weight_color(self, weight, total_weight=MAX_WEIGHT):
        """Determina el color segun el porcentaje de peso

        Usa el total medido (suma de celdas) como referencia para el porcentaje,
        no el peso aplicado. Esto refleja el comportamiento real del instrumento.
        """
        if total_weight == 0:
            return '#4CAF50'
        percentage = (weight / total_weight) * 100

        if percentage < 33:
            return '#4CAF50'
        elif percentage < 66:
            return "#006AFF"
        else:
            return '#F44336'

    def validate_position(self, x, y):
        """Valida que la posicion este dentro del cuadrado"""
        return 0 <= x <= self.square_size and 0 <= y <= self.square_size
