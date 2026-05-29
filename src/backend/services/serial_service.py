import sys
import os
import threading
import json
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from config.constans import SQUARE_SIZE


class SerialService:
    """Servicio para comunicacion serial con balanza de celdas de carga"""

    def __init__(self):
        """Inicializa el servicio serial"""
        self.connection = None
        self.running = False
        self.read_thread = None
        self.on_data_received = None
        self.on_error = None
        self._lock = threading.Lock()
        self._last_data = None

    def list_available_ports(self):
        """
        Escanea y devuelve los puertos serial disponibles
        Returns:
            list: Lista de nombres de puertos (ej: COM3, /dev/ttyUSB0)
        """
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            return [port.device for port in sorted(ports)]
        except ImportError:
            return []
        except Exception:
            return []

    def connect(self, port, baudrate=9600, timeout=1, **kwargs):
        """
        Conecta al puerto serial especificado
        Args:
            port: Nombre del puerto (ej: COM3)
            baudrate: Velocidad en baudios (9600 por defecto)
            timeout: Timeout de lectura en segundos
        Returns:
            bool: True si la conexion fue exitosa
        """
        try:
            import serial
            self.disconnect()

            self.connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                **kwargs
            )

            return self.connection.is_open

        except Exception as e:
            self._notify_error(f"Error al conectar a {port}: {e}")
            return False

    def disconnect(self):
        """Desconecta del puerto serial si esta conectado"""
        self.stop_reading()

        with self._lock:
            if self.connection and self.connection.is_open:
                try:
                    self.connection.close()
                except Exception:
                    pass
            self.connection = None

    def is_connected(self):
        """Verifica si hay una conexion activa"""
        with self._lock:
            return self.connection is not None and self.connection.is_open

    def start_reading(self, data_callback, error_callback=None):
        """
        Inicia un hilo en segundo plano para leer datos del puerto serial
        Args:
            data_callback: Funcion que recibe los pesos parseados {top-left, top-right, ...}
            error_callback: Funcion que recibe mensajes de error
        """
        self.on_data_received = data_callback
        self.on_error = error_callback
        self.running = True

        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()

    def stop_reading(self):
        """Detiene el hilo de lectura"""
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        self.read_thread = None

    def _read_loop(self):
        """Bucle interno de lectura en segundo plano"""
        buffer = ""

        while self.running:
            try:
                if not self.is_connected():
                    self._notify_error("Conexion perdida con el puerto serial")
                    break

                with self._lock:
                    if self.connection and self.connection.in_waiting > 0:
                        raw = self.connection.read(self.connection.in_waiting)
                        buffer += raw.decode("utf-8", errors="replace")

                # Procesar lineas completas (separadas por \n)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        parsed = self._parse_line(line)
                        if parsed:
                            self._last_data = parsed
                            if self.on_data_received:
                                self.on_data_received(parsed)

            except Exception as e:
                self._notify_error(f"Error de lectura serial: {e}")
                break

    def _parse_line(self, line):
        """
        Parsea una linea de texto proveniente del puerto serial
        Soporta formato CSV (4 valores separados por coma) y JSON

        Args:
            line: Linea de texto recibida
        Returns:
            dict | None: Pesos parseados {top-left, top-right, bottom-left, bottom-right}
        """
        # Intentar parsear como JSON primero
        if line.startswith("{"):
            try:
                data = json.loads(line)
                return {
                    "top-left": float(data.get("top-left", 0)),
                    "top-right": float(data.get("top-right", 0)),
                    "bottom-left": float(data.get("bottom-left", 0)),
                    "bottom-right": float(data.get("bottom-right", 0))
                }
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # Intentar parsear como CSV: val1,val2,val3,val4
        parts = line.split(",")
        if len(parts) == 4:
            try:
                values = [float(p.strip()) for p in parts]
                return {
                    "top-left": values[0],
                    "top-right": values[1],
                    "bottom-left": values[2],
                    "bottom-right": values[3]
                }
            except (ValueError, TypeError):
                pass

        # Intentar extraer 4 numeros con regex
        numbers = re.findall(r"[-+]?\d*\.?\d+", line)
        if len(numbers) >= 4:
            try:
                values = [float(n) for n in numbers[:4]]
                return {
                    "top-left": values[0],
                    "top-right": values[1],
                    "bottom-left": values[2],
                    "bottom-right": values[3]
                }
            except (ValueError, TypeError):
                pass

        return None

    def send_data(self, data):
        """
        Envia datos al puerto serial
        Args:
            data: String o bytes a enviar
        Returns:
            bool: True si se envio correctamente
        """
        try:
            if not self.is_connected():
                return False

            if isinstance(data, str):
                data = data.encode("utf-8")

            with self._lock:
                self.connection.write(data)
            return True

        except Exception as e:
            self._notify_error(f"Error al enviar datos: {e}")
            return False

    def get_last_data(self):
        """Devuelve el ultimo conjunto de datos recibido"""
        return self._last_data

    def _notify_error(self, message):
        """Notifica un error a traves del callback"""
        if self.on_error:
            self.on_error(message)
