import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.dirname(__file__))

from src.backend.services.weight_services import WeightService
from src.backend.models.weight_models import WeightDistribution
from src.backend.services.serial_service import SerialService
from src.backend.services.cell_protocol import CellProtocol
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
        self.cell_protocol = CellProtocol()  # Protocolo de comunicacion con celdas HBM
        self.serial_service = SerialService(protocol=self.cell_protocol)

        # Estado de la simulacion
        self.ball_x = SQUARE_SIZE // 2
        self.ball_y = SQUARE_SIZE // 2
        self.is_dragging = False
        self.total_weight = tk.DoubleVar(value=100)

        # Estado del modo serial
        self.receiving_data = False  # True = recibiendo datos reales del puerto
        self.serial_port_var = tk.StringVar()
        self.serial_baud_var = tk.IntVar(value=9600)
        self.serial_status_var = tk.StringVar(value="Desconectado")
        self.forward_data_var = tk.BooleanVar(value=False)  # Reenviar datos al otro programa
        self._serial_update_id = None
        self._command_update_id = None  # ID para actualizacion de comando en UI

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
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.grid(row=1, column=0, padx=(0, 20))

        self.canvas = tk.Canvas(
            canvas_frame,
            width=SQUARE_SIZE,
            height=SQUARE_SIZE,
            bg="#f9f9f9",
            highlightthickness=2,
            highlightbackground="#333"
        )
        self.canvas.pack()

        # Modo actual
        self.mode_label = ttk.Label(
            canvas_frame,
            text="Modo: Simulacion",
            font=("Segoe UI", 9, "italic"),
            foreground="#666"
        )
        self.mode_label.pack(anchor="w", pady=(5, 0))

        # Panel lateral derecho
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=1, column=1, sticky="n")

        # Panel de control de simulacion
        control_frame = ttk.LabelFrame(right_panel, text="Control", padding=15)
        control_frame.pack(fill="x", pady=(0, 10))

        # Entrada de peso aplicado (lo que se coloca sobre la plataforma)
        ttk.Label(control_frame, text="Peso aplicado (kg):", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        weight_spinbox = ttk.Spinbox(
            control_frame,
            from_=MIN_WEIGHT,
            to=MAX_WEIGHT,
            increment=10000,
            textvariable=self.total_weight,
            width=15,
            font=("Segoe UI", 10)
        )
        weight_spinbox.grid(row=1, column=0, pady=(0, 5))
        weight_spinbox.bind("<KeyRelease>", lambda e: self._calcular_y_actualizar())
        self.total_weight.trace_add("write", lambda *_: self._calcular_y_actualizar())

        # Boton para poner peso en 0
        reset_weight_btn = ttk.Button(
            control_frame,
            text="Poner peso en 0 kg",
            command=self._reiniciar_peso
        )
        reset_weight_btn.grid(row=2, column=0, sticky="ew", pady=(0, 5))

        # Boton para tarar las celdas (elimina offsets y muestra solo peso aplicado)
        tare_btn = ttk.Button(
            control_frame,
            text="Tara",
            command=self._tare_celdas
        )
        tare_btn.grid(row=3, column=0, sticky="ew", pady=(0, 20))

        # Mostrar posicion
        ttk.Label(control_frame, text="Posicion:", font=("Segoe UI", 10, "bold")).grid(
            row=4, column=0, sticky="w", pady=(0, 5)
        )
        self.pos_label = ttk.Label(
            control_frame,
            text=f"({self.ball_x}, {self.ball_y})",
            font=("Segoe UI", 12),
            foreground="#667eea"
        )
        self.pos_label.grid(row=5, column=0, sticky="w", pady=(0, 20))

        # Estado de la tara
        self.tare_status_label = ttk.Label(
            control_frame,
            text="",
            font=("Segoe UI", 8, "italic"),
            foreground="#999"
        )
        self.tare_status_label.grid(row=6, column=0, sticky="w", pady=(0, 5))

        # Boton para reiniciar
        reset_btn = ttk.Button(
            control_frame,
            text="Reiniciar posicion",
            command=self._reiniciar_posicion
        )
        reset_btn.grid(row=7, column=0, sticky="ew")

        # Panel de conexion serial
        serial_frame = ttk.LabelFrame(right_panel, text="Puerto Serial", padding=15)
        serial_frame.pack(fill="x")

        # Selector de puerto
        ttk.Label(serial_frame, text="Puerto:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.port_combo = ttk.Combobox(
            serial_frame,
            textvariable=self.serial_port_var,
            width=15,
            font=("Segoe UI", 10),
            state="readonly"
        )
        self.port_combo.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        # Boton para escanear puertos
        scan_btn = ttk.Button(
            serial_frame,
            text="Escanear",
            command=self._escanear_puertos,
            width=8
        )
        scan_btn.grid(row=1, column=1, padx=(5, 0), pady=(0, 10))

        # Selector de baudios
        ttk.Label(serial_frame, text="Baudios:", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        baud_combo = ttk.Combobox(
            serial_frame,
            textvariable=self.serial_baud_var,
            values=[1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200],
            width=15,
            font=("Segoe UI", 10),
            state="readonly"
        )
        baud_combo.grid(row=3, column=0, pady=(0, 10), sticky="ew")

        # Boton conectar/desconectar
        self.connect_btn = ttk.Button(
            serial_frame,
            text="Conectar",
            command=self._toggle_serial,
            width=20
        )
        self.connect_btn.grid(row=4, column=0, columnspan=2, pady=(0, 10))

        # Estado de la conexion
        self.status_label = ttk.Label(
            serial_frame,
            textvariable=self.serial_status_var,
            font=("Segoe UI", 9),
            foreground="#999"
        )
        self.status_label.grid(row=5, column=0, columnspan=2)

        # Checkbox para reenviar datos al otro programa
        self.forward_check = ttk.Checkbutton(
            serial_frame,
            text="Reenviar datos a otro programa",
            variable=self.forward_data_var
        )
        self.forward_check.grid(row=6, column=0, columnspan=2, pady=(8, 0))

        # Label para mostrar el ultimo comando/respuesta del protocolo HBM
        self.cmd_label = ttk.Label(
            serial_frame,
            text="",
            font=("Segoe UI", 8),
            foreground="#666"
        )
        self.cmd_label.grid(row=7, column=0, columnspan=2, pady=(5, 0))

        # Panel de resultados (pesos en esquinas)
        results_frame = ttk.LabelFrame(main_frame, text="Distribucion de Pesos", padding=15)
        results_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0), sticky="ew")
        results_frame.columnconfigure(0, weight=1)

        # Crear labels para cada esquina
        self.weight_labels = {}
        corner_names = {
            "top-left": "Superior Izquierda",
            "top-right": "Superior Derecha",
            "bottom-left": "Inferior Izquierda",
            "bottom-right": "Inferior Derecha"
        }

        self.corner_buttons = {}
        for i, (corner_key, corner_display) in enumerate(corner_names.items()):
            frame = ttk.Frame(results_frame)
            frame.grid(row=i // 2, column=i % 2, padx=10, pady=5, sticky="ew")
            results_frame.columnconfigure(i % 2, weight=1)

            ttk.Label(
                frame,
                text=f"Esquina {corner_display}:",
                font=("Segoe UI", 9)
            ).pack(side="left")

            btn = ttk.Button(
                frame,
                text="Llevar",
                width=5,
                command=lambda k=corner_key: self._mover_a_esquina(k)
            )
            btn.pack(side="left", padx=(5, 0))
            self.corner_buttons[corner_key] = btn

            weight_label = ttk.Label(
                frame,
                text="0 kg",
                font=("Segoe UI", 11, "bold")
            )
            weight_label.pack(side="right")
            self.weight_labels[corner_key] = weight_label

        # Total medido (suma real de las 4 celdas)
        sep = ttk.Separator(results_frame, orient="horizontal")
        sep.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 5))

        total_frame = ttk.Frame(results_frame)
        total_frame.grid(row=3, column=0, columnspan=2, sticky="ew")

        ttk.Label(
            total_frame,
            text="Total medido:",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        self.total_measured_label = ttk.Label(
            total_frame,
            text="0 kg",
            font=("Segoe UI", 11, "bold"),
            foreground="#333"
        )
        self.total_measured_label.pack(side="right")

        # Vincular eventos del mouse al canvas
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

        # Escanear puertos al iniciar
        self._escanear_puertos()

        # Dibujar el estado inicial
        self._dibujar_canvas()

    def _escanear_puertos(self):
        """Escanea los puertos serial disponibles y actualiza el combobox"""
        ports = self.serial_service.list_available_ports()
        self.port_combo["values"] = ports
        if ports and not self.serial_port_var.get():
            self.serial_port_var.set(ports[0])

    def _toggle_serial(self):
        """Conecta o desconecta del puerto serial"""
        if self.serial_service.is_connected():
            # Desconectar
            self.serial_service.disconnect()
            self._on_serial_disconnected()
        else:
            # Conectar
            port = self.serial_port_var.get()
            if not port:
                messagebox.showwarning("Puerto no seleccionado",
                                       "Seleccione un puerto serial primero.")
                return

            baud = self.serial_baud_var.get()
            success = self.serial_service.connect(port, baud)

            if success:
                self._on_serial_connected(port, baud)
            else:
                messagebox.showerror("Error de conexion",
                                     f"No se pudo conectar a {port}.\n"
                                     "Verifique que el puerto exista y no este en uso.")

    def _on_serial_connected(self, port, baud):
        """Maneja la conexion serial exitosa"""
        self.serial_status_var.set(f"Conectado a {port} ({baud} baud)")
        self.status_label.config(foreground="#4CAF50")
        self.connect_btn.config(text="Desconectar")
        self.mode_label.config(text="Modo: Simulacion (reenvio activo)", foreground="#FF9800")

        # Registrar callback para respuestas de comandos del protocolo
        self.serial_service.on_command_response = self._on_protocol_command

        # Iniciar lectura en segundo plano
        self.serial_service.start_reading(
            data_callback=self._on_serial_data,
            error_callback=self._on_serial_error
        )

    def _on_serial_disconnected(self):
        """Maneja la desconexion del puerto serial"""
        self.serial_status_var.set("Desconectado")
        self.status_label.config(foreground="#999")
        self.connect_btn.config(text="Conectar")
        self.receiving_data = False
        self.mode_label.config(text="Modo: Simulacion", foreground="#666")
        self.cmd_label.config(text="")

        # Cancelar actualizaciones pendientes
        if self._serial_update_id:
            self.root.after_cancel(self._serial_update_id)
            self._serial_update_id = None
        if self._command_update_id:
            self.root.after_cancel(self._command_update_id)
            self._command_update_id = None

    def _on_serial_data(self, weights):
        """
        Recibe datos del puerto serial y actualiza la interfaz
        Args:
            weights: Dict con pesos {top-left, top-right, bottom-left, bottom-right}
        """
        if not self.serial_service.is_connected():
            return

        # Programar actualizacion en el hilo principal de tkinter
        if self._serial_update_id:
            self.root.after_cancel(self._serial_update_id)
        self._serial_update_id = self.root.after_idle(
            self._actualizar_con_datos_reales, weights
        )

    def _actualizar_con_datos_reales(self, weights):
        """
        Actualiza la interfaz con datos reales del puerto serial
        Args:
            weights: Dict con pesos de las 4 celdas
        """
        self._serial_update_id = None

        # Cambiar a modo datos reales y bloquear la bola
        if not self.receiving_data:
            self.receiving_data = True
            self.mode_label.config(text="Modo: Datos reales", foreground="#4CAF50")

        # Actualizar modelo con datos reales
        total = sum(weights.values())
        self.distribution.total_weight = total
        self.distribution.corner_weights = weights

        # Calcular posicion aproximada desde los pesos (interpolacion inversa)
        if total > 0:
            nx = (weights.get("bottom-right", 0) + weights.get("top-right", 0)) / total
            ny = (weights.get("bottom-left", 0) + weights.get("bottom-right", 0)) / total
            self.ball_x = max(15, min(SQUARE_SIZE - 15, nx * SQUARE_SIZE))
            self.ball_y = max(15, min(SQUARE_SIZE - 15, ny * SQUARE_SIZE))
            self.distribution.position_x = self.ball_x
            self.distribution.position_y = self.ball_y

        # Actualizar visualizacion
        self._dibujar_canvas()

        # Actualizar pesos en el protocolo de celdas virtuales
        self.cell_protocol.update_all_weights(weights)

        # Actualizar labels de pesos con colores
        for corner, weight_value in weights.items():
            color = self.weight_service.get_weight_color(weight_value, total)
            self.weight_labels[corner].config(
                text=f"{weight_value} kg",
                foreground=color
            )

        # Actualizar label de total medido
        self.total_measured_label.config(text=f"{round(total, 2)} kg")

        # Actualizar label de posicion
        self.pos_label.config(text=f"({int(self.ball_x)}, {int(self.ball_y)})")

        # Reenviar datos al otro programa si esta activo
        self._reenviar_datos(weights)

    def _on_serial_error(self, error_msg):
        """Maneja errores del puerto serial"""
        self.root.after_idle(
            lambda: self.serial_status_var.set(f"Error: {error_msg}")
        )
        self.root.after_idle(
            lambda: self.status_label.config(foreground="#F44336")
        )

    def _on_protocol_command(self, command, response):
        """
        Callback para cuando se procesa un comando del protocolo HBM
        Muestra el comando y respuesta en la UI para feedback visual

        Args:
            command: Comando recibido (ej: "S01;MSV?")
            response: Respuesta enviada (ej: "-0010236")
        """
        if self._command_update_id:
            self.root.after_cancel(self._command_update_id)
        self._command_update_id = self.root.after_idle(
            self._mostrar_comando_protocolo, command, response
        )

    def _mostrar_comando_protocolo(self, command, response):
        """
        Actualiza la etiqueta de comando en la UI
        Muestra el ultimo comando recibido y su respuesta, y lo limpia tras 5 segundos
        """
        self._command_update_id = None
        self.cmd_label.config(
            text=f"CMD: {command} => {response}",
            foreground="#005EEC"
        )
        # Limpiar el mensaje despues de 5 segundos
        self.root.after(5000, lambda: self.cmd_label.config(text=""))

    def _reenviar_datos(self, weights):
        """
        Reenvia los valores de las celdas al otro programa a traves del par virtual
        Solo reenvia si el checkbox esta activo y el puerto serial esta conectado

        Args:
            weights: Dict con pesos {top-left, top-right, bottom-left, bottom-right}
        """
        if not self.forward_data_var.get() or not self.serial_service.is_connected():
            return

        # Formato CSV con retorno de carro para compatibilidad
        datos = f"{weights['top-left']},{weights['top-right']},{weights['bottom-left']},{weights['bottom-right']}\r\n"
        self.serial_service.send_data(datos)

    def _dibujar_canvas(self):
        """Dibuja el cuadrado, la cuadricula, las marcas de esquinas y la bola"""
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

        # Dibujar bola
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
        """Calcula la distribucion de pesos y actualiza la interfaz"""
        if self.receiving_data:
            return

        weight = self.total_weight.get()
        if weight < MIN_WEIGHT:
            weight = MIN_WEIGHT
            self.total_weight.set(MIN_WEIGHT)

        # Calcular pesos en cada esquina
        corner_weights = self.weight_service.calculate_corner_weights(
            self.ball_x, self.ball_y, weight
        )

        # Obtener el total medido real (suma de las 4 celdas, incluye offsets + ruido)
        measured_total = self.weight_service.get_measured_total(corner_weights)

        # Actualizar modelo
        self.distribution.total_weight = measured_total
        self.distribution.position_x = self.ball_x
        self.distribution.position_y = self.ball_y
        self.distribution.corner_weights = corner_weights

        # Actualizar pesos en el protocolo de celdas virtuales
        self.cell_protocol.update_all_weights(corner_weights)

        # Actualizar labels de pesos con colores (usa total medido como referencia)
        for corner, weight_value in corner_weights.items():
            color = self.weight_service.get_weight_color(weight_value, measured_total)
            self.weight_labels[corner].config(
                text=f"{weight_value} kg",
                foreground=color
            )

        # Actualizar label de total medido
        self.total_measured_label.config(text=f"{measured_total} kg")

        # Actualizar label de posicion
        self.pos_label.config(text=f"({int(self.ball_x)}, {int(self.ball_y)})")

        # Reenviar datos al otro programa si esta activo
        self._reenviar_datos(corner_weights)

    def _reiniciar_peso(self):
        """Pone el peso total en 0 kg"""
        if self.receiving_data:
            return

        self.total_weight.set(0)
        self._calcular_y_actualizar()

    def _tare_celdas(self):
        """Activa o desactiva la tara de las celdas de carga

        Al activar: captura los offsets como linea base y los resta de las lecturas.
        Los valores negativos desaparecen y el sistema mide solo el peso aplicado + ruido.

        Al desactivar: restaura los offsets originales (las celdas vuelven a mostrar
        sus valores sin compensar, incluyendo los negativos).
        """
        if self.receiving_data:
            return

        if self.weight_service.is_tared:
            self.weight_service.clear_tare()
            self.tare_status_label.config(text="")
        else:
            self.weight_service.tare()
            self.tare_status_label.config(
                text="Tara activa",
                foreground="#4CAF50"
            )

        self._calcular_y_actualizar()

    def _mover_a_esquina(self, corner_key):
        """Mueve la bola a la esquina indicada"""
        if self.receiving_data:
            return

        margin = 15
        positions = {
            "top-left": (margin, margin),
            "top-right": (SQUARE_SIZE - margin, margin),
            "bottom-left": (margin, SQUARE_SIZE - margin),
            "bottom-right": (SQUARE_SIZE - margin, SQUARE_SIZE - margin)
        }
        self.ball_x, self.ball_y = positions[corner_key]
        self._dibujar_canvas()
        self._calcular_y_actualizar()

    def _reiniciar_posicion(self):
        """Reinicia la posicion de la bola al centro del cuadrado"""
        if self.receiving_data:
            return

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
        """Maneja el evento de presionar el boton del mouse"""
        if self.receiving_data:
            return

        self.is_dragging = True
        self.ball_x, self.ball_y = self._obtener_posicion_mouse(event)
        self._dibujar_canvas()
        self._calcular_y_actualizar()

    def _on_mouse_move(self, event):
        """Maneja el evento de arrastrar el mouse"""
        if self.receiving_data or not self.is_dragging:
            return

        self.ball_x, self.ball_y = self._obtener_posicion_mouse(event)
        self._dibujar_canvas()
        self._calcular_y_actualizar()

    def _on_mouse_up(self, event):
        """Maneja el evento de soltar el boton del mouse"""
        self.is_dragging = False

    def __del__(self):
        """Limpia recursos al cerrar la aplicacion"""
        if hasattr(self, "serial_service"):
            self.serial_service.disconnect()


def main():
    """Punto de entrada principal de la aplicacion"""
    root = tk.Tk()
    app = SimuladorCeldas(root)
    root.mainloop()


if __name__ == "__main__":
    main()
