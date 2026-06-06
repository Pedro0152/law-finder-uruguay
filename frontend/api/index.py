import sys
import os

# Agrega la carpeta 'backend' al principio del path para evitar conflictos con la carpeta 'api' local
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Importar la app de FastAPI desde backend/api/main.py
from api.main import app
