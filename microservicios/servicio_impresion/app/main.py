"""
Servicio de Impresión - PATRON MVC + COMMAND
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from datetime import datetime
import logging
from configuracion import configuration
from modelos import TicketRequest, ReporteRequest, ImpresionResponse
from servicios import ServicioImpresion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PATRON MVC - Controller principal
app = FastAPI(
    title="Servicio de Impresión - POS Core",
    description="Microservicio para gestión de impresión de tickets y reportes",
    version="1.0.0"
)

# PATRON SINGLETON: Servicio de impresión global
servicio_impresion = ServicioImpresion()

@app.get("/")
async def raiz():
    return {
        "servicio": "Impresión POS Core",
        "estado": "Funcionando",
        "version": "1.0.0"
    }

@app.get("/health")
async def salud():
    return {
        "estado": "Saludable",
        "servicio": "Impresión",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/imprimir/ticket", response_model=ImpresionResponse)
async def imprimir_ticket(ticket: TicketRequest, background_tasks: BackgroundTasks):
    """PATRON MVC - Controller: Endpoint para imprimir ticket"""
    try:
        # PATRON COMMAND: Crear comando de impresión
        trabajo_id = servicio_impresion.encolar_trabajo("ticket_venta", ticket.dict())
        
        # Procesar en background
        trabajo = {
            "id": trabajo_id,
            "tipo": "ticket_venta",
            "datos": ticket.dict(),
            "timestamp": datetime.now().isoformat()
        }
        background_tasks.add_task(servicio_impresion.procesar_impresion, trabajo)
        
        return ImpresionResponse(
            mensaje="Ticket enviado a impresión",
            id_trabajo=trabajo_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error al imprimir ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Error al imprimir: {str(e)}")

@app.post("/api/v1/imprimir/reporte", response_model=ImpresionResponse)
async def imprimir_reporte(reporte: ReporteRequest, background_tasks: BackgroundTasks):
    """PATRON MVC - Controller: Endpoint para imprimir reporte"""
    try:
        # PATRON COMMAND: Crear comando de impresión de reporte
        trabajo_id = servicio_impresion.encolar_trabajo("reporte", reporte.dict())
        
        trabajo = {
            "id": trabajo_id,
            "tipo": "reporte",
            "datos": reporte.dict(),
            "timestamp": datetime.now().isoformat()
        }
        background_tasks.add_task(servicio_impresion.procesar_impresion, trabajo)
        
        return ImpresionResponse(
            mensaje="Reporte enviado a impresión",
            id_trabajo=trabajo_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error al imprimir reporte: {e}")
        raise HTTPException(status_code=500, detail=f"Error al imprimir reporte: {str(e)}")

@app.get("/api/v1/impresion/estado")
async def estado_impresion():
    """PATRON MVC - Controller: Endpoint para estado de impresión"""
    try:
        # Obtener estado de la cola
        cola_length = servicio_impresion.redis_client.llen("cola_impresion")
        trabajos_recientes = servicio_impresion.redis_client.lrange("cola_impresion", 0, 4)
        
        return {
            "trabajos_en_cola": cola_length,
            "trabajos_recientes": trabajos_recientes,
            "impresora_conectada": True
        }
    except Exception as e:
        logger.error(f"Error al obtener estado: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estado: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)