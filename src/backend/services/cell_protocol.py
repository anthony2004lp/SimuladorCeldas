"""
Protocolo de comunicacion para celdas de carga HBM C16iC3

Soporta dos formatos de comando:

Formato multi-linea (nuevo):
  S98                     # Llamada a grupo (todas las celdas, no responden)
  MSV? o msv?             # Comando a ejecutar (case insensitive)
  S02                     # Celda destino a consultar

Formato clasico (compatibilidad):
  Sxx;MSV?;   - Consultar el peso de la celda en direccion xx
  Sxx;IDN?;   - Consultar el numero de serie de la celda en direccion xx
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
        weight_int = int(abs(self.weight) * 10 + 0.5)
        sign = "-" if self.weight < 0 else " "
        return f"{sign}{weight_int:07d}"

    def get_id_response(self):
        """
        Genera la respuesta para el comando IDN?
        Formato: HBM,MODELO          ,SERIAL   ,VERSION
        Ejemplo: HBM,C16iC3/40t     ,M64702 ,P52
        """
        model = "C16iC3/40t"
        serial = self.serial_number
        return f"HBM,{model:14s},{serial:7s},P52"


class CellProtocol:
    """
    Gestiona el protocolo de comunicacion con las celdas de carga

    Soporta dos formatos:
    1. Multi-linea: S98 -> MSV?/IDN?/TDD1 -> Sxx
    2. Clasico: Sxx;MSV?;  Sxx;IDN?;  ADRx,"SERIAL"  Sxx;TDD1;
    """

    # Estados del protocolo multi-linea
    STATE_IDLE = 0
    STATE_GROUP_SENT = 1
    STATE_CMD_RECEIVED = 2

    # Patrones para formato clasico (case insensitive)
    RE_MSV = re.compile(r"^S(\d+);MSV\?;?$", re.IGNORECASE)
    RE_IDN = re.compile(r"^S(\d+);IDN\?;?$", re.IGNORECASE)
    RE_ADR = re.compile(r'^ADR(\d+),"([^"]+)"(?:;)?$', re.IGNORECASE)
    RE_TDD = re.compile(r"^S(\d+);TDD1;?$", re.IGNORECASE)

    def __init__(self):
        """Inicializa el gestor de protocolo con 4 celdas virtuales por defecto"""
        self.cells = {}
        self._init_default_cells()
        self.last_command = None
        self.last_response = None
        # Maquina de estados para protocolo multi-linea
        self.state = self.STATE_IDLE
        self.pending_command = None

    def _init_default_cells(self):
        """Crea las 4 celdas virtuales por defecto, una por esquina"""
        defaults = [
            ("S00", "M64701", "top-left"),
            ("S01", "M64702", "top-right"),
            ("S02", "M64703", "bottom-left"),
            ("S03", "M64704", "bottom-right"),
        ]
        for addr, serial, name in defaults:
            self.cells[addr] = VirtualCell(addr, serial, name)

    def _reset_state(self):
        """Reinicia la maquina de estados del protocolo multi-linea"""
        self.state = self.STATE_IDLE
        self.pending_command = None

    def get_cell_by_address(self, address):
        """Busca una celda por su direccion (formato Sxx)"""
        return self.cells.get(address)

    def get_cell_by_serial(self, serial_number):
        """Busca una celda por su numero de serie"""
        for cell in self.cells.values():
            if cell.serial_number == serial_number:
                return cell
        return None

    def update_weight(self, address, weight):
        """Actualiza el peso de una celda por su direccion"""
        cell = self.get_cell_by_address(address)
        if cell:
            cell.weight = weight
            return True
        return False

    def update_all_weights(self, weights_dict):
        """Actualiza los pesos de todas las celdas desde un dict de esquinas"""
        corner_to_addr = {
            "top-left": "S00", "top-right": "S01",
            "bottom-left": "S02", "bottom-right": "S03",
        }
        for corner_name, weight in weights_dict.items():
            addr = corner_to_addr.get(corner_name)
            if addr:
                self.update_weight(addr, weight)

    def get_all_weights_dict(self):
        """Devuelve los pesos actuales en formato esquinas"""
        addr_to_corner = {
            "S00": "top-left", "S01": "top-right",
            "S02": "bottom-left", "S03": "bottom-right",
        }
        result = {}
        for addr, corner in addr_to_corner.items():
            cell = self.get_cell_by_address(addr)
            if cell:
                result[corner] = cell.weight
        return result

    # ------------------------------------------------------------------ #
    # Procesamiento de comandos
    # ------------------------------------------------------------------ #

    def handle_command(self, command_line):
        """
        Procesa una linea de comando y devuelve la respuesta a enviar

        Maquina de estados para multi-linea (S98 -> MSV? -> Sxx).
        Si no hay transaccion activa, prueba el formato clasico.

        Args:
            command_line: Linea de texto con el comando

        Returns:
            str: Respuesta formateada, "" si es paso intermedio,
                 None si no es comando valido en ningun formato
        """
        command_line = command_line.strip()
        self.last_command = command_line
        self.last_response = None

        # ========================================================== #
        # PROTOCOLO MULTI-LINEA
        # ========================================================== #

        # Paso 1: S98 - llamada a grupo, inicia transaccion
        if command_line.upper() == "S98":
            self.state = self.STATE_GROUP_SENT
            self.pending_command = None
            self.last_response = ""
            return self.last_response

        # Paso 2: comando (MSV?/IDN?/TDD1) - case insensitive
        if self.state == self.STATE_GROUP_SENT:
            upper = command_line.upper()
            if upper in ("MSV?", "IDN?", "TDD1"):
                self.state = self.STATE_CMD_RECEIVED
                self.pending_command = upper
                self.last_response = ""
                return self.last_response
            self._reset_state()
            self.last_response = "?"
            return self.last_response

        # Paso 3: destino (Sxx) - ejecuta comando almacenado
        if self.state == self.STATE_CMD_RECEIVED:
            match = re.match(r"^S(\d+)$", command_line.upper())
            if match:
                addr = f"S{match.group(1)}"
                cell = self.get_cell_by_address(addr)
                if self.pending_command == "MSV?":
                    self.last_response = cell.get_weight_response() if cell else "?S00"
                elif self.pending_command == "IDN?":
                    self.last_response = cell.get_id_response() if cell else "?S00"
                elif self.pending_command == "TDD1":
                    if cell:
                        cell.eeprom_dirty = False
                        self.last_response = "OK"
                    else:
                        self.last_response = "?S00"
                self._reset_state()
                return self.last_response
            self._reset_state()
            self.last_response = "?"
            return self.last_response

        # ========================================================== #
        # FORMATO CLASICO (compatibilidad hacia atras)
        # ========================================================== #

        match = self.RE_MSV.match(command_line)
        if match:
            addr = f"S{match.group(1)}"
            cell = self.get_cell_by_address(addr)
            self.last_response = cell.get_weight_response() if cell else "?S00"
            return self.last_response

        match = self.RE_IDN.match(command_line)
        if match:
            addr = f"S{match.group(1)}"
            cell = self.get_cell_by_address(addr)
            self.last_response = cell.get_id_response() if cell else "?S00"
            return self.last_response

        match = self.RE_ADR.match(command_line)
        if match:
            new_addr_num = match.group(1)
            serial = match.group(2)
            cell = self.get_cell_by_serial(serial)
            if cell:
                old_addr = cell.address
                new_addr = f"S{int(new_addr_num):02d}"
                if old_addr == new_addr:
                    self.last_response = f"OK {serial} -> {new_addr} (sin cambios)"
                else:
                    existing_cell = self.get_cell_by_address(new_addr)
                    if existing_cell:
                        existing_cell.address = old_addr
                        self.cells[old_addr] = existing_cell
                    else:
                        del self.cells[old_addr]
                    cell.address = new_addr
                    self.cells[new_addr] = cell
                    self.last_response = f"OK {serial} -> {new_addr}"
            else:
                self.last_response = f"?{serial}"
            return self.last_response

        match = self.RE_TDD.match(command_line)
        if match:
            addr = f"S{match.group(1)}"
            cell = self.get_cell_by_address(addr)
            if cell:
                cell.eeprom_dirty = False
                self.last_response = "OK"
            else:
                self.last_response = "?S00"
            return self.last_response

        return None

    def is_command(self, line):
        """
        Verifica si una linea debe ser tratada como comando

        Incluye el protocolo multi-linea (segun estado actual)
        y el formato clasico de una sola linea.

        Args:
            line: Linea de texto a verificar
        Returns:
            bool: True si es comando en el contexto actual
        """
        line = line.strip()

        if line.upper() == "S98":
            return True

        if self.state != self.STATE_IDLE:
            return True

        upper = line.upper()
        return bool(
            self.RE_MSV.match(upper)
            or self.RE_IDN.match(upper)
            or self.RE_ADR.match(line)
            or self.RE_TDD.match(upper)
        )
