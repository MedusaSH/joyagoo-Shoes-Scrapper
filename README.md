# 🥿 Joyagoo Shoes Scraper

Un scraper Python automatisé pour extraire toutes les paires de **chaussures** listées sur le site [JoyagooSheets](https://www.joyagoosheets.com/item-type/shoes).  
Il collecte les noms, les URLs et télécharge toutes les **images** associées aux produits dans un dossier local nommé `SHOES`.

---

## ✨ Fonctionnalités

- Navigation dynamique via Selenium pour charger tout le contenu JS.
- Extraction des liens produits `/products/...` depuis la catégorie `Shoes`.
- Téléchargement des images dans un format structuré.
- Filtrage intelligent (évite les logos, favicons, SVG, etc).
- Nommage propre des fichiers et gestion des doublons.
- Exécution totalement autonome (`python scraper.py`).

---

## 🛠️ Installation

### 1. Cloner le repo

```bash
git clone https://github.com/ton-utilisateur/joyagoo-shoes-scraper.git
cd joyagoo-shoes-scraper
