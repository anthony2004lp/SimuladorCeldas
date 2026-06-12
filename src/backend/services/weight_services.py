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
            'S00': round(random.uniform(-130, -120), 2),
            'S01': round(random.uniform(0, 9), 2),
            'S02': round(random.uniform(0, 9), 2),
            'S03': round(random.uniform(-130, -120), 2)
        }

        # Tara: captura el offset como linea base y lo resta de lecturas futuras
        self._tare_baseline = None

        # Configuracion de ruido realista para las celdas de carga
        self._noise_base_std = 0.5      # Ruido base en kg (siempre presente)
        self._noise_load_factor = 0.003 # 0.3% del peso leido como ruido proporcional
        self._noise_common_std = 0.3    # Ruido comun a todas las celdas (fuente de poder, etc.)

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
    # Ruido realista
    # ------------------------------------------------------------------ #

    def _get_noise(self, cell_weight=0):
        """Genera ruido realista para una celda de carga

        Compuesto por:
        - Ruido base: pequena fluctuacion electrica siempre presente
        - Ruido proporcional: aumenta con el peso medido (0.3% del valor)
        - Ruido comun: afecta a todas las celdas por igual (fuente de poder)

        Args:
            cell_weight: Peso actual en la celda en kg

        Returns:
            float: Ruido total para esta celda
        """
        base = random.gauss(0, self._noise_base_std)
        proportional = random.gauss(0, abs(cell_weight) * self._noise_load_factor)
        return round(base + proportional, 2)

    def _get_common_noise(self):
        """Genera ruido comun que afecta a todas las celdas por igual

        Simula variaciones en la fuente de poder o interferencias
        electromagneticas que afectan a todo el sistema.
        """
        return round(random.gauss(0, self._noise_common_std), 2)

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
            dict: Pesos en cada celda {S00, S01, S02, S03}
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
            'S00': raw_tl * total_weight,
            'S01': raw_tr * total_weight,
            'S02': raw_bl * total_weight,
            'S03': raw_br * total_weight,
        }

        # Ruido comun que afecta a todas las celdas simultaneamente
        common_noise = self._get_common_noise()

        result = {}
        for corner in ['S00', 'S01', 'S02', 'S03']:
            # Peso ideal + offset fijo del sensor + ruido de medicion
            ideal = base[corner]
            cell_noise = self._get_noise(ideal)
            value = ideal + self._corner_offsets[corner] + cell_noise + common_noise

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
