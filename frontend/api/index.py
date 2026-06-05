import sys
import os

# Agrega la carpeta 'backend' al path de Python para que FastAPI pueda resolver sus propios imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Importar la app de FastAPI desde backend/api/main.py
from api.main import app
