# Dockerfile CORREGIDO
FROM python:3.11-slim

# 1. Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Directorio de trabajo
WORKDIR /app

# 3. Copiar requirements
COPY requirements.txt .

# 4.CORRECCIÓN CRÍTICA: Instalar dlib SIN --no-binary
RUN pip install --no-cache-dir dlib==20.0.0

# 5. Instalar el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar aplicación
COPY . .

# 7. Crear directorios necesarios
RUN mkdir -p assets/imagenes_estudiantes assets/rostros_conocidos data logs

# 8. Exponer puerto
EXPOSE 8501

# 9. Comando para ejecutar
CMD ["streamlit", "run", "app_web.py", "--server.port=8501", "--server.address=0.0.0.0"]
# Configurar Python path para que encuentre los módulos
ENV PYTHONPATH=/app
