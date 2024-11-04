import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openpyxl import Workbook
import pandas as pd
from env import URL, DriverLocation

def page_fully_loaded(driver):
    print("Acces a la page en cours...")
    return driver.execute_script('return document.readyState') == 'complete'

def validate_gdrp_google(driver):
    if 'consent.google.com' in driver.current_url:
        driver.execute_script('document.getElementsByTagName("form")[0].submit()')

def get_review_count(driver):
    data_structure_type = 1
    try:
        result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//body/div/div[3]/div[8]/div[9]/div/div/div/div[3]/div/div/div/div/div[3]/div/div/div[2]/div[3]'))
        ).text
    except Exception:
        data_structure_type = 2
        result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//body/div/div[3]/div[8]/div[9]/div/div/div/div[2]/div/div/div/div/div[2]/div/div/div[2]/div[3]'))
        ).text
        
    result = result.replace(',', '').replace('.', '').split()[0]
    return int(int(result) / 10) + 1, data_structure_type

def scroll_page(driver, count):
    print('Défilement de la page en cours...')
    scrollable_div = driver.find_element("xpath", '//body/div/div[3]/div[8]/div[9]/div/div/div/div[3]/div/div/div/div/div[3]/div[last()]')
    for _ in range(count):
        driver.execute_script(
            "var element = document.evaluate('//body/div/div[3]/div[8]/div[9]/div/div/div/div[3]/div/div/div/div/div[3]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; element.scrollTop = element.scrollHeight;",
            scrollable_div
        )
        time.sleep(3)

def get_data(driver, data_structure_type):    
    print('Collecte des données avis clients...')
    extend_reviews = driver.find_elements("xpath", "//*[contains(@class, 'w8nwRe') and contains(@class, 'kyuRq')]")

    # Développe chaque avis en appuyant sur le bouton 'plus'
    for element in extend_reviews:
        driver.execute_script("arguments[0].scrollIntoView();", element)
        try:
            element.click()
            print("Clicked successfully!")
        except Exception:
            print("Click intercepted, retrying...")                                                                                

    base_xpath = "//body/div/div[3]/div[8]/div[9]/div/div/div/div[3]/div/div/div/div/div[3]"

    global_place_reviews_xpath = f"{base_xpath}/div"
    global_elements_reviews_xpath = f"{base_xpath}/div[{10 if data_structure_type == 1 else 8}]"

    # Récupérer la bannière d'avis global de l'endroit sur la page
    global_place_review = driver.find_element("xpath", global_place_reviews_xpath)

    # Récupérer les éléments de reviews sur la page
    elements = driver.find_element("xpath", global_elements_reviews_xpath)
    singular_review_element = elements.find_element("xpath", './div[1]')
    singular_review_class_name = singular_review_element.get_attribute('class')

    # Récupérer tous les éléments d'avis de la page
    elements = elements.find_elements("xpath", f'//*[@class="{singular_review_class_name}"]')

    # Récupérer les classes des détails du client de chaque avis
    name_client_class = singular_review_element.find_element("xpath", './div/div/div[2]/div[2]/div/button/div').get_attribute('class')
    details_about_client_class = singular_review_element.find_element("xpath", './div/div/div[2]/div[2]/div/button/div[2]').get_attribute('class')
    text_client_review = singular_review_element.find_element("xpath", './div/div/div[4]/div[2]/div/span').get_attribute('class')

    lst_data = []

    for data in elements:
        # Initialiser les valeurs par défaut
        name = 'Non spécifié'
        details_client = 'Non spécifié'
        text = 'Non spécifié'
        review_details = []

        try:
            # Extraction des informations principales pour chaque client
            name = data.find_element("xpath", f'.//*[@class="{name_client_class}"]').text
            details_client = data.find_element("xpath", f'.//*[@class="{details_about_client_class}"]').text
            text = data.find_element("xpath", f'.//*[@class="{text_client_review}"][not(@lang="fr")]').text

            # Localiser le bloc principal contenant les éléments div à extraire
            try:
                precision_about_review_block = data.find_element("xpath", './div/div/div[4]/div[2]/div/div')
                precision_about_review_block_class = precision_about_review_block.get_attribute('jslog')
                all_reviews_precision = driver.find_elements("xpath", f'//div[@jslog="{precision_about_review_block_class}"]')

                for singular_review_element in all_reviews_precision:
                    print("Conteneur d'avis parcouru!")
                    sub_div_elements = singular_review_element.find_elements("xpath", './div')

                    # Traiter chaque sous-élément div
                    for sub_div in sub_div_elements:
                        try:
                            paired_divs = sub_div.find_elements("xpath", './div')
                            # Vérification pour les paires de divs (Cas 1)
                            if len(paired_divs) >= 2:
                                for i in range(0, len(paired_divs), 2):
                                    if i + 1 < len(paired_divs):
                                        title = paired_divs[i].text.strip()
                                        info = paired_divs[i + 1].text.strip()
                                        review_details.append({title: info}) 
                                        print(f"Case 1 - Title: {title}, Info: {info}")
                            else:
                                # Vérification pour les éléments uniques (Cas 2)
                                title = sub_div.find_element("xpath", './div/span/span/b').text.strip()
                                info = sub_div.find_element("xpath", './div/span/span').text.strip()
                                info = info.replace(title, '').strip()
                                review_details.append({title: info})
                                print(f"Case 2 - Title: {title}, Info: {info}")

                        except Exception as e:
                            print(f"Erreur à la deuxième couche: {e}")

            except Exception as e:
                print(f"Erreur lors de l'extraction du bloc de précision d'avis : {e}")

            # Ajouter le dictionnaire pour chaque avis avec ses détails isolés dans 'lst_data'
            lst_data.append({
                "name": f"{name} depuis Google Maps",
                "details_client": details_client,
                "text": text,
                "review_details": review_details
            })

        except Exception as e:
            print(f"Erreur à la première couche: {e}")

    # Affichage final des données de manière lisible
    for i, review_data in enumerate(lst_data, start=1):
        print(f"\nAvis {i}:")
        print(f"  Nom du client          : {review_data['name']}")
        print(f"  Détails du client      : {review_data['details_client']}")
        print(f"  Texte de l'avis        : {review_data['text']}")
        print(f"  Détails supplémentaires:")
        
        if review_data["review_details"]:
            for detail in review_data["review_details"]:
                for title, info in detail.items():
                    print(f"    - {title} : {info}")
        else:
            print("    Aucun détail supplémentaire")
        
        print("\n" + "-" * 40)  # Séparateur pour chaque avis

    print("Tout s'est bien passé!")
    return lst_data

if __name__ == "__main__":
    url = "https://www.google.com/"
    url2 = "https://www.google.com/maps/place/Paul/@50.8333281,4.0519869,11z/data=!4m12!1m2!2m1!1spaul!3m8!1s0x47c3c4845ec5b809:0xa8aca620c7277d7d!8m2!3d50.8406084!4d4.3665856!9m1!1b1!15sCgRwYXVsIgOIAQFaBiIEcGF1bJIBBmJha2VyeeABAA!16s%2Fg%2F11c2y73ydz?entry=ttu&g_ep=EgoyMDI0MTAyMy4wIKXMDSoASAFQAw%3D%3D"

    print("demarrage scrapping...")
    options = Options()
    # Execute le navigateur de manière discrete (non graphique)
    options.add_argument("--headless")
    options.add_argument("--lang=fr-FR")
    options.add_experimental_option('prefs', {'intl.accept_languages': 'fr,fr_FR'})
    DriverPath = DriverLocation
    driver = webdriver.Chrome(DriverPath, options=options)

    driver.get(url2)
    while not page_fully_loaded(driver):
        print("Chargement de la page...")
        time.sleep(1)

    validate_gdrp_google(driver)

    while not page_fully_loaded(driver):
        print("Validation des gdrp de google en cours...")
        time.sleep(3)

    count, data_structure_type = get_review_count(driver)
    scroll_page(driver, count)
    
    data = get_data(driver, data_structure_type)
    driver.quit()

    print(data)
    

