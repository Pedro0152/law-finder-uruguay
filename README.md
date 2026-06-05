# Law Finder Uruguay 🇺🇾⚖️

Plataforma SaaS inteligente para búsqueda, análisis y consulta de normativa legal uruguaya, actualizada automáticamente desde fuentes oficiales del Estado.

## ¿Qué es?
Un sistema que permite a cualquier usuario consultar leyes, decretos, resoluciones y reglamentos del Uruguay usando lenguaje natural, obteniendo respuestas trazables y fundamentadas con citas a las fuentes oficiales vigentes.

## Funcionalidades
- 🔍 **Búsqueda híbrida**: Full-Text Search + Búsqueda Semántica (pgvector).
- 🤖 **Chat Jurídico AI (RAG)**: Pregunta en lenguaje natural, obtén respuestas con citas legales.
- 🕷️ **Scraping automático**: Actualización diaria desde IMPO y otras fuentes oficiales.
- 📋 **Panel Admin**: Control de trabajos de scraping, logs y estado del sistema.
- 📜 **Historial de versiones**: Seguimiento de modificaciones y derogaciones de normas.

## Stack Tecnológico
| Capa | Tecnología |
|------|-----------|
| Frontend | Next.js 16 (App Router, TypeScript) |
| Backend | Python, FastAPI |
| Base de Datos | PostgreSQL (Supabase) + pgvector |
| Scraping | BeautifulSoup + Requests |
| Cola de Tareas | Celery + Redis |
| Despliegue Frontend | Vercel |
| Despliegue Backend | VPS + Docker Compose + Nginx |

## Estructura del Proyecto
```
law-finder-uruguay/
├── frontend/           # Aplicación Next.js (Vercel)
│   ├── app/
│   │   ├── page.tsx        # Página principal y buscador
│   │   ├── chat/page.tsx   # Chat Legal AI
│   │   └── admin/page.tsx  # Panel Admin
├── backend-services/   # API FastAPI + Workers (VPS)
│   ├── api/main.py         # Endpoints FastAPI
│   ├── scraper/            # Scrapers por fuente
│   ├── nlp/rag_pipeline.py # Pipeline RAG (AI)
│   ├── workers/            # Celery + cron jobs
│   ├── db/schema.sql       # Esquema PostgreSQL
│   └── requirements.txt
├── docker/
│   └── docker-compose.yml  # Orquestación de servicios
├── deploy.sh           # Script de instalación para VPS
└── nginx.conf          # Reverse proxy config
```

## Configuración y Despliegue

### Variables de Entorno (`.env`)
```env
SUPABASE_URL=https://[TU-PROYECTO].supabase.co
SUPABASE_KEY=[TU-ANON-KEY]
POSTGRES_URL=[CONNECTION-STRING]
OPENAI_API_KEY=[TU-KEY]
REDIS_URL=redis://redis:6379/0
```

### Supabase / Base de Datos
1. Habilitar extensión: `CREATE EXTENSION IF NOT EXISTS vector;`
2. Ejecutar `backend-services/db/schema.sql` en el SQL Editor de Supabase.

### Backend (VPS)
```bash
bash deploy.sh           # Instala Docker, Nginx, Certbot
cd docker
docker compose up -d --build
```

### Frontend (Vercel)
El frontend se despliega automáticamente con `vercel --prod`.

## Aviso Legal
Este sistema brinda información jurídica automatizada basada exclusivamente en fuentes oficiales del Estado uruguayo. **No reemplaza el asesoramiento de un profesional del derecho.**
