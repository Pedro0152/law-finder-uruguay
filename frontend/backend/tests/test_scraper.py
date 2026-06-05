import unittest
from scraper.base_scraper import BaseScraper
from scraper.impo_scraper import ImpoScraper
from bs4 import BeautifulSoup

class TestScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = BaseScraper("Test", "http://test.com")
        self.impo = ImpoScraper()

    def test_clean_text(self):
        dirty_text = "  Texto con \n\n  muchos   espacios  "
        clean = self.scraper.clean_text(dirty_text)
        self.assertEqual(clean, "Texto con muchos espacios")

    def test_parse_articles(self):
        full_text = "Considerando bla bla. Artículo 1. El estado es laico. Artículo 2. El estado garantiza la libertad."
        articles = self.scraper.parse_articles(full_text)
        
        self.assertEqual(len(articles), 3) # Preámbulo + 2 artículos
        self.assertEqual(articles[0]['numero'], "Preámbulo")
        self.assertEqual(articles[1]['numero'].strip(), "Artículo 1.")
        self.assertEqual(articles[1]['texto'].strip(), "El estado es laico.")

    def test_metadata_extraction(self):
        html = '''
        <html>
            <h1 class="titulo">LEY N° 19.889</h1>
            <span class="fecha">Promulgación: 09/07/2020</span>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        metadata = self.impo.extract_metadata(soup)
        
        self.assertEqual(metadata['tipo'], "Ley")
        self.assertEqual(metadata['numero'], "19889")
        self.assertEqual(metadata['fecha_promulgacion'], "2020-07-09")

if __name__ == '__main__':
    unittest.main()
