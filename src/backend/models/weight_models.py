class WeightDistribution:
    """Modelo de distribucion de pesos en las 4 esquinas"""

    def __init__(self, total_weight=0, position_x=0, position_y=0, square_size=400):
        """
        Inicializa el modelo de distribucion de pesos
        Args:
            total_weight: Peso total en kg
            position_x: Posicion X de la bola
            position_y: Posicion Y de la bola
            square_size: Tamano del cuadrado en pixeles
        """
        self.total_weight = total_weight
        self.position_x = position_x
        self.position_y = position_y
        self.square_size = square_size
        self.corner_weights = {
            'S00': 0,        # Peso en esquina superior izquierda
            'S01': 0,       # Peso en esquina superior derecha
            'S02': 0,     # Peso en esquina inferior izquierda
            'S03': 0     # Peso en esquina inferior derecha
        }

    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'total_weight': self.total_weight,
            'position': {
                'x': self.position_x,
                'y': self.position_y
            },
            'corner_weights': self.corner_weights
        }

    def update_position(self, x, y):
        """
        Actualiza la posicion de la bola asegurando que este dentro del cuadrado
        Args:
            x: Nueva posicion X
            y: Nueva posicion Y
        """
        self.position_x = max(0, min(x, self.square_size))
        self.position_y = max(0, min(y, self.square_size))
