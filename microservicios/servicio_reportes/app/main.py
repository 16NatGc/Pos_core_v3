"""
Servicio de Reportes - PATRON MVC + GOF
"""

from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime, timedelta
from typing import List
import logging
from configuracion import configuration
from modelos import ReporteVentas, ReporteInventario, ReporteGeneral
from servicios import ReporteService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PATRON MVC - Controller principal
app = FastAPI(
    title="Servicio de Reportes - POS Core",
    description="Microservicio para generación de reportes",
    version="1.0.0"
)

# PATRON DEPENDENCY INJECTION
def get_reporte_service():
    return ReporteService()

@app.get("/")
async def raiz():
    return {
        "servicio": "Reportes POS Core",
        "estado": "Funcionando",
        "version": "1.0.0"
    }

@app.get("/health")
async def salud():
    return {
        "estado": "Saludable",
        "servicio": "Reportes",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/reportes/ventas", response_model=ReporteVentas)
async def obtener_reporte_ventas(
    dias: int = 7,
    reporte_service: ReporteService = Depends(get_reporte_service)
):
    """PATRON MVC - Controller: Endpoint para reporte de ventas"""
    try:
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=dias)
        
        reporte = await reporte_service.generar_reporte_ventas(fecha_inicio, fecha_fin)
        return reporte
    except Exception as e:
        logger.error(f"Error generando reporte de ventas: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte")

@app.get("/api/v1/reportes/inventario", response_model=ReporteInventario)
async def obtener_reporte_inventario(
    reporte_service: ReporteService = Depends(get_reporte_service)
):
    """PATRON MVC - Controller: Endpoint para reporte de inventario"""
    try:
        reporte = await reporte_service.generar_reporte_inventario()
        return reporte
    except Exception as e:
        logger.error(f"Error generando reporte de inventario: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte")

@app.get("/api/v1/reportes/general", response_model=ReporteGeneral)
async def obtener_reporte_general(
    dias: int = 7,
    reporte_service: ReporteService = Depends(get_reporte_service)
):
    """PATRON MVC - Controller: Endpoint para reporte general compuesto"""
    try:
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=dias)
        
        # PATRON COMPOSITE: Reporte general compuesto de otros reportes
        reporte_ventas = await reporte_service.generar_reporte_ventas(fecha_inicio, fecha_fin)
        reporte_inventario = await reporte_service.generar_reporte_inventario()
        
        return ReporteGeneral(
            ventas=reporte_ventas,
            inventario=reporte_inventario,
            fecha_generacion=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error generando reporte general: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)