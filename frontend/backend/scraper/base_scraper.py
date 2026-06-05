import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import hashlib
from datetime import datetime

class BaseScraper:
    """Clase base para scrapeadores de normativa legal uruguaya"""
    
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.session = requests.Session()
        # Header común para no ser bloqueados fácilmente
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def fetch_html(self, url: str) -> Optional[str]:
        """Obtiene el HTML de una URL de manera segura."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            # Forzar encoding si es necesario (IMPO usa a veces iso-8859-1)
            response.encoding = response.apparent_encoding
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def clean_text(self, text: str) -> str:
        """Sanitiza el texto, removiendo espacios extra y saltos múltiples."""
        if not text:
            return ""
        # Reemplazar múltiples espacios o saltos de línea por uno solo
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def generate_hash(self, content: str) -> str:
        """Genera un hash MD5 del contenido para control de versiones y duplicados."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def parse_articles(self, full_text: str) -> List[Dict]:
        """
        Método heurístico genérico para dividir un texto legal en artículos.
        Debe ser sobreescrito si la fuente tiene una estructura HTML clara.
        """
        articles = []
        # Buscar "Artículo 1", "Art. 1", "ARTÍCULO 1º" etc.
        pattern = re.compile(r'(Artículo\s+\d+|Art\.\s*\d+|ARTÍCULO\s+\d+º?)', re.IGNORECASE)
        splits = pattern.split(full_text)
        
        # El split genera [texto_previo, "Artículo 1", "texto_art_1", "Artículo 2", "texto_art_2"...]
        # El texto previo podría ser el preámbulo o considerandos.
        preamble = splits[0].strip()
        if preamble:
            articles.append({
                "numero": "Preámbulo",
                "texto": preamble
            })
            
        for i in range(1, len(splits) - 1, 2):
            art_num = splits[i].strip()
            art_text = splits[i+1].strip()
            articles.append({
                "numero": art_num,
                "texto": art_text
            })
            
        return articles

    def scrape_latest(self):
        """Método principal a implementar por cada scraper específico."""
        raise NotImplementedError("Debe implementarse en la clase hija")

