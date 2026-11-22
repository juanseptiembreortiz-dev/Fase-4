from abc import ABC, abstractmethod
from datetime import datetime
from functools import singledispatchmethod
import re


# =====================================================================
# 1. EXCEPCIONES PERSONALIZADAS
# =====================================================================
class ErrorSistemaSoftwareFJ(Exception):
    """Excepción base del sistema de gestión de Software FJ."""


class ErrorValidacionDato(ErrorSistemaSoftwareFJ):
    """Error lanzado cuando un dato o parámetro no cumple las reglas."""


class ErrorServicioNoDisponible(ErrorSistemaSoftwareFJ):
    """Error lanzado cuando se intenta usar un servicio no disponible."""


class ErrorReservaInvalida(ErrorSistemaSoftwareFJ):
    """Error lanzado ante una reserva inconsistente o inválida."""


class ErrorOperacionNoPermitida(ErrorSistemaSoftwareFJ):
    """Error lanzado cuando el estado actual impide la operación."""


# =====================================================================
# 2. REGISTRADOR DE LOGS (ARCHIVO DE TEXTO, SIN BASE DE DATOS)
# =====================================================================
class RegistradorLogs:
    def __init__(self, ruta_archivo: str = "software_fj.log") -> None:
        self.ruta_archivo = ruta_archivo

    def registrar(self, nivel: str, mensaje: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{timestamp}] [{nivel}] {mensaje}\n"
        try:
            with open(self.ruta_archivo, "a", encoding="utf-8") as archivo:
                archivo.write(linea)
        except OSError as exc:
            print(f"[AVISO LOG] No se pudo escribir en {self.ruta_archivo}: {exc}")


# =====================================================================
# 3. CLASE ABSTRACTA BASE Y CLASE CLIENTE (ENCAPSULACIÓN Y VALIDACIÓN)
# =====================================================================
class EntidadBase(ABC):
    def __init__(self, id_entidad: str) -> None:
        if not isinstance(id_entidad, str) or not id_entidad.strip():
            raise ErrorValidacionDato("El ID de la entidad no puede estar vacío.")
        self._id_entidad = id_entidad.strip().upper()
        self._fecha_registro = datetime.now()

    @property
    def id_entidad(self) -> str:
        return self._id_entidad

    @property
    def fecha_registro(self) -> datetime:
        return self._fecha_registro

    @abstractmethod
    def resumen(self) -> str:
        """Devuelve una descripción resumida de la entidad."""


class Cliente(EntidadBase):
    def __init__(self, id_entidad: str, nombre: str, documento: str, correo: str) -> None:
        super().__init__(id_entidad)
        self.nombre = nombre
        self.documento = documento
        self.correo = correo

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 2:
            raise ErrorValidacionDato("El nombre del cliente debe tener al menos 2 caracteres.")
        self._nombre = valor.strip()

    @property
    def documento(self) -> str:
        return self._documento

    @documento.setter
    def documento(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip().isalnum():
            raise ErrorValidacionDato("El documento debe ser alfanumérico y no estar vacío.")
        self._documento = valor.strip().upper()

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        patron = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
        if not isinstance(valor, str) or not re.match(patron, valor.strip()):
            raise ErrorValidacionDato(f"Correo electrónico inválido: '{valor}'.")
        self._correo = valor.strip().lower()

    def resumen(self) -> str:
        return f"Cliente [{self.id_entidad}] {self.nombre} | Doc: {self.documento} | Correo: {self.correo}"


# =====================================================================
# 4. CLASE ABSTRACTA SERVICIO Y CLASES DERIVADAS (HERENCIA Y POLIMORFISMO)
# =====================================================================
class Servicio(EntidadBase):
    def __init__(self, id_entidad: str, nombre: str, tarifa_base: float, disponible: bool = True) -> None:
        super().__init__(id_entidad)
        self.nombre = nombre
        self.tarifa_base = tarifa_base
        self._disponible = bool(disponible)

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorValidacionDato("El nombre del servicio es obligatorio.")
        self._nombre = valor.strip()

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
            raise ErrorValidacionDato("La tarifa base debe ser un número mayor que cero.")
        self._tarifa_base = float(valor)

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        self._disponible = bool(estado)

    @abstractmethod
    def calcular_costo_base(self, duracion: int) -> float:
        """Calcula el costo según la duración o unidades del servicio."""

    @abstractmethod
    def describir(self) -> str:
        """Describe los detalles específicos del servicio."""

    @abstractmethod
    def validar_parametros(self, duracion: int) -> None:
        """Valida si la duración o parámetros son válidos para este servicio."""

    # Variantes / sobrecarga de cálculo con parámetros opcionales
    def calcular_costo(
        self,
        duracion: int,
        impuesto_pct: float = 0.0,
        descuento_pct: float = 0.0,
        recargo_extra: float = 0.0,
    ) -> float:
        if not (0 <= impuesto_pct <= 100) or not (0 <= descuento_pct <= 100):
            raise ErrorValidacionDato("Los porcentajes de impuesto y descuento deben estar entre 0 y 100.")
        if recargo_extra < 0:
            raise ErrorValidacionDato("El recargo extra no puede ser negativo.")

        subtotal = self.calcular_costo_base(duracion) + recargo_extra
        con_descuento = subtotal * (1 - descuento_pct / 100.0)
        total = con_descuento * (1 + impuesto_pct / 100.0)
        return round(total, 2)

    # Sobrecarga basada en tipo de argumento con singledispatchmethod
    @singledispatchmethod
    def aplicar_ajuste_especial(self, ajuste) -> float:
        raise ErrorValidacionDato(f"Tipo de ajuste no soportado: {type(ajuste).__name__}")

    @aplicar_ajuste_especial.register
    def _(self, porcentaje_descuento: float) -> float:
        if not (0 <= porcentaje_descuento <= 100):
            raise ErrorValidacionDato("El descuento porcentual debe estar entre 0 y 100.")
        return round(self._tarifa_base * (1 - porcentaje_descuento / 100.0), 2)

    @aplicar_ajuste_especial.register
    def _(self, monto_fijo_extra: int) -> float:
        if monto_fijo_extra < 0:
            raise ErrorValidacionDato("El monto fijo extra no puede ser negativo.")
        return round(self._tarifa_base + monto_fijo_extra, 2)

    def resumen(self) -> str:
        estado = "Disponible" if self._disponible else "No disponible"
        return f"Servicio [{self.id_entidad}] {self.nombre} ({estado}) - {self.describir()}"


class ReservaSala(Servicio):
    """Reserva de salas (horas)."""

    def __init__(self, id_entidad: str, nombre: str, tarifa_hora: float, capacidad: int, disponible: bool = True) -> None:
        super().__init__(id_entidad, nombre, tarifa_hora, disponible)
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
            raise ErrorValidacionDato("La capacidad de la sala debe ser un entero positivo.")
        self.capacidad = capacidad

    def validar_parametros(self, duracion: int) -> None:
        if isinstance(duracion, bool) or not isinstance(duracion, int) or not (1 <= duracion <= 24):
            raise ErrorValidacionDato("La duración en horas para una sala debe estar entre 1 y 24.")

    def calcular_costo_base(self, duracion: int) -> float:
        self.validar_parametros(duracion)
        return self.tarifa_base * duracion

    def describir(self) -> str:
        return f"Reserva de Sala (capacidad {self.capacidad} personas, tarifa/hora: ${self.tarifa_base:,.2f})"


class AlquilerEquipo(Servicio):
    """Alquiler de equipos (días)."""

    def __init__(self, id_entidad: str, nombre: str, tarifa_dia: float, codigo_equipo: str, disponible: bool = True) -> None:
        super().__init__(id_entidad, nombre, tarifa_dia, disponible)
        if not isinstance(codigo_equipo, str) or not codigo_equipo.strip():
            raise ErrorValidacionDato("El código del equipo es obligatorio.")
        self.codigo_equipo = codigo_equipo.strip().upper()

    def validar_parametros(self, duracion: int) -> None:
        if isinstance(duracion, bool) or not isinstance(duracion, int) or not (1 <= duracion <= 30):
            raise ErrorValidacionDato("El alquiler de equipo debe ser de 1 a 30 días.")

    def calcular_costo_base(self, duracion: int) -> float:
        self.validar_parametros(duracion)
        return self.tarifa_base * duracion

    def describir(self) -> str:
        return f"Alquiler de Equipo [{self.codigo_equipo}] (tarifa/día: ${self.tarifa_base:,.2f})"


class AsesoriaEspecializada(Servicio):
    """Asesoría especializada (sesiones)."""

    def __init__(self, id_entidad: str, nombre: str, tarifa_sesion: float, especialidad: str, disponible: bool = True) -> None:
        super().__init__(id_entidad, nombre, tarifa_sesion, disponible)
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise ErrorValidacionDato("La especialidad de la asesoría es obligatoria.")
        self.especialidad = especialidad.strip()

    def validar_parametros(self, duracion: int) -> None:
        if isinstance(duracion, bool) or not isinstance(duracion, int) or not (1 <= duracion <= 15):
            raise ErrorValidacionDato("La cantidad de sesiones de asesoría debe estar entre 1 y 15.")

    def calcular_costo_base(self, duracion: int) -> float:
        self.validar_parametros(duracion)
        return self.tarifa_base * duracion

    def describir(self) -> str:
        return f"Asesoría Especializada en {self.especialidad} (tarifa/sesión: ${self.tarifa_base:,.2f})"


# =====================================================================
# 5. CLASE RESERVA
# =====================================================================
class Reserva(EntidadBase):
    ESTADOS_VALIDOS = {"PENDIENTE", "CONFIRMADA", "CANCELADA", "PROCESADA"}

    def __init__(self, id_entidad: str, cliente: Cliente, servicio: Servicio, duracion: int) -> None:
        super().__init__(id_entidad)
        if not isinstance(cliente, Cliente):
            raise ErrorReservaInvalida("Se requiere un objeto Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ErrorReservaInvalida("Se requiere un objeto Servicio válido.")
        if not servicio.disponible:
            raise ErrorServicioNoDisponible(f"El servicio '{servicio.nombre}' no está disponible.")

        servicio.validar_parametros(duracion)
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = "PENDIENTE"
        self.monto_total = servicio.calcular_costo(duracion)

    def confirmar(self) -> None:
        if self.estado == "CANCELADA":
            raise ErrorOperacionNoPermitida("No se puede confirmar una reserva cancelada.")
        if self.estado == "PROCESADA":
            raise ErrorOperacionNoPermitida("La reserva ya fue procesada.")
        self.estado = "CONFIRMADA"

    def cancelar(self) -> None:
        if self.estado == "PROCESADA":
            raise ErrorOperacionNoPermitida("No se puede cancelar una reserva ya procesada.")
        if self.estado == "CANCELADA":
            raise ErrorOperacionNoPermitida("La reserva ya está cancelada.")
        self.estado = "CANCELADA"
        self.servicio.disponible = True

    def procesar(self, impuesto_pct: float = 0.0, descuento_pct: float = 0.0) -> float:
        if self.estado != "CONFIRMADA":
            raise ErrorOperacionNoPermitida(
                f"Solo se pueden procesar reservas CONFIRMADAS. Estado actual: {self.estado}."
            )
        try:
            self.monto_total = self.servicio.calcular_costo(
                self.duracion, impuesto_pct=impuesto_pct, descuento_pct=descuento_pct
            )
        except ErrorValidacionDato as exc:
            raise ErrorReservaInvalida("Error al calcular el monto final durante el procesamiento.") from exc

        self.estado = "PROCESADA"
        self.servicio.disponible = False
        return self.monto_total

    def resumen(self) -> str:
        return (
            f"Reserva [{self.id_entidad}] | Estado: {self.estado} | "
            f"Cliente: {self.cliente.nombre} | Servicio: {self.servicio.nombre} | "
            f"Duración: {self.duracion} | Total: ${self.monto_total:,.2f}"
        )


# =====================================================================
# 6. SISTEMA GESTOR (LISTAS EN MEMORIA + LOGS + EXCEPCIONES)
# =====================================================================
class SistemaGestionSoftwareFJ:
    def __init__(self, archivo_log: str = "software_fj.log") -> None:
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []
        self.logger = RegistradorLogs(archivo_log)

    def _buscar_cliente(self, id_cliente: str) -> Cliente:
        for c in self.clientes:
            if c.id_entidad == id_cliente.strip().upper():
                return c
        raise ErrorReservaInvalida(f"Cliente con ID '{id_cliente}' no encontrado.")

    def _buscar_servicio(self, id_servicio: str) -> Servicio:
        for s in self.servicios:
            if s.id_entidad == id_servicio.strip().upper():
                return s
        raise ErrorReservaInvalida(f"Servicio con ID '{id_servicio}' no encontrado.")

    def _buscar_reserva(self, id_reserva: str) -> Reserva:
        for r in self.reservas:
            if r.id_entidad == id_reserva.strip().upper():
                return r
        raise ErrorReservaInvalida(f"Reserva con ID '{id_reserva}' no encontrada.")

    def registrar_cliente(self, id_cliente: str, nombre: str, documento: str, correo: str) -> Cliente:
        if any(c.id_entidad == id_cliente.strip().upper() for c in self.clientes):
            raise ErrorValidacionDato(f"Ya existe un cliente con ID '{id_cliente}'.")
        cliente = Cliente(id_cliente, nombre, documento, correo)
        self.clientes.append(cliente)
        return cliente

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        if not isinstance(servicio, Servicio):
            raise ErrorValidacionDato("El objeto proporcionado no es un Servicio válido.")
        if any(s.id_entidad == servicio.id_entidad for s in self.servicios):
            raise ErrorValidacionDato(f"Ya existe un servicio con ID '{servicio.id_entidad}'.")
        self.servicios.append(servicio)
        return servicio

    def crear_reserva(self, id_reserva: str, id_cliente: str, id_servicio: str, duracion: int) -> Reserva:
        if any(r.id_entidad == id_reserva.strip().upper() for r in self.reservas):
            raise ErrorReservaInvalida(f"Ya existe una reserva con ID '{id_reserva}'.")
        try:
            cliente = self._buscar_cliente(id_cliente)
            servicio = self._buscar_servicio(id_servicio)
            reserva = Reserva(id_reserva, cliente, servicio, duracion)
        except ErrorSistemaSoftwareFJ as exc:
            raise ErrorReservaInvalida(f"No se pudo crear la reserva '{id_reserva}'.") from exc

        self.reservas.append(reserva)
        return reserva

    def ejecutar_operacion(self, descripcion: str, accion):
        print(f"\n--- {descripcion} ---")
        error_ocurrido = False
        resultado = None
        try:
            resultado = accion()
        except ErrorSistemaSoftwareFJ as exc:
            error_ocurrido = True
            causa = f" (Causa: {exc.__cause__})" if exc.__cause__ else ""
            mensaje = f"{descripcion} -> {type(exc).__name__}: {exc}{causa}"
            self.logger.registrar("ERROR", mensaje)
            print(f"[ERROR CONTROLADO] {mensaje}")
        except Exception as exc:
            error_ocurrido = True
            mensaje = f"{descripcion} -> Error inesperado {type(exc).__name__}: {exc}"
            self.logger.registrar("CRITICAL", mensaje)
            print(f"[ERROR INESPERADO] {mensaje}")
        else:
            self.logger.registrar("INFO", f"{descripcion} -> Éxito.")
            print(f"[OK] Completado correctamente.")
        finally:
            estado_fin = "con error registrado" if error_ocurrido else "sin errores"
            print(f"[FIN OPERACIÓN] Estado: {estado_fin}.")
        return resultado


# =====================================================================
# 7. SIMULACIÓN DE MÁS DE 10 OPERACIONES (CASOS VÁLIDOS E INVÁLIDOS)
# =====================================================================
def simular_sistema() -> None:
    sistema = SistemaGestionSoftwareFJ("software_fj.log")

    # 1. Registro válido de cliente
    sistema.ejecutar_operacion(
        "Op 1: Registrar cliente válido",
        lambda: sistema.registrar_cliente("C-01", "Juan Pérez", "1052345678", "juan.perez@correo.com"),
    )

    # 2. Intento de registro inválido de cliente (correo mal formado)
    sistema.ejecutar_operacion(
        "Op 2: Intento de registrar cliente con correo inválido",
        lambda: sistema.registrar_cliente("C-02", "Ana Gómez", "98765432", "correo_sin_arroba"),
    )

    # 3. Creación válida de servicio ReservaSala
    sistema.ejecutar_operacion(
        "Op 3: Registrar servicio ReservaSala válido",
        lambda: sistema.registrar_servicio(ReservaSala("S-01", "Sala Conferencias A", 50000.0, 12)),
    )

    # 4. Intento de creación incorrecta de servicio (tarifa negativa)
    sistema.ejecutar_operacion(
        "Op 4: Intento de crear servicio con tarifa inválida",
        lambda: sistema.registrar_servicio(AlquilerEquipo("S-02", "Proyector HD", -15000.0, "EQ-101")),
    )

    # 5. Creación válida de servicio AlquilerEquipo
    sistema.ejecutar_operacion(
        "Op 5: Registrar servicio AlquilerEquipo válido",
        lambda: sistema.registrar_servicio(AlquilerEquipo("S-03", "Estación Trabajo", 80000.0, "EQ-205")),
    )

    # 6. Creación válida de servicio AsesoriaEspecializada
    sistema.ejecutar_operacion(
        "Op 6: Registrar servicio AsesoriaEspecializada válido",
        lambda: sistema.registrar_servicio(AsesoriaEspecializada("S-04", "Arquitectura Cloud", 120000.0, "Cloud")),
    )

    # 7. Cálculo de costos con variantes/sobrecarga (impuestos, descuentos, ajustes)
    def probar_calculos():
        srv = sistema._buscar_servicio("S-01")
        c1 = srv.calcular_costo(3)
        c2 = srv.calcular_costo(3, impuesto_pct=19.0, descuento_pct=10.0, recargo_extra=10000.0)
        c3 = srv.aplicar_ajuste_especial(15.0)
        print(f"Base 3h: ${c1:,.2f} | Con ajuste/imp/desc: ${c2:,.2f} | Ajuste 15%: ${c3:,.2f}")

    sistema.ejecutar_operacion("Op 7: Calcular costos con variantes y sobrecarga", probar_calculos)

    # 8. Reserva exitosa
    sistema.ejecutar_operacion(
        "Op 8: Crear reserva exitosa R-01",
        lambda: sistema.crear_reserva("R-01", "C-01", "S-01", 4),
    )

    # 9. Confirmación y procesamiento de R-01
    def confirmar_y_procesar():
        res = sistema._buscar_reserva("R-01")
        res.confirmar()
        total = res.procesar(impuesto_pct=19.0, descuento_pct=5.0)
        print(f"Reserva R-01 procesada por: ${total:,.2f}")

    sistema.ejecutar_operacion("Op 9: Confirmar y procesar reserva R-01", confirmar_y_procesar)

    # 10. Intento de reserva fallida (duración inválida para AsesoriaEspecializada)
    sistema.ejecutar_operacion(
        "Op 10: Intento de reserva con duración inválida (50 sesiones)",
        lambda: sistema.crear_reserva("R-02", "C-01", "S-04", 50),
    )

    # 11. Crear segunda reserva R-02 válida y cancelarla
    def crear_y_cancelar():
        res2 = sistema.crear_reserva("R-02", "C-01", "S-03", 2)
        res2.cancelar()
        print(res2.resumen())

    sistema.ejecutar_operacion("Op 11: Crear reserva R-02 y cancelarla", crear_y_cancelar)

    # 12. Operación no permitida: intentar cancelar R-01 que ya está PROCESADA
    sistema.ejecutar_operacion(
        "Op 12: Intento de cancelar reserva ya PROCESADA (R-01)",
        lambda: sistema._buscar_reserva("R-01").cancelar(),
    )

    print("\n=== RESUMEN FINAL EN MEMORIA ===")
    for r in sistema.reservas:
        print(r.resumen())


if __name__ == "__main__":
    simular_sistema()