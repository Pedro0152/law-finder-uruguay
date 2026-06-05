#!/bin/bash
set -e

# Imprimir comandos y salir si hay error
echo "Iniciando configuración de VPS para Law Finder Uruguay..."

# 1. Actualizar sistema e instalar utilidades básicas
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl wget git nginx certbot python3-certbot-nginx

# 2. Instalar Docker si no existe
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# 3. Instalar Docker Compose v2 (si no existe)
if ! docker compose version &> /dev/null; then
    echo "Docker Compose plugin no está disponible. Asegúrate de tener la versión más reciente de Docker."
fi

# 4. Iniciar y habilitar servicios
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl enable nginx
sudo systemctl start nginx

# Mensaje final
echo "================================================================"
echo "✅ Instalación de dependencias completada."
echo "================================================================"
echo ""
echo "Siguientes Pasos Manuales:"
echo "1. Clona tu repositorio en esta máquina: git clone [URL_REPO]"
echo "2. Crea el archivo .env dentro de la carpeta /backend-services basado en el .env.example"
echo "3. Copia el archivo nginx.conf a /etc/nginx/sites-available/lawfinder"
echo "4. Ejecuta: sudo ln -s /etc/nginx/sites-available/lawfinder /etc/nginx/sites-enabled/"
echo "5. Reinicia Nginx: sudo systemctl restart nginx"
echo "6. Genera SSL con Certbot: sudo certbot --nginx -d tu-dominio.com"
echo "7. Entra a la carpeta /docker y ejecuta: docker compose up -d --build"
echo "================================================================"
