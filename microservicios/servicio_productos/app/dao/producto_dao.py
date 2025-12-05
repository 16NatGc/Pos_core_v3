"""
Data Access Object (DAO) para Productos
Implementa el patrón DAO para abstraer completamente el acceso a MongoDB
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import logging

# Configurar logging
logger = logging.getLogger(__name__)


class DAOError(Exception):
    """Excepción personalizada para errores del DAO"""
    pass


class ProductoDAO:
    """
    Data Access Object para la entidad Producto
    
    Responsabilidades:
    - Abstraer todas las operaciones de base de datos
    - Manejar conversiones de tipos (ObjectId <-> str)
    - Proporcionar una interfaz consistente para el acceso a datos
    - Aislar el código de negocio de los detalles de MongoDB
    """
    
    def __init__(self, db_connection):
        """
        Inicializa el DAO con una conexión a la base de datos
        
        Args:
            db_connection: Conexión a MongoDB
        """
        self.db = db_connection
        self.collection_name = "productos"
    
    def _get_collection(self):
        """Obtiene la colección de productos de MongoDB"""
        return self.db[self.collection_name]
    
    def _convert_to_dict(self, producto_doc):
        """
        Convierte un documento de MongoDB a un diccionario Python
        
        Args:
            producto_doc: Documento de MongoDB
            
        Returns:
            Diccionario con el ID como string
        """
        if not producto_doc:
            return None
        
        # Convertir ObjectId a string
        producto_dict = dict(producto_doc)
        producto_dict['id'] = str(producto_dict.pop('_id'))
        
        # Convertir fechas a string ISO format
        for date_field in ['creado_en', 'actualizado_en']:
            if date_field in producto_dict and isinstance(producto_dict[date_field], datetime):
                producto_dict[date_field] = producto_dict[date_field].isoformat()
        
        return producto_dict
    
    def crear(self, producto_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo producto en la base de datos
        
        Args:
            producto_data: Diccionario con los datos del producto
            
        Returns:
            Diccionario con el producto creado incluyendo ID
            
        Raises:
            DAOError: Si hay un error en la operación de base de datos
            ValueError: Si los datos no son válidos
        """
        try:
            collection = self._get_collection()
            
            # Validaciones básicas
            if not producto_data.get('nombre'):
                raise ValueError("El nombre del producto es requerido")
            
            if not producto_data.get('codigo'):
                raise ValueError("El código del producto es requerido")
            
            if producto_data.get('precio', 0) <= 0:
                raise ValueError("El precio debe ser mayor a 0")
            
            # Verificar que el código no exista
            codigo_existente = collection.find_one({'codigo': producto_data['codigo']})
            if codigo_existente:
                raise ValueError(f"El código {producto_data['codigo']} ya existe")
            
            # Agregar metadatos
            producto_data['activo'] = True
            producto_data['creado_en'] = datetime.utcnow()
            producto_data['actualizado_en'] = datetime.utcnow()
            
            # Insertar en la base de datos
            result = collection.insert_one(producto_data)
            
            # Obtener el documento insertado
            producto_insertado = collection.find_one({'_id': result.inserted_id})
            
            logger.info(f"Producto creado exitosamente: {producto_data['codigo']}")
            return self._convert_to_dict(producto_insertado)
            
        except ValueError as ve:
            logger.warning(f"Error de validación al crear producto: {str(ve)}")
            raise ve
        except Exception as e:
            logger.error(f"Error DAO al crear producto: {str(e)}")
            raise DAOError(f"No se pudo crear el producto: {str(e)}")
    
    def obtener_por_id(self, producto_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un producto por su ID
        
        Args:
            producto_id: ID del producto como string
            
        Returns:
            Diccionario con los datos del producto o None si no existe
        """
        try:
            collection = self._get_collection()
            
            # Validar formato del ID
            if not ObjectId.is_valid(producto_id):
                raise ValueError("ID de producto inválido")
            
            # Buscar el producto
            producto_doc = collection.find_one({'_id': ObjectId(producto_id)})
            
            if not producto_doc:
                logger.debug(f"Producto no encontrado: {producto_id}")
                return None
            
            logger.debug(f"Producto encontrado: {producto_id}")
            return self._convert_to_dict(producto_doc)
            
        except ValueError as ve:
            logger.warning(f"ID inválido: {str(ve)}")
            raise ve
        except Exception as e:
            logger.error(f"Error DAO al obtener producto {producto_id}: {str(e)}")
            raise DAOError(f"No se pudo obtener el producto: {str(e)}")
    
    def obtener_todos(self, filtros: Optional[Dict] = None, 
                     pagina: int = 1, por_pagina: int = 10) -> Dict[str, Any]:
        """
        Obtiene todos los productos con paginación y filtros
        
        Args:
            filtros: Diccionario con filtros de búsqueda
            pagina: Número de página (comienza en 1)
            por_pagina: Cantidad de elementos por página
            
        Returns:
            Diccionario con productos y metadatos de paginación
        """
        try:
            collection = self._get_collection()
            
            if filtros is None:
                filtros = {}
            
            # Filtro por defecto: solo productos activos
            if 'activo' not in filtros:
                filtros['activo'] = True
            
            # Calcular skip para paginación
            skip = (pagina - 1) * por_pagina
            
            # Contar total de documentos
            total = collection.count_documents(filtros)
            
            # Obtener documentos paginados
            cursor = collection.find(filtros).skip(skip).limit(por_pagina)
            
            # Convertir documentos
            productos = [self._convert_to_dict(doc) for doc in cursor]
            
            # Calcular metadatos de paginación
            total_paginas = (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
            
            logger.debug(f"Obtenidos {len(productos)} productos, página {pagina}")
            
            return {
                'productos': productos,
                'paginacion': {
                    'pagina_actual': pagina,
                    'por_pagina': por_pagina,
                    'total_productos': total,
                    'total_paginas': total_paginas
                }
            }
            
        except Exception as e:
            logger.error(f"Error DAO al obtener productos: {str(e)}")
            raise DAOError(f"No se pudo obtener los productos: {str(e)}")
    
    def obtener_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un producto por su código único
        
        Args:
            codigo: Código del producto
            
        Returns:
            Diccionario con los datos del producto o None
        """
        try:
            collection = self._get_collection()
            
            producto_doc = collection.find_one({
                'codigo': codigo,
                'activo': True
            })
            
            return self._convert_to_dict(producto_doc)
            
        except Exception as e:
            logger.error(f"Error DAO al buscar producto por código {codigo}: {str(e)}")
            raise DAOError(f"No se pudo buscar el producto: {str(e)}")
    
    def actualizar(self, producto_id: str, 
                  datos_actualizados: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Actualiza un producto existente
        
        Args:
            producto_id: ID del producto a actualizar
            datos_actualizados: Diccionario con los campos a actualizar
            
        Returns:
            Diccionario con el producto actualizado o None si no existe
        """
        try:
            collection = self._get_collection()
            
            # Validar ID
            if not ObjectId.is_valid(producto_id):
                raise ValueError("ID de producto inválido")
            
            # No permitir actualización del ID
            if 'id' in datos_actualizados:
                del datos_actualizados['id']
            if '_id' in datos_actualizados:
                del datos_actualizados['_id']
            
            # Si se actualiza el código, verificar que no exista
            if 'codigo' in datos_actualizados:
                producto_existente = collection.find_one({
                    'codigo': datos_actualizados['codigo'],
                    '_id': {'$ne': ObjectId(producto_id)}
                })
                if producto_existente:
                    raise ValueError(f"El código {datos_actualizados['codigo']} ya está en uso")
            
            # Agregar timestamp de actualización
            datos_actualizados['actualizado_en'] = datetime.utcnow()
            
            # Realizar la actualización
            result = collection.find_one_and_update(
                {'_id': ObjectId(producto_id)},
                {'$set': datos_actualizados},
                return_document=True  # Retornar el documento actualizado
            )
            
            if not result:
                logger.warning(f"Producto no encontrado para actualizar: {producto_id}")
                return None
            
            logger.info(f"Producto actualizado: {producto_id}")
            return self._convert_to_dict(result)
            
        except ValueError as ve:
            logger.warning(f"Error de validación al actualizar producto: {str(ve)}")
            raise ve
        except Exception as e:
            logger.error(f"Error DAO al actualizar producto {producto_id}: {str(e)}")
            raise DAOError(f"No se pudo actualizar el producto: {str(e)}")
    
    def eliminar(self, producto_id: str) -> bool:
        """
        Elimina (soft delete) un producto
        
        Args:
            producto_id: ID del producto a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        try:
            collection = self._get_collection()
            
            if not ObjectId.is_valid(producto_id):
                raise ValueError("ID de producto inválido")
            
            # Soft delete: marcar como inactivo
            result = collection.update_one(
                {'_id': ObjectId(producto_id)},
                {'$set': {
                    'activo': False,
                    'actualizado_en': datetime.utcnow()
                }}
            )
            
            if result.modified_count > 0:
                logger.info(f"Producto eliminado (soft delete): {producto_id}")
                return True
            else:
                logger.warning(f"Producto no encontrado para eliminar: {producto_id}")
                return False
                
        except ValueError as ve:
            logger.warning(f"ID inválido al eliminar producto: {str(ve)}")
            raise ve
        except Exception as e:
            logger.error(f"Error DAO al eliminar producto {producto_id}: {str(e)}")
            raise DAOError(f"No se pudo eliminar el producto: {str(e)}")
    
    def actualizar_stock(self, producto_id: str, cantidad: int) -> Optional[Dict[str, Any]]:
        """
        Actualiza el stock de un producto (incrementa o decrementa)
        
        Args:
            producto_id: ID del producto
            cantidad: Cantidad a ajustar (positivo para aumentar, negativo para disminuir)
            
        Returns:
            Producto actualizado o None si no existe
        """
        try:
            collection = self._get_collection()
            
            if not ObjectId.is_valid(producto_id):
                raise ValueError("ID de producto inválido")
            
            # Primero verificar que existe
            producto = collection.find_one({'_id': ObjectId(producto_id), 'activo': True})
            if not producto:
                logger.warning(f"Producto no encontrado para actualizar stock: {producto_id}")
                return None
            
            # Verificar que no quede stock negativo
            nuevo_stock = producto.get('stock', 0) + cantidad
            if nuevo_stock < 0:
                raise ValueError("Stock no puede ser negativo")
            
            # Actualizar stock
            result = collection.find_one_and_update(
                {'_id': ObjectId(producto_id)},
                {'$set': {
                    'stock': nuevo_stock,
                    'actualizado_en': datetime.utcnow()
                }},
                return_document=True
            )
            
            logger.info(f"Stock actualizado para producto {producto_id}: {cantidad} unidades")
            return self._convert_to_dict(result)
            
        except ValueError as ve:
            logger.warning(f"Error de validación al actualizar stock: {str(ve)}")
            raise ve
        except Exception as e:
            logger.error(f"Error DAO al actualizar stock para producto {producto_id}: {str(e)}")
            raise DAOError(f"No se pudo actualizar el stock: {str(e)}")
    
    def buscar(self, consulta: str, campo: str = 'nombre') -> List[Dict[str, Any]]:
        """
        Busca productos por texto en un campo específico
        
        Args:
            consulta: Texto a buscar
            campo: Campo donde buscar (nombre, descripcion, etc.)
            
        Returns:
            Lista de productos que coinciden con la búsqueda
        """
        try:
            collection = self._get_collection()
            
            # Crear expresión regular para búsqueda case-insensitive
            regex = {'$regex': consulta, '$options': 'i'}
            
            cursor = collection.find({
                campo: regex,
                'activo': True
            }).limit(50)  # Limitar resultados
            
            productos = [self._convert_to_dict(doc) for doc in cursor]
            logger.debug(f"Búsqueda '{consulta}' en campo '{campo}': {len(productos)} resultados")
            return productos
            
        except Exception as e:
            logger.error(f"Error DAO al buscar productos: {str(e)}")
            raise DAOError(f"No se pudo realizar la búsqueda: {str(e)}")
    
    def obtener_productos_bajo_stock(self, limite_stock: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene productos con stock por debajo del límite especificado
        
        Args:
            limite_stock: Límite de stock para alerta
            
        Returns:
            Lista de productos con stock bajo
        """
        try:
            collection = self._get_collection()
            
            cursor = collection.find({
                'stock': {'$lt': limite_stock},
                'activo': True
            }).sort('stock', 1)  # Ordenar por stock ascendente
            
            productos = [self._convert_to_dict(doc) for doc in cursor]
            logger.info(f"Encontrados {len(productos)} productos con stock bajo (<{limite_stock})")
            return productos
            
        except Exception as e:
            logger.error(f"Error DAO al obtener productos bajo stock: {str(e)}")
            raise DAOError(f"No se pudo obtener productos bajo stock: {str(e)}")