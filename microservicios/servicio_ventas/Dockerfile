FROM python:3.11-slim

WORKDIR /app

# Copiar requirements primero para cache de dependencias
COPY requisitos.txt .
RUN pip install --no-cache-dir -r requisitos.txt

# Copiar TODO el contenido del microservicio
COPY . .

# El main.py está en la carpeta app/, así que ejecutamos desde ahí
CMD ["python", "app/main.py"]