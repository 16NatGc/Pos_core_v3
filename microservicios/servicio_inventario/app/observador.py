"""
Sistema de notificaciones usando Observer Pattern
PATRON GOF OBSERVER: Para notificaciones desacopladas
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Observador(ABC):
    """
    Interfaz Observer del patrón Observer
    PATRON STRATEGY: Cada observador implementa su propia estrategia
    """
    
    @abstractmethod
    def actualizar(self, evento: str, datos: Dict[str, Any]):
        """Método abstracto para actualizar observadores"""
        pass

class NotificadorEmail(Observador):
    """Observador concreto para notificaciones por email"""
    
    def actualizar(self, evento: str, datos: Dict[str, Any]):
        try:
            logger.info(f"Notificación Email - Evento: {evento}")
            logger.info(f"Producto: {datos.get('nombre')}, Stock: {datos.get('stock')}")
        except Exception as e:
            logger.error(f"Error en notificación email: {str(e)}")

class NotificadorLog(Observador):
    """Observador concreto para registro en logs"""
    
    def actualizar(self, evento: str, datos: Dict[str, Any]):
        try:
            log_message = f"NOTIFICACION: {evento} | Producto: {datos.get('nombre')} | Stock: {datos.get('stock')}"
            logger.warning(log_message)
        except Exception as e:
            logger.error(f"Error en notificación de log: {str(e)}")

class SujetoStock:
    """
    Sujeto concreto del patrón Observer
    PATRON COMPOSITE: Mantiene lista de observadores
    """
    
    def __init__(self):
        self._observadores: List[Observador] = []
    
    def agregar_observador(self, observador: Observador):
        """Agrega un observador a la lista"""
        if observador not in self._observadores:
            self._observadores.append(observador)
    
    def eliminar_observador(self, observador: Observador):
        """Elimina un observador de la lista"""
        if observador in self._observadores:
            self._observadores.remove(observador)
    
    def notificar_observadores(self, evento: str, datos: Dict[str, Any]):
        """
        Notifica a todos los observadores registrados
        PATRON ITERATOR: Itera sobre todos los observadores
        """
        for observador in self._observadores:
            try:
                observador.actualizar(evento, datos)
            except Exception as e:
                logger.error(f"Error notificando observador: {str(e)}")
    
    def notificar_stock_bajo(self, producto: Dict[str, Any]):
        """Método específico para notificaciones de stock bajo"""
        self.notificar_observadores("stock_bajo", producto)

# Instancia global del sujeto - PATRON SINGLETON
sujeto_stock = SujetoStock()

# Configuración inicial de observadores
def inicializar_observadores():
    """PATRON FACTORY METHOD: Inicializa observadores por defecto"""
    sujeto_stock.agregar_observador(NotificadorLog())
    sujeto_stock.agregar_observador(NotificadorEmail())

# Inicializar al importar el módulo
inicializar_observadores()