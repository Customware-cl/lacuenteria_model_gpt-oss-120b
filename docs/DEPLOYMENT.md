# Guía de Despliegue - Sistema Cuentería

## Requisitos del Sistema

### Hardware Mínimo
- **CPU:** 4 cores
- **RAM:** 8 GB (16 GB recomendado)
- **Disco:** 50 GB disponibles
- **GPU:** Opcional, pero recomendado para gpt-oss-120b

### Software
- **OS:** Ubuntu 20.04+ / Debian 11+
- **Python:** 3.8 o superior
- **Git:** 2.25+
- **Modelo LLM:** gpt-oss-120b instalado y funcionando

## Instalación Paso a Paso

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Customware-cl/lacuenteria_model_gpt-oss-120b.git
cd lacuenteria_model_gpt-oss-120b
```

### 2. Configurar Entorno Python

```bash
# Instalar Python y pip
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar gpt-oss-120b

El modelo gpt-oss-120b debe estar ejecutándose antes de iniciar Cuentería.

#### Opción A: Docker (Recomendado)

```bash
# Ejemplo de configuración Docker para gpt-oss-120b
docker run -d \
  --name gpt-oss-120b \
  -p 8080:8080 \
  -v /path/to/models:/models \
  --gpus all \
  gpt-oss-120b:latest \
  --model-path /models/gpt-oss-120b \
  --port 8080
```

#### Opción B: Instalación Local

```bash
# Instalar dependencias del modelo
pip install torch transformers accelerate

# Descargar modelo (ajustar según documentación de gpt-oss-120b)
python -c "from transformers import AutoModel; AutoModel.from_pretrained('gpt-oss-120b')"

# Iniciar servidor del modelo
python -m gpt_oss_server --port 8080
```

### 4. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar configuración
nano .env
```

Configuración mínima requerida:

```env
# Endpoint del modelo LLM
LLM_ENDPOINT=http://localhost:8080/v1/completions

# Configuración API
API_HOST=0.0.0.0
API_PORT=5000

# Origen permitido para CORS
CORS_ORIGINS=https://lacuenteria.cl
```

### 5. Verificar Instalación

```bash
# Verificar conexión con modelo LLM
python3 -c "
import sys
sys.path.insert(0, 'src')
from llm_client import get_llm_client
client = get_llm_client()
print('LLM disponible:', client.validate_connection())
"

# Verificar configuración
python3 -c "
import sys
sys.path.insert(0, 'src')
from config import validate_config
validate_config()
print('Configuración válida')
"
```

### 6. Iniciar el Sistema

#### Modo Desarrollo

```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar servidor
./start.sh
```

#### Modo Producción con Gunicorn

```bash
# Instalar Gunicorn
pip install gunicorn gevent

# Iniciar con workers
gunicorn -w 4 \
  -k gevent \
  --timeout 600 \
  -b 0.0.0.0:5000 \
  --chdir src \
  api_server:app
```

#### Modo Producción con Systemd

Crear archivo `/etc/systemd/system/cuenteria.service`:

```ini
[Unit]
Description=Cuenteria Story Generation System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/cuenteria
Environment="PATH=/home/ubuntu/cuenteria/venv/bin"
Environment="LLM_ENDPOINT=http://localhost:8080/v1/completions"
ExecStart=/home/ubuntu/cuenteria/venv/bin/gunicorn \
  -w 4 -k gevent --timeout 600 -b 0.0.0.0:5000 \
  --chdir src api_server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cuenteria
sudo systemctl start cuenteria
sudo systemctl status cuenteria
```

## Configuración de Producción

### 1. Nginx como Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.cuenteria.local;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts largos para procesamiento
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
}
```

### 2. SSL con Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d api.cuenteria.local

# Renovación automática
sudo certbot renew --dry-run
```

### 3. Monitoreo

#### Con Prometheus

Agregar endpoint de métricas en `api_server.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest

story_counter = Counter('stories_processed', 'Total stories processed')
processing_time = Histogram('story_processing_seconds', 'Time to process story')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

#### Logs con ELK Stack

```bash
# Configurar Filebeat para enviar logs
filebeat.inputs:
- type: log
  paths:
    - /home/ubuntu/cuenteria/runs/*/logs/*.log
  json.keys_under_root: true
  
output.elasticsearch:
  hosts: ["localhost:9200"]
```

### 4. Backup y Recuperación

```bash
# Script de backup
#!/bin/bash
BACKUP_DIR="/backups/cuenteria"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup de historias completadas
tar -czf "$BACKUP_DIR/stories_$DATE.tar.gz" /home/ubuntu/cuenteria/runs/

# Limpiar backups antiguos (mantener 30 días)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Agregar a crontab:

```bash
# Backup diario a las 2 AM
0 2 * * * /home/ubuntu/cuenteria/backup.sh
```

## Optimización de Rendimiento

### 1. Configuración del Modelo LLM

```python
# En config.py, ajustar según recursos disponibles
LLM_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 4000,
    "timeout": 60,
    # Agregar configuración de batch si el modelo lo soporta
    "batch_size": 1,
    "max_concurrent_requests": 3
}
```

### 2. Cache de Redis (Opcional)

```bash
# Instalar Redis
sudo apt install redis-server

# En requirements.txt agregar
redis==4.5.0

# Configurar cache en agent_runner.py
import redis
cache = redis.Redis(host='localhost', port=6379, decode_responses=True)
```

### 3. Límites de Sistema

```bash
# En /etc/security/limits.conf
ubuntu soft nofile 65535
ubuntu hard nofile 65535

# En /etc/sysctl.conf
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
```

## Troubleshooting

### Problema: "No se puede conectar al modelo LLM"

**Solución:**
```bash
# Verificar que el modelo está ejecutándose
curl http://localhost:8080/health

# Verificar logs del modelo
docker logs gpt-oss-120b

# Ajustar endpoint en .env
LLM_ENDPOINT=http://localhost:8080/v1/completions
```

### Problema: "Timeout en procesamiento de historias"

**Solución:**
```bash
# Aumentar timeouts en .env
LLM_TIMEOUT=120
STORY_TIMEOUT=900

# Ajustar workers de Gunicorn
gunicorn -w 2 --timeout 900 ...
```

### Problema: "Error de memoria"

**Solución:**
```bash
# Reducir concurrencia en .env
MAX_CONCURRENT_STORIES=1

# Reducir max_tokens
LLM_MAX_TOKENS=2000

# Aumentar swap si es necesario
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Problema: "QA scores consistentemente bajos"

**Solución:**
```python
# Ajustar temperatura en config.py
LLM_CONFIG["temperature"] = 0.8  # Más creatividad

# Reducir umbral mínimo
QUALITY_THRESHOLDS["min_qa_score"] = 3.5

# Aumentar reintentos
QUALITY_THRESHOLDS["max_retries"] = 3
```

### Logs y Debugging

```bash
# Ver logs del sistema
tail -f /home/ubuntu/cuenteria/cuenteria.log

# Ver logs de una historia específica
cat /home/ubuntu/cuenteria/runs/{story_id}/logs/*.log | jq

# Ver estado del servicio
sudo systemctl status cuenteria
sudo journalctl -u cuenteria -f

# Modo debug
DEBUG=True python3 src/api_server.py
```

## Seguridad

### 1. Firewall

```bash
# Configurar UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp  # API (solo si es necesario externamente)
sudo ufw enable
```

### 2. Rate Limiting

Agregar en `api_server.py`:

```python
from flask_limiter import Limiter
limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route('/api/stories/create')
@limiter.limit("10 per hour")
def create_story():
    # ...
```

### 3. Validación de Entrada

```python
# Validar tamaño de brief
MAX_BRIEF_SIZE = 50000  # caracteres

if len(json.dumps(brief)) > MAX_BRIEF_SIZE:
    return jsonify({"error": "Brief demasiado grande"}), 400
```

## Mantenimiento

### Limpieza Automática

```bash
# Crear script cleanup.sh
#!/bin/bash
# Limpiar historias antiguas (más de 30 días)
find /home/ubuntu/cuenteria/runs -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \;

# Agregar a crontab (ejecutar diariamente a las 3 AM)
0 3 * * * /home/ubuntu/cuenteria/cleanup.sh
```

### Actualizaciones

```bash
# Actualizar código
cd /home/ubuntu/cuenteria
git pull origin main

# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Reiniciar servicio
sudo systemctl restart cuenteria
```

## Contacto y Soporte

- **Repositorio:** https://github.com/Customware-cl/lacuenteria_model_gpt-oss-120b
- **Issues:** https://github.com/Customware-cl/lacuenteria_model_gpt-oss-120b/issues
- **Email:** soporte@customware.cl