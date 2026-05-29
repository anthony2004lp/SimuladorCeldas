import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.append(os.path.dirname(__file__))

from src.backend.services.weight_services import WeightService
from src.backend.models.weight_models import WeightDistribution
from config.constans import SQUARE_SIZE, MAX_WEIGHT, MIN_WEIGHT, COLORS, CORNERS


class SimuladorCeldas:
    """Clase principal de la aplicacion de escritorio"""

    def __init__(self, root):
        """
        Inicializa la aplicacion de escritorio
        Args:
            root: Ventana principal de tkinter
        """
        self.root = root
        root.title("Simulador de Distribucion de Pesos")
        root.resizable(False, False)

        # Inicializar servicios y modelos
        self.weight_service = WeightService()
        self.distribution = WeightDistribution()

        # Estado de la simulacion
        self.ball_x = SQUARE_SIZE // 2
        self.ball_y = SQUARE_SIZE // 2
        self.is_dragging = False
        self.total_weight = tk.DoubleVar(value=100)

        # Construir la interfaz grafica
        self._crear_interfaz()

        # Realizar el primer calculo
        self._calcular_y_actualizar()

    def _crear_interfaz(self):
        """
        Crea todos los elementos visuales de la aplicacion
        """
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.grid(row=0, column=0)

        # Titulo
        title_label = ttk.Label(
            main_frame,
            text="Simulador de Distribucion de Pesos",
            font=("Segoe UI", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Canvas para dibujar la simulacion
        self.canvas = tk.Canvas(
            main_frame,
            width=SQUARE_SIZE,
            height=SQUARE_SIZE,
            bg="#f9f9f9",
            highlightthickness=2,
            highlightbackground="#333"
        )
        self.canvas.grid(row=1, column=0, padx=(0, 20))

        # Panel de control
        control_frame = ttk.LabelFrame(main_frame, text="Control", padding=15)
        control_frame.grid(row=1, column=1, sticky="n")

        # Entrada de peso total
        ttk.Label(control_frame, text="Peso Total (kg):", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        weight_spinbox = ttk.Spinbox(
            control_frame,
            from_=MIN_WEIGHT,
            to=500,
            increment=10,
            textvariable=self.total_weight,
            width=15,
            font=("Segoe UI", 10)
        )
        weight_spinbox.grid(row=1, column=0, pady=(0, 20))
        weight_spinbox.bind("<KeyRelease>", lambda e: self._calcular_y_actualizar())
        self.total_weight.trace_add("write", lambda *_: self._calcular_y_actualizar())

        # Mostrar posicion
        ttk.Label(control_frame, text="Posicion:", font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        self.pos_label = ttk.Label(
            control_frame,
            text=f"({self.ball_x}, {self.ball_y})",
            font=("Segoe UI", 12),
            foreground="#667eea"
        )
        self.pos_label.grid(row=3, column=0, sticky="w", pady=(0, 20))

        # Boton para reiniciar
        reset_btn = ttk.Button(
            control_frame,
            text="Reiniciar posicion",
            command=self._reiniciar_posicion
        )
        reset_btn.grid(row=4, column=0, sticky="ew")

        # Panel de resultados (pesos en esquinas)
        results_frame = ttk.LabelFrame(main_frame, text="Distribucion de Pesos", padding=15)
        results_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0), sticky="ew")

        # Crear labels para cada esquina
        self.weight_labels = {}
        corner_names = {
            "top-left": "Superior Izquierda",
            "top-right": "Superior Derecha",
            "bottom-left": "Inferior Izquierda",
            "bottom-right": "Inferior Derecha"
        }

        for i, (corner_key, corner_display) in enumerate(corner_names.items()):
            frame = ttk.Frame(results_frame)
            frame.grid(row=i // 2, column=i % 2, padx=10, pady=5, sticky="ew")
            results_frame.columnconfigure(i % 2, weight=1)

            ttk.Label(
                frame,
                text=f"Esquina {corner_display}:",
                font=("Segoe UI", 9)
            ).pack(side="left")

            weight_label = ttk.Label(
                frame,
                text="0 kg",
                font=("Segoe UI", 11, "bold")
            )
            weight_label.pack(side="right")
            self.weight_labels[corner_key] = weight_label

        # Vincular eventos del mouse al canvas
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

        # Dibujar el estado inicial
        self._dibujar_canvas()

    def _dibujar_canvas(self):
        """
        Dibuja el cuadrado, la cuadricula, las marcas de esquinas y la bola
        """
        self.canvas.delete("all")

        # Dibujar cuadricula
        for i in range(5):
            pos = i * 100
            self.canvas.create_line(pos, 0, pos, SQUARE_SIZE, fill="#ddd", width=1)
            self.canvas.create_line(0, pos, SQUARE_SIZE, pos, fill="#ddd", width=1)

        # Dibujar marcas de esquinas
        corner_positions = {
            "TL": (10, 15),
            "TR": (SQUARE_SIZE - 25, 15),
            "BL": (10, SQUARE_SIZE - 10),
            "BR": (SQUARE_SIZE - 25, SQUARE_SIZE - 10)
        }
        for label, (cx, cy) in corner_positions.items():
            self.canvas.create_text(cx, cy, text=label, fill="#666", font=("Arial", 9))

        # Dibujar bola (circulo rojo)
        ball_radius = 15
        self.canvas.create_oval(
            self.ball_x - ball_radius,
            self.ball_y - ball_radius,
            self.ball_x + ball_radius,
            self.ball_y + ball_radius,
            fill="#F44336",
            outline="white",
            width=2
        )

    def _calcular_y_actualizar(self):
        """
        Calcula la distribucion de pesos y actualiza la interfaz
        """
        weight = self.total_weight.get()
        if weight < MIN_WEIGHT:
            weight = MIN_WEIGHT
            self.total_weight.set(MIN_WEIGHT)

        # Calcular pesos en cada esquina
        corner_weights = self.weight_service.calculate_corner_weights(
            self.ball_x, self.ball_y, weight
        )

        # Actualizar modelo
        self.distribution.total_weight = weight
        self.distribution.position_x = self.ball_x
        self.distribution.position_y = self.ball_y
        self.distribution.corner_weights = corner_weights

        # Actualizar labels de pesos con colores
        for corner, weight_value in corner_weights.items():
            color = self.weight_service.get_weight_color(weight_value, weight)
            self.weight_labels[corner].config(
                text=f"{weight_value} kg",
                foreground=color
            )

        # Actualizar label de posicion
        self.pos_label.config(text=f"({int(self.ball_x)}, {int(self.ball_y)})")

    def _reiniciar_posicion(self):
        """
        Reinicia la posicion de la bola al centro del cuadrado
        """
        self.ball_x = SQUARE_SIZE // 2
        self.ball_y = SQUARE_SIZE // 2
        self._dibujar_canvas()
        self._calcular_y_actualizar()

    def _obtener_posicion_mouse(self, event):
        """
        Convierte coordenadas del evento del mouse a coordenadas del canvas
        Args:
            event: Evento del mouse de tkinter
        Returns:
            tuple: (x, y) coordenadas dentro del cuadrado
        """
        x = max(15, min(SQUARE_SIZE - 15, event.x))
        y = max(15, min(SQUARE_SIZE - 15, event.y))
        return x, y

    def _on_mouse_down(self, event):
        """
        Maneja el evento de presionar el boton del mouse
        """
        self.is_dragging = True
        self.ball_x, self.ball_y = self._obtener_posicion_mouse(event)
        self._dibujar_canvas()
        self._calcular_y_actualizar()

    def _on_mouse_move(self, event):
        """
        Maneja el evento de arrastrar el mouse
        """
        if self.is_dragging:
            self.ball_x, self.ball_y = self._obtener_posicion_mouse(event)
            self._dibujar_canvas()
            self._calcular_y_actualizar()

    def _on_mouse_up(self, event):
        """
        Maneja el evento de soltar el boton del mouse
        """
        self.is_dragging = False


def main():
    """Punto de entrada principal de la aplicacion"""
    root = tk.Tk()
    app = SimuladorCeldas(root)
    root.mainloop()


if __name__ == "__main__":
    main()
