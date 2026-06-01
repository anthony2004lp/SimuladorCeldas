"""
Protocolo de comunicacion para celdas de carga HBM C16iC3

Soporta los siguientes comandos:
  Sxx;MSV?   - Consultar el peso de la celda en direccion xx
  Sxx;IDN?   - Consultar el numero de serie de la celda en direccion xx
  ADRx,"SERIAL" - Asignar la direccion x a la celda con numero de serie SERIAL
  Sxx;TDD1   - Guardar la configuracion en la EEPROM (simulado)

Las celdas se almacenan en una tabla interna con direccion y numero de serie.
Cuando se recibe un comando, el protocolo busca la celda correspondiente
y genera la respuesta adecuada segun el estado actual de la simulacion.
"""

import re


class VirtualCell:
    """Representa una celda de carga virtual con su direccion y numero de serie"""

    def __init__(self, address, serial_number, name=""):
        """
        Inicializa una celda virtual
        Args:
            address: Direccion de la celda (formato Sxx, ej: S01)
            serial_number: Numero de serie unico (ej: M64702)
            name: Nombre descriptivo opcional (top-left, top-right, etc.)
        """
        self.address = address          # Direccion asignada (S00, S01, etc.)
        self.serial_number = serial_number  # Numero de serie unico
        self.name = name                # Nombre descriptivo de la celda
        self.weight = 0.0               # Peso actual en kg
        self.eeprom_dirty = False       # Indica si hay cambios sin guardar en EEPROM

    def get_weight_response(self):
        """
        Genera la respuesta para el comando MSV?
        Formato: SGGGGGGG  (signo + 7 digitos numericos)
        El peso se expresa en decimas de kg (0.1 kg = 1 unidad)
        Ejemplo: -0010236  => -1023.6 kg
        """
        # Convertir peso a decimas de kg y redondear
        weight_int = int(abs(self.weight) * 10 + 0.5)
        # Determinar el signo
        sign = "-" if self.weight < 0 else " "
        # Formatear a 7 digitos con signo
        return f"{sign}{weight_int:07d}"

    def get_id_response(self):
        """
        Genera la respuesta para el comando IDN?
        Formato: HBM,MODELO          ,SERIAL   ,VERSION
        Ejemplo: HBM,C16iC3/40t     ,M64702 ,P52
        """
        model = "C16iC3/40t"
        serial = self.serial_number
        # Formatear con espacios fijos para coincidir con el formato esperado
        return f"HBM,{model:14s},{serial:7s},P52"


class CellProtocol:
    """
    Gestiona el protocolo de comunicacion con las celdas de carga

    Mantiene una tabla de celdas virtuales (accedidas por direccion Sxx).
    Procesa comandos entrantes, busca la celda objetivo y genera la
    respuesta correspondiente.

    Comandos soportados:
        Sxx;MSV?   - Consultar peso de la celda en direccion xx
        Sxx;IDN?   - Consultar numero de serie de la celda en direccion xx
        ADRx,"SERIAL" - Asignar direccion x a la celda con numero de serie SERIAL
        Sxx;TDD1   - Guardar configuracion en EEPROM (simulado)
    """

    # Patrones de expresiones regulares para cada comando
    # Se permite un punto y coma opcional al final para tolerancia
    RE_MSV = re.compile(r"^S(\d+);MSV\?;?$")           # Ej: S01;MSV?  o  S01;MSV?;
    RE_IDN = re.compile(r"^S(\d+);IDN\?;?$")           # Ej: S02;IDN?  o  S02;IDN?;
    RE_ADR = re.compile(r'^ADR(\d+),"([^"]+)"(?:;)?$') # Ej: ADR2,"M64702"  o  ADR2,"M64702";
    RE_TDD = re.compile(r"^S(\d+);TDD1;?$")            # Ej: S02;TDD1  o  S02;TDD1;

    def __init__(self):
        """Inicializa el gestor de protocolo con 4 celdas virtuales por defecto"""
        self.cells = {}             # Diccionario: direccion (Sxx) -> VirtualCell
        self._init_default_cells()  # Crear las 4 celdas iniciales
        self.last_command = None    # Ultimo comando procesado
        self.last_response = None   # Ultima respuesta generada

    def _init_default_cells(self):
        """
        Crea las 4 celdas virtuales por defecto
        Cada celda se asocia a una esquina del simulador
        """
        defaults = [
            ("S00", "M64701", "top-left"),      # Celda 0: esquina superior izquierda
            ("S01", "M64702", "top-right"),     # Celda 1: esquina superior derecha
            ("S02", "M64703", "bottom-left"),   # Celda 2: esquina inferior izquierda
            ("S03", "M64704", "bottom-right"),  # Celda 3: esquina inferior derecha
        ]
        for addr, serial, name in defaults:
            self.cells[addr] = VirtualCell(addr, serial, name)

    def get_cell_by_address(self, address):
        """
        Busca una celda por su direccion
        Args:
            address: Direccion en formato Sxx (ej: S01)
        Returns:
            VirtualCell o None si no se encuentra
        """
        return self.cells.get(address)

    def get_cell_by_serial(self, serial_number):
        """
        Busca una celda por su numero de serie
        Args:
            serial_number: Numero de serie (ej: M64702)
        Returns:
            VirtualCell o None si no se encuentra
        """
        for cell in self.cells.values():
            if cell.serial_number == serial_number:
                return cell
        return None

    def update_weight(self, address, weight):
        """
        Actualiza el peso de una celda por su direccion
        Args:
            address: Direccion en formato Sxx
            weight: Nuevo peso en kg
        Returns:
            bool: True si se actualizo correctamente
        """
        cell = self.get_cell_by_address(address)
        if cell:
            cell.weight = weight
            return True
        return False

    def update_all_weights(self, weights_dict):
        """
        Actualiza los pesos de todas las celdas desde un diccionario

        Convierte los nombres de esquina del simulador a direcciones Sxx
        y actualiza el peso de cada celda virtual.

        Args:
            weights_dict: Dict con formato {"top-left": 25.0, "top-right": 31.2, ...}
        """
        # Mapeo de nombres de esquina a direcciones de celda
        corner_to_addr = {
            "top-left": "S00",
            "top-right": "S01",
            "bottom-left": "S02",
            "bottom-right": "S03",
        }
        for corner_name, weight in weights_dict.items():
            addr = corner_to_addr.get(corner_name)
            if addr:
                self.update_weight(addr, weight)

    def get_all_weights_dict(self):
        """
        Devuelve un diccionario con los pesos actuales de todas las celdas
        en el formato de esquinas del simulador
        Returns:
            dict: {"top-left": float, "top-right": float, ...}
        """
        addr_to_corner = {
            "S00": "top-left",
            "S01": "top-right",
            "S02": "bottom-left",
            "S03": "bottom-right",
        }
        result = {}
        for addr, corner in addr_to_corner.items():
            cell = self.get_cell_by_address(addr)
            if cell:
                result[corner] = cell.weight
        return result

    def handle_command(self, command_line):
        """
        Procesa una linea de comando y devuelve la respuesta a enviar

        El metodo identifica el tipo de comando usando expresiones regulares,
        busca la celda objetivo y genera la respuesta correspondiente.

        Args:
            command_line: Linea de texto con el comando (ej: "S01;MSV?")

        Returns:
            str o None: Respuesta formateada para enviar, None si no es comando valido
        """
        command_line = command_line.strip()
        self.last_command = command_line
        self.last_response = None

        # --- Comando: Sxx;MSV? --- Consultar peso de la celda ---
        match = self.RE_MSV.match(command_line)
        if match:
            addr = f"S{match.group(1)}"  # Construir direccion Sxx
            cell = self.get_cell_by_address(addr)
            if cell:
                # Generar respuesta con el peso actual de la celda
                self.last_response = cell.get_weight_response()
            else:
                # Celda no encontrada: responder con codigo de error
                self.last_response = "?S00"
            return self.last_response

        # --- Comando: Sxx;IDN? --- Consultar numero de serie ---
        match = self.RE_IDN.match(command_line)
        if match:
            addr = f"S{match.group(1)}"
            cell = self.get_cell_by_address(addr)
            if cell:
                # Generar respuesta con modelo, serie y version
                self.last_response = cell.get_id_response()
            else:
                self.last_response = "?S00"
            return self.last_response

        # --- Comando: ADRx,"SERIAL" --- Asignar direccion por numero de serie ---
        match = self.RE_ADR.match(command_line)
        if match:
            new_addr_num = match.group(1)   # Nueva direccion (ej: 2)
            serial = match.group(2)         # Numero de serie (ej: M64702)
            cell = self.get_cell_by_serial(serial)
            if cell:
                old_addr = cell.address
                new_addr = f"S{int(new_addr_num):02d}"
                if old_addr == new_addr:
                    # La celda ya tiene esa direccion, no hacer cambios
                    self.last_response = f"OK {serial} -> {new_addr} (sin cambios)"
                else:
                    # Verificar si la nueva direccion ya esta ocupada
                    existing_cell = self.get_cell_by_address(new_addr)
                    if existing_cell:
                        # Intercambiar direcciones: el ocupante pasa a la direccion vieja
                        existing_cell.address = old_addr
                        self.cells[old_addr] = existing_cell
                    else:
                        # La direccion esta libre, eliminar la entrada anterior
                        del self.cells[old_addr]
                    # Asignar la nueva direccion a la celda solicitada
                    cell.address = new_addr
                    self.cells[new_addr] = cell
                    self.last_response = f"OK {serial} -> {new_addr}"
            else:
                # Numero de serie no encontrado
                self.last_response = f"?{serial}"
            return self.last_response

        # --- Comando: Sxx;TDD1 --- Guardar en EEPROM ---
        match = self.RE_TDD.match(command_line)
        if match:
            addr = f"S{match.group(1)}"
            cell = self.get_cell_by_address(addr)
            if cell:
                # Marcar EEPROM como guardada (simulado)
                cell.eeprom_dirty = False
                self.last_response = "OK"
            else:
                self.last_response = "?S00"
            return self.last_response

        # No es un comando reconocido
        return None

    def is_command(self, line):
        """
        Verifica si una linea de texto coincide con algun comando del protocolo
        Args:
            line: Linea de texto a verificar
        Returns:
            bool: True si la linea es un comando valido
        """
        line = line.strip()
        return bool(
            self.RE_MSV.match(line)
            or self.RE_IDN.match(line)
            or self.RE_ADR.match(line)
            or self.RE_TDD.match(line)
        )
