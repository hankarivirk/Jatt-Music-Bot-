FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    fonts-liberation \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/assets/fonts && \
    cp /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf \
       /app/assets/fonts/Roboto-Regular.ttf 2>/dev/null || true && \
    cp /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf \
       /app/assets/fonts/Roboto-Bold.ttf 2>/dev/null || true && \
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
       /app/assets/fonts/Roboto-Regular.ttf 2>/dev/null || true && \
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
       /app/assets/fonts/Roboto-Bold.ttf 2>/dev/null || true

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc g++ make libffi-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/* /root/.cache
    
COPY . .

CMD ["python", "main.py"]
