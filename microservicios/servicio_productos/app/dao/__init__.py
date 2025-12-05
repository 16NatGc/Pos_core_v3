"""
Módulo DAO para el servicio de productos
Contiene las implementaciones del patrón Data Access Object
"""

from .producto_dao import ProductoDAO, DAOError

__all__ = ["ProductoDAO", "DAOError"]