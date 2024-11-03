import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from openpyxl import Workbook
import pandas as pd
from env import URL, DriverLocation

# Cette fonction récupère le texte principal, le score, le nom de chaque élément avis sur google maps.
# Prend comme paramètres 'driver' et 'data_structure_type' qui représente respectivement le navigateur web controlé et
# une valeur représentant la structure de donné présente sur la page. 
# Renvoie une liste avec chaque éléments composé de ses détails.
def get_data(driver, data_structure_type):    
    print('Collecte des données...')
    more_elements = driver.find_elements("class name", 'w8nwRe kyuRq')  # selection bouton plus pour afficher tout le commentaire
    for element in more_elements:
        element.click()                                                 # clique sur l'element pour dérouler l'avis complet                                    
    
    # Chemin basé sur le type de structure de données de la page
    base_xpath = "//body/div[2]/div[3]/div[8]/div[9]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]"
    elements_xpath = f"{base_xpath}/div[{9 if data_structure_type == 1 else 8}]"

    # Trouver element unique sur la page
    elements = driver.find_element("xpath", elements_xpath)
    # Trouver première div enfant de l'élément trouvé 
    child_element = elements.find_element("xpath", './/div[1]')
    # Récupérer le nom de la class de la div enfant 
    class_name = child_element.get_attribute('class')
    # Récupérer tout les éléments appartenant a la même class
    elements = elements.find_elements("xpath", f'//*[@class="{class_name}"]')

    # Récupérer les class de 'name', 'text' et 'score' de la div enfant
    name_class = child_element.find_element("xpath", './/div[1]/div[1]/div[2]/div[2]/div[1]/button[1]/div[1]').get_attribute('class')
    text_class = child_element.find_element("xpath", './/div[1]/div[4]/div[2]/div[1]/span[1]').get_attribute('class')
    score_class = child_element.find_element("xpath", './/div[1]/div[1]/div[4]/div[1]/span[1]').get_attribute('class')

    # Stockage des datas extraites sous forme de sous liste
    # Initialisation des datas sur des valeurs par défault
    lst_data = []
    for data in elements:
        name = 'Non spécifié'
        text = 'Non spécifié'
        score = '-'
        try:
            name = data.find_element("xpath", f'.//*[@class="{name_class}"]').text
            score = data.find_element("xpath", f'.//*[@class="{score_class}"]').get_attribute("aria-label")
            text = data.find_element("xpath", f'.//*[@class="{text_class}"]').text
        except Exception:
            pass
        
        # Ajouter les éléments extrait dans la liste 'lst_data'
        lst_data.append([f"{name} depuis Google Maps", text, score[0]])
    return lst_data

# Sert a bypass la notification de concentement google
def check_gdrp_notice(driver):
    # Si l'url actuelle du navigateur contient 'consent.google.com', execute le script pour submit le formulaire
    if 'consent.google.com' in driver.current_url:
        driver.execute_script('document.getElementsByTagName("form")[0].submit()')

# Vérifie si la page web est complètement chargée dans le navigateur
# Retourne True si chargée, False si non
def page_fully_loaded(driver):
    return driver.execute_script('return document.readyState') == 'complete'

# Permet de récupérer la valeur des note d'avis d'un etablissement a partir de la page web
def get_review_count(driver):
    data_structure_type = 1
    try:
        result = driver.find_element("xpath", '//body/div[2]/div[3]/div[8]/div[9]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]').find_element("class name", 'fontBodySmall').text
    except Exception:
        data_structure_type = 2
        result = driver.find_element("xpath", '//body/div[2]/div[3]/div[8]/div[9]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]').find_element("class name", 'fontBodySmall').text

    result = result.replace(',', '').replace('.', '').split()[0]
    return int(int(result) / 10) + 1, data_structure_type

# Sert a faire défiler la page web 
def scroll_page(driver, count):
    print('Défilement de la page...')
    scrollable_div = driver.find_element("xpath", '//body/div/div[3]/div[8]/div[9]/div/div/div/div[3]/div/div/div/div/div[3]/div[last()]')
    for _ in range(count):
        driver.execute_script(
            "var element = document.evaluate('//body/div[2]/div[3]/div[8]/div[9]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; element.scrollTop = element.scrollHeight;",
            scrollable_div
        )
        time.sleep(3)

# Sert a remplir les data dans un fichier Excel au format .xlsx
# Remplis le fichier out.xlsx
def write_to_xlsx(data):
    print('Écriture des données dans Excel...')
    cols = ["Nom", "Commentaire", "Note"]
    df = pd.DataFrame(data, columns=cols)
    df.to_excel('out.xlsx', index=False)

if __name__ == "__main__":
    print('Démarrage...')
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--lang=en-US")
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    DriverPath = DriverLocation
    driver = webdriver.Chrome(DriverPath, options=options)

    driver.get(URL)
    while not page_fully_loaded(driver):
        time.sleep(1)

    check_gdrp_notice(driver)

    while not page_fully_loaded(driver):
        time.sleep(1)

    count, data_structure_type = get_review_count(driver)
    scroll_page(driver, count)

    data = get_data(driver, data_structure_type)
    driver.quit()

    write_to_xlsx(data)
    print('Terminé!')