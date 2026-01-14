from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import csv

URL = "https://rpp.pe/ultimas-noticias"

# Configuración del navegador
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

print("➡️ Abriendo RPP...")
driver.get(URL)
time.sleep(3)

news_data = []
click_count = 0

# Loop para cargar todas las noticias del día
while True:
    articles = driver.find_elements(By.CSS_SELECTOR, "article")
    print(f"📄 Artículos detectados: {len(articles)}")

    for art in articles:
        try:
            title = art.find_element(By.CSS_SELECTOR, "h2, h3").text.strip()
            link = art.find_element(By.TAG_NAME, "a").get_attribute("href")

            try:
                date_attr = art.find_element(By.TAG_NAME, "time").get_attribute("datetime")
            except:
                date_attr = ""

            news_data.append({
                "titulo": title,
                "link": link,
                "fecha_publicacion": date_attr
            })
        except:
            continue

    try:
        ver_mas = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Ver más')]"))
        )
        driver.execute_script("arguments[0].click();", ver_mas)
        click_count += 1
        print(f"Click en 'Ver más' #{click_count}")
        time.sleep(3)
    except:
        print("No hay más noticias del día")
        break

driver.quit()

# Eliminar duplicados por link
unique_news = list({n["link"]: n for n in news_data}.values())
print(f"Total noticias del día: {len(unique_news)}")

# Guardar JSON
with open("rpp_noticias_hoy.json", "w", encoding="utf-8") as f:
    json.dump(unique_news, f, ensure_ascii=False, indent=2)

# Guardar CSV compatible con Excel (UTF-8 con BOM)
with open("rpp_noticias_hoy.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["titulo", "link", "fecha_publicacion"]
    )
    writer.writeheader()
    writer.writerows(unique_news)

print("Archivos generados correctamente:")
print("- rpp_noticias_hoy.json")
print("- rpp_noticias_hoy.csv")
