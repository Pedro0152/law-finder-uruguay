from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import re
from datetime import datetime

class ImpoScraper(BaseScraper):
    """Scraper para la Dirección Nacional de Impresiones y Publicaciones Oficiales (IMPO)"""

    def __init__(self):
        super().__init__(
            source_name="IMPO", 
            base_url="https://www.impo.com.uy"
        )

    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        """Extrae metadatos comunes del HTML de una norma en IMPO."""
        metadata = {
            "numero": None,
            "tipo": None,
            "titulo": None,
            "fecha_promulgacion": None,
            "estado_vigencia": "Desconocida"
        }
        
        # Ejemplo: Buscar el título principal (suele estar en <h1> o div específico)
        title_tag = soup.find('h1', class_=re.compile('titulo|title', re.I))
        if title_tag:
            metadata["titulo"] = self.clean_text(title_tag.text)
            
            # Inferir tipo a partir del título
            texto_titulo = metadata["titulo"].upper()
            if "LEY N" in texto_titulo:
                metadata["tipo"] = "Ley"
                match = re.search(r'N°?\s*(\d+\.?\d*)', texto_titulo)
                if match:
                    metadata["numero"] = match.group(1).replace(".", "")
            elif "DECRETO" in texto_titulo:
                metadata["tipo"] = "Decreto"
            else:
                metadata["tipo"] = "Otra"

        # Fechas (a menudo en span con clase "fecha" o texto específico)
        # Esto requiere inspeccionar el DOM real de IMPO
        fechas_text = soup.find(text=re.compile(r'Promulgación:', re.I))
        if fechas_text:
            match = re.search(r'(\d{2}/\d{2}/\d{4})', fechas_text)
            if match:
                # Convertir a formato SQL YYYY-MM-DD
                try:
                    fecha_obj = datetime.strptime(match.group(1), '%d/%m/%Y')
                    metadata["fecha_promulgacion"] = fecha_obj.strftime('%Y-%m-%d')
                except ValueError:
                    pass

        return metadata

    def scrape_norm(self, url: str) -> dict:
        """Scrapea una norma legal completa a partir de su URL específica."""
        print(f"Scrapeando {url}...")
        html = self.fetch_html(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        
        # Eliminar scripts y estilos
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()

        # Extraer metadatos
        metadata = self.extract_metadata(soup)
        
        # Extraer texto principal (usualmente en un contenedor principal)
        main_content = soup.find('div', id=re.compile('Cuerpo|main', re.I))
        if not main_content:
            main_content = soup.body

        texto_completo = self.clean_text(main_content.get_text(separator='\n'))
        
        # Generar hash
        content_hash = self.generate_hash(texto_completo)

        # Parsear artículos
        articulos = self.parse_articles(texto_completo)

        return {
            "metadata": metadata,
            "texto_completo": texto_completo,
            "hash": content_hash,
            "articulos": articulos,
            "url": url
        }

    def scrape_latest(self):
        """Scrapea el índice de novedades (ej: Diario Oficial)."""
        # Endpoint de ejemplo, la URL real depende del sitio actual.
        novedades_url = f"{self.base_url}/novedades"
        html = self.fetch_html(novedades_url)
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/bases/' in href or 'normativa' in href:
                full_link = href if href.startswith('http') else f"{self.base_url}{href}"
                links.append(full_link)
                
        # Scrapear las primeras 3 normas como prueba
        results = []
        for link in set(links[:3]): 
            norm_data = self.scrape_norm(link)
            if norm_data:
                results.append(norm_data)
                
        return results

if __name__ == "__main__":
    # Test sencillo
    scraper = ImpoScraper()
    # URL de prueba (Ley de Urgente Consideración o similar)
    url_test = "https://www.impo.com.uy/bases/leyes/19889-2020" 
    resultado = scraper.scrape_norm(url_test)
    if resultado:
        print(f"Éxito extrayendo norma: {resultado['metadata']}")
        print(f"Total artículos parseados: {len(resultado['articulos'])}")
