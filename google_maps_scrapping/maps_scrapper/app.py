import time
import csv
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
    
    print(result)
    #result = result.replace(',', '').replace('.', '').split()[0]
    result = ''.join(filter(str.isdigit, result))  # garde uniquement les chiffres dans 'result'
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

def display_reviews(lst_data):
    # Affichage final des données de manière lisible
    for i, review_data in enumerate(lst_data, start=1):
        print(f"\nAvis {i}:")
        print(f"  Nom du client          : {review_data['name']}")
        print(f"  Détails du client      : {review_data['details_client']}")
        print(f"  Date de l'avis         : {review_data['review_date']}")
        print(f"  Étoile sur l'avis      : {review_data['star_rating']}")
        print(f"  Texte de l'avis        : {review_data['text']}")
        print(f"  Détails supplémentaires :")

        # Afficher chaque sous-catégorie avec une valeur par défaut si elle est absente
        print(f"    - Type de service    : {review_data.get('service_type', 'Non spécifié')}")
        print(f"    - Type de repas      : {review_data.get('meal_type', 'Non spécifié')}")
        print(f"    - Prix par personne  : {review_data.get('price_per_person', 'Non spécifié')}")
        print(f"    - Note de la cuisine : {review_data.get('cuisine_rating', 'Non spécifié')}")
        print(f"    - Note du service    : {review_data.get('service_rating', 'Non spécifié')}")
        print(f"    - Note de l'ambiance : {review_data.get('ambiance_rating', 'Non spécifié')}")
        print(f"    - Plats recommandés  : {review_data.get('recommended_dishes', 'Non spécifié')}")
        
        print("\n" + "-" * 40)

def parse_details_review(details_review):
    # Initialise chaque sous-catégorie avec None par défaut
    parsed_details = {
        "service_type": None,
        "meal_type": None,
        "price_per_person": None,
        "cuisine_rating": None,
        "service_rating": None,
        "ambiance_rating": None,
        "recommended_dishes": None,
    }
    
    # Remplissage des sous-catégories si elles sont présentes dans le texte
    for detail in details_review:
        for title, info in detail.items():
            if title == "Service":
                # Si info est une note de service
                if info.startswith(":") and info[2:].strip().isdigit():
                    note = int(info[2:].strip())
                    if 1 <= note <= 5:
                        parsed_details["service_rating"] = note
                else:
                    parsed_details["service_type"] = info
            elif "Type de repas" in title:
                parsed_details["meal_type"] = info
            elif "Prix par personne" in title:
                parsed_details["price_per_person"] = info
            elif "Cuisine" in title:
                # Si info est une note de cuisine
                if info.startswith(":") and info[2:].strip().isdigit():
                    note = int(info[2:].strip())
                    if 1 <= note <= 5:
                        parsed_details["cuisine_rating"] = note
                else:
                    parsed_details["cuisine_rating"] = info
            elif "Ambiance" in title:
                # Si info est une note d'ambiance
                if info.startswith(":") and info[2:].strip().isdigit():
                    note = int(info[2:].strip())
                    if 1 <= note <= 5:
                        parsed_details["ambiance_rating"] = note
                else:
                    parsed_details["ambiance_rating"] = info
            elif "Plats recommandés" in title:
                parsed_details["recommended_dishes"] = info
    
    # Ajout d'une vérification pour éviter les valeurs comme ": 3..."
    for key in ["service_rating", "cuisine_rating", "ambiance_rating"]:
        if isinstance(parsed_details[key], str) and ':' in parsed_details[key]:
            parsed_details[key] = None  # Remplace les valeurs mal formatées par None

    return parsed_details

def get_data(driver, data_structure_type):    
    print('Collecte des données avis clients...')
    extend_reviews = driver.find_elements("xpath", "//*[contains(@class, 'w8nwRe') and contains(@class, 'kyuRq')]")

    # Développe chaque avis en appuyant sur le bouton 'plus'
    for element in extend_reviews:
        driver.execute_script("arguments[0].scrollIntoView();", element)
        try:
            element.click()
        except Exception:
            print("Click intercepted, retrying...")                                                                                

    base_xpath = "//body/div/div[3]/div[8]/div[9]/div/div/div/div[3]/div/div/div/div/div[3]"
    poi_name_path = "//body/div/div[3]/div[8]/div[9]/div/div/div/div[3]/div/div/div/div/div/div/div/div[2]/div/div/span"

    global_place_reviews_xpath = f"{base_xpath}/div"
    global_elements_reviews_xpath = f"{base_xpath}/div[{10 if data_structure_type == 1 else 8}]"

    global_place_review = driver.find_element("xpath", global_place_reviews_xpath)
    elements = driver.find_element("xpath", global_elements_reviews_xpath)
    singular_review_element = elements.find_element("xpath", './div[1]')
    singular_review_class_name = singular_review_element.get_attribute('class')
    elements = elements.find_elements("xpath", f'//*[@class="{singular_review_class_name}"]')

    name_client_class = singular_review_element.find_element("xpath", './div/div/div[2]/div[2]/div/button/div').get_attribute('class')
    details_about_client_class = singular_review_element.find_element("xpath", './div/div/div[2]/div[2]/div/button/div[2]').get_attribute('class')
    text_client_review_class = singular_review_element.find_element("xpath", './div/div/div[4]/div[2]/div/span').get_attribute('class')
    date_reviews_client_class = singular_review_element.find_element("xpath", './div/div/div[4]/div/span[2]').get_attribute('class')
    start_client_rating_class = singular_review_element.find_element("xpath", './div/div/div[4]/div/span').get_attribute('class')
    positive_client_star_class = singular_review_element.find_element("xpath", './div/div/div[4]/div/span/span').get_attribute('class')
    
    try:
        precision_about_review_block = singular_review_element.find_element("xpath", './div/div/div[4]/div[2]/div/div')
        precision_about_review_block_jslog = precision_about_review_block.get_attribute('jslog')
    except Exception:
        print("Pas de précision de review trouvés pour cet élément...")

    lst_data = []
    for data in elements:
        # Initialiser les valeurs par défaut
        # REMPLACER PAR NONE POUR LES INIT DE BASE
        name = 'Non spécifié'
        details_client = 'Non spécifié'
        text = 'Non spécifié'
        review_details = []
        review_date = 'Non spécifié'
        client_star_rate = 'Non spécifié'

        try:
            name = data.find_element("xpath", f'.//*[@class="{name_client_class}"]').text
        except Exception:
            pass

        try:
            details_client = data.find_element("xpath", f'.//*[@class="{details_about_client_class}"]').text
        except Exception:
            pass

        try:
            text = data.find_element("xpath", f'.//*[@class="{text_client_review_class}"][not(@lang="fr")]').text
        except Exception:
            pass

        try:
            review_date = data.find_element("xpath", f'.//*[@class="{date_reviews_client_class}"]').text
        except Exception:
            pass

        try:     
            count = 0
            stars_inside_div = data.find_elements("xpath", f'.//*[@class="{start_client_rating_class}"]/span')
            for star in stars_inside_div:
                if star.get_attribute('class') == positive_client_star_class:
                    count += 1
            client_star_rate = count  
        except Exception as e:
            pass

        try:
            if (data.find_element("xpath", f'.//div[@jslog="{precision_about_review_block_jslog}"]')):
                sub_div_elements = data.find_elements("xpath", f'.//div[@jslog="{precision_about_review_block_jslog}"]/div')
                for sub_div in sub_div_elements:
                    try: 
                        paired_divs = sub_div.find_elements("xpath", './div')
                        if len(paired_divs) >= 2:
                            for i in range(0, len(paired_divs), 2):
                                if i + 1 < len(paired_divs):
                                    title = paired_divs[i].text.strip()
                                    info = paired_divs[i + 1].text.strip()
                                    review_details.append({title: info})
                        else:
                            title = sub_div.find_element("xpath", './div/span/span/b').text.strip()
                            info = sub_div.find_element("xpath", './div/span/span').text.strip()
                            info = info.replace(title, '').strip()
                            review_details.append({title: info})
                    except Exception:
                        print("Erreur dans la nouvelle boucle")    
        except Exception:
            pass

        # Parse les détails d'avis et ajoute le résultat structuré à lst_data
        parsed_review_details = parse_details_review(review_details)
        
        lst_data.append({
            "name": f"{name} depuis Google Maps",
            "details_client": details_client,
            "review_date": review_date,
            "star_rating": client_star_rate,
            "text": text,
            "service_type": parsed_review_details["service_type"],
            "meal_type": parsed_review_details["meal_type"],
            "price_per_person": parsed_review_details["price_per_person"],
            "cuisine_rating": parsed_review_details["cuisine_rating"],
            "service_rating": parsed_review_details["service_rating"],
            "ambiance_rating": parsed_review_details["ambiance_rating"],
            "recommended_dishes": parsed_review_details["recommended_dishes"]
        })

    #display_reviews(lst_data)

    print("Tout s'est bien passé!")
    return lst_data

def save_data_to_csv(raw_data, filename="avis_clients.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Définir les en-têtes avec les nouvelles sous-catégories
        headers = [
            "Nom du client",
            "Détails du client",
            "Date",
            "Étoiles",
            "Texte",
            "Type de service",
            "Type de repas",
            "Prix par personne",
            "Note de la cuisine",
            "Note du service",
            "Note de l'ambiance",
            "Plats recommandés"
        ]

        writer.writerow(headers)

        # Écrire chaque avis en incluant les sous-catégories
        for single_review_data in raw_data:
            writer.writerow([
                single_review_data["name"],
                single_review_data["details_client"],
                single_review_data["review_date"],
                single_review_data["star_rating"],
                single_review_data["text"],
                single_review_data.get("service_type", "Non spécifié"),
                single_review_data.get("meal_type", "Non spécifié"),
                single_review_data.get("price_per_person", "Non spécifié"),
                single_review_data.get("cuisine_rating", "Non spécifié"),
                single_review_data.get("service_rating", "Non spécifié"),
                single_review_data.get("ambiance_rating", "Non spécifié"),
                single_review_data.get("recommended_dishes", "Non spécifié")
            ])

    print(f"Les avis ont été enregistrés dans le fichier '{filename}' avec succès.")

if __name__ == "__main__":
    url = "https://www.google.com/"
    url2 = "https://www.google.com/maps/place/Paul/@40.4426809,-3.7174492,12z/data=!3m1!5s0xd422e0f61a610a7:0x292adb6bede30388!4m12!1m2!2m1!1spaul!3m8!1s0xd422e0f7d078031:0x9384d6eb08e0c932!8m2!3d40.4913111!4d-3.5917845!9m1!1b1!15sCgRwYXVsIgOIAQFaBiIEcGF1bJIBBmJha2VyeeABAA!16s%2Fg%2F11b76gddyh?entry=ttu&g_ep=EgoyMDI0MTAyOS4wIKXMDSoASAFQAw%3D%3D"

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

    save_data_to_csv(data)
    
    # print(data)
    

