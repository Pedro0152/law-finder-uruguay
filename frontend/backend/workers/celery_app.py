import os
from celery import Celery
from celery.schedules import crontab

# Configuración de broker (Redis)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    'law_finder_workers',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['workers.tasks']
)

# Configuración adicional de Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Montevideo',
    enable_utc=True,
)

# Programación de tareas recurrentes (Cron)
app.conf.beat_schedule = {
    'scrape-impo-diario-oficial-daily': {
        'task': 'workers.tasks.scrape_daily_norms',
        # Ejecutar todos los días a las 04:00 AM
        'schedule': crontab(hour=4, minute=0),
        'args': ('IMPO_DIARIO_OFICIAL',)
    },
}

if __name__ == '__main__':
    app.start()
