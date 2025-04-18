import os
import time
import requests
import re
import uuid
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

class ShoesScraper:
    """
    Scraper spécialisé pour extraire les données de chaussures du site joyagoosheets.com
    """
    
    def __init__(self):
        """Initialise le scraper avec les configurations nécessaires"""
        self.base_url = "https://www.joyagoosheets.com"
        self.shoes_url = "https://www.joyagoosheets.com/item-type/shoes"
        self.data_folder = "SHOES"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Configuration de Firefox en mode headless
        self.firefox_options = FirefoxOptions()
        self.firefox_options.add_argument("--headless")
        self.firefox_options.add_argument("--no-sandbox")
        self.firefox_options.add_argument("--disable-dev-shm-usage")
        self.firefox_options.set_preference("general.useragent.override", self.headers['User-Agent'])
        
        # Créer le dossier SHOES s'il n'existe pas
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            print(f"Dossier {self.data_folder} créé.")
    
    def slugify(self, text):
        """Convertit un texte en format slug pour les noms de fichiers"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text
    
    def get_dynamic_content(self, url):
        """Utilise Selenium pour récupérer le contenu chargé dynamiquement"""
        driver = None
        try:
            # Utiliser un chemin fixe pour le driver Firefox
            firefox_options = self.firefox_options
            
            # Essayer d'utiliser le driver Firefox déjà installé sur le système
            try:
                driver = webdriver.Firefox(options=firefox_options)
                print("Driver Firefox initialisé avec succès.")
            except Exception as e:
                print(f"Erreur avec Firefox par défaut: {e}")
                print("Tentative avec le chemin explicite du driver...")
                
                # Si vous avez téléchargé manuellement geckodriver, spécifiez son chemin ici
                gecko_path = "./geckodriver"  # ou utilisez un chemin absolu
                service = FirefoxService(executable_path=gecko_path)
                driver = webdriver.Firefox(service=service, options=firefox_options)
                print("Driver Firefox initialisé avec le chemin explicite.")
                
            driver.get(url)
            print(f"Navigation vers: {url}")
            
            # Attendre que la page soit chargée
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Faire défiler la page pour charger tout le contenu
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Attendre le chargement du contenu
            
            return BeautifulSoup(driver.page_source, 'html.parser')
        except Exception as e:
            print(f"Erreur lors du chargement dynamique de {url}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
                print("Driver Firefox fermé.")
    
    def get_shoe_product_links(self):
        """Récupère tous les liens de produits de chaussures"""
        print(f"Récupération des produits de chaussures depuis: {self.shoes_url}")
        soup = self.get_dynamic_content(self.shoes_url)
        if not soup:
            return []
        
        product_links = []
        # Chercher les liens qui mènent vers des produits
        product_elements = soup.find_all('a', href=re.compile(r'/products/'))
        
        for link in product_elements:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                product_links.append(full_url)
                print(f"Produit de chaussures trouvé: {full_url}")
        
        return list(set(product_links))  # Éliminer les doublons
    
    def extract_shoe_info(self, product_url):
        """Extrait les informations d'une paire de chaussures"""
        print(f"Extraction des informations de la chaussure: {product_url}")
        soup = self.get_dynamic_content(product_url)
        if not soup:
            return None
        
        # Extraire le nom du produit depuis l'URL
        shoe_name = product_url.split('/')[-1].replace('-', ' ').title()
        print(f"Nom de la chaussure extrait de l'URL: {shoe_name}")
        
        # Extraire les liens des images
        image_links = []
        
        # Rechercher toutes les images possibles
        # 1. Images standard
        image_elements = soup.find_all('img')
        for img in image_elements:
            src = img.get('src')
            if src and not src.startswith('data:'):
                # Ignorer les SVG
                if not src.lower().endswith('.svg'):
                    full_img_url = urljoin(self.base_url, src)
                    if full_img_url not in image_links:
                        image_links.append(full_img_url)
        
        # 2. Images dans les attributs de style (background-image)
        style_elements = soup.find_all(lambda tag: tag.has_attr('style') and 'background-image' in tag['style'])
        for element in style_elements:
            style = element['style']
            url_match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
            if url_match:
                img_url = url_match.group(1)
                # Ignorer les SVG
                if not img_url.lower().endswith('.svg'):
                    full_img_url = urljoin(self.base_url, img_url)
                    if full_img_url not in image_links:
                        image_links.append(full_img_url)
        
        # 3. Images dans les attributs data-src (lazy loading)
        data_src_elements = soup.find_all(lambda tag: tag.has_attr('data-src'))
        for element in data_src_elements:
            data_src = element['data-src']
            # Ignorer les SVG
            if not data_src.lower().endswith('.svg'):
                full_img_url = urljoin(self.base_url, data_src)
                if full_img_url not in image_links:
                    image_links.append(full_img_url)
        
        # Filtrer les images qui ne sont pas des chaussures (logos, icônes, etc.)
        filtered_images = []
        for img_url in image_links:
            # Exclure les images très petites, les icônes et les SVG
            if not any(keyword in img_url.lower() for keyword in ['icon', 'logo', 'favicon', '.svg']):
                filtered_images.append(img_url)
        
        print(f"Nombre d'images trouvées pour {shoe_name}: {len(filtered_images)}")
        
        return {
            'name': shoe_name,
            'url': product_url,
            'images': filtered_images
        }
    
    def download_image(self, image_url, save_path):
        """Télécharge une image et la sauvegarde"""
        try:
            response = requests.get(image_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Vérifier que c'est bien une image
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                print(f"Contenu non-image ignoré: {image_url} (type: {content_type})")
                return False
            
            # Ignorer les SVG
            if content_type == 'image/svg+xml' or image_url.lower().endswith('.svg'):
                print(f"Image SVG ignorée: {image_url}")
                return False
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Image téléchargée: {save_path}")
            return True
        except Exception as e:
            print(f"Erreur lors du téléchargement de l'image {image_url}: {e}")
            return False
    
    def save_shoe_data(self, shoe_info):
        """Sauvegarde les données d'une paire de chaussures"""
        if not shoe_info:
            return False
        
        shoe_name = shoe_info['name']
        slug = self.slugify(shoe_name)
        
        # Télécharger chaque image avec un nom unique basé sur le nom de la chaussure
        downloaded_count = 0
        for i, img_url in enumerate(shoe_info['images']):
            # Déterminer l'extension de l'image
            extension = '.jpg'  # Extension par défaut
            url_path = img_url.split('?')[0]  # Enlever les paramètres d'URL
            if '.' in url_path:
                file_extension = os.path.splitext(url_path)[1]
                if file_extension and len(file_extension) <= 5:  # Vérifier que c'est une extension valide
                    extension = file_extension
            
            # Ignorer les SVG
            if extension.lower() == '.svg':
                continue
            
            # Créer un nom de fichier unique pour chaque image
            # Format: nom-de-la-chaussure_index.extension
            img_filename = f"{slug}_{i+1}{extension}"
            img_path = os.path.join(self.data_folder, img_filename)
            
            # S'assurer que le nom de fichier est unique
            if os.path.exists(img_path):
                # Ajouter un identifiant unique si le fichier existe déjà
                unique_id = str(uuid.uuid4())[:8]
                img_filename = f"{slug}_{i+1}_{unique_id}{extension}"
                img_path = os.path.join(self.data_folder, img_filename)
            
            if self.download_image(img_url, img_path):
                downloaded_count += 1
        
        print(f"Images de la chaussure {shoe_name} téléchargées")
        print(f"Nombre d'images téléchargées pour {shoe_name}: {downloaded_count}")
        return True
    
    def run(self):
        """Exécute le processus de scraping pour les chaussures"""
        print("Démarrage du scraping de chaussures sur JoyaGooSheets...")
        
        # Récupérer les liens de produits de chaussures
        shoe_links = self.get_shoe_product_links()
        print(f"Nombre de chaussures trouvées: {len(shoe_links)}")
        
        # Pour chaque paire de chaussures, extraire les informations et les sauvegarder
        successful_shoes = 0
        for shoe_url in shoe_links:
            shoe_info = self.extract_shoe_info(shoe_url)
            if shoe_info and self.save_shoe_data(shoe_info):
                successful_shoes += 1
        
        print(f"\nScraping terminé. {successful_shoes}/{len(shoe_links)} paires de chaussures ont été extraites avec succès.")
        print(f"Toutes les images sont sauvegardées dans le dossier: {self.data_folder}")


if __name__ == "__main__":
    scraper = ShoesScraper()
    scraper.run() 
