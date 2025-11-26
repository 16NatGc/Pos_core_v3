# servicio_impresion/main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict
import json
from datetime import datetime

app = FastAPI(title="Servicio de Impresión")

class TicketRequest(BaseModel):
    productos: List[Dict]
    total: float
    cliente: str
    vendedor: str

@app.post("/imprimir/ticket")
async def imprimir_ticket(ticket: TicketRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(procesar_impresion, ticket.dict())
    return {"mensaje": "Ticket enviado a impresión"}

async def procesar_impresion(ticket_data: Dict):
    # Lógica de impresión
    print(f"Imprimiendo ticket: {ticket_data}")