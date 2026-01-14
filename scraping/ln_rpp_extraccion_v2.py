import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import csv
import re

# ================= CONFIGURACIÓN =================
INPUT_JSON = "rpp_noticias_hoy.json"
TZ = pytz.timezone("America/Lima")

now = datetime.now(TZ)
timestamp = now.strftime("%Y%m%d_%H%M")  # YA DEFINIDO (NO SE TOCA)

OUTPUT_JSON = f"rpp_detalle.json"
OUTPUT_CSV  = f"rpp_detalle.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-PE,es;q=0.9"
}

# ================= CARGAR LINKS ==================
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    noticias = json.load(f)

resultado = []

# ================= CONTADOR SECUENCIAL ID =================
counter = 1

# ================= PROCESAR ======================
for n in noticias:
    url = n["link"]
    print(f"Procesando: {url}")

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            print("HTTP error")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # ---------- TÍTULO ----------
        h1 = soup.find("h1")
        if not h1:
            print("Sin título")
            continue
        titulo = h1.get_text(strip=True)

        # ---------- CONTENIDO DESDE JSON-LD ----------
        article_body = None

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "NewsArticle":
                    article_body = data.get("articleBody")
                    break
            except:
                continue

        if not article_body:
            print("Sin cuerpo textual")
            continue

        article_body = article_body.strip()

        # ---------- NORMALIZAR A PÁRRAFOS ----------
        oraciones = re.split(r'(?<=[.!?])\s+', article_body)

        parrafos = []
        bloque = ""
        for o in oraciones:
            bloque += o + " "
            if len(bloque) >= 300:
                parrafos.append(bloque.strip())
                bloque = ""

        if bloque.strip():
            parrafos.append(bloque.strip())

        if len(parrafos) == 1 and len(parrafos[0]) < 300:
            print("Contenido insuficiente")
            continue

        # ---------- FECHA ----------
        fecha_publicacion = ""
        time_tag = soup.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            fecha_publicacion = time_tag["datetime"]

        # ---------- IMÁGENES ----------
        imagenes = []

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            imagenes.append({
                "url": og["content"],
                "caption": "",
                "credit": "RPP"
            })

        for link in soup.find_all("link", {"as": "image"}):
            if len(imagenes) >= 15:
                break
            href = link.get("href")
            if href and href not in [i["url"] for i in imagenes]:
                imagenes.append({
                    "url": href,
                    "caption": "",
                    "credit": "RPP"
                })

        # ---------- ID SECUENCIAL ----------
        record_id = int(f"{timestamp.replace('_','')}{counter:07d}")
        counter += 1

        # ---------- REGISTRO ----------
        resultado.append({
            "id": record_id,
            "diario": "RPP",
            "fecha_extraccion": now.isoformat(),
            "fecha_publicacion": fecha_publicacion,
            "titulo": titulo,
            "contenido": parrafos,
            "url": url,
            "imagenes": imagenes
        })

        print("OK")

    except Exception as e:
        print(f"Error: {e}")
        continue

# ================= GUARDAR =======================
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "id",
            "diario",
            "fecha_extraccion",
            "fecha_publicacion",
            "titulo",
            "url",
            "contenido",
            "imagenes"
        ]
    )
    writer.writeheader()

    for r in resultado:
        writer.writerow({
            "id": r["id"],
            "diario": r["diario"],
            "fecha_extraccion": r["fecha_extraccion"],
            "fecha_publicacion": r["fecha_publicacion"],
            "titulo": r["titulo"],
            "url": r["url"],
            "contenido": " || ".join(r["contenido"]),
            "imagenes": json.dumps(r["imagenes"], ensure_ascii=False)
        })

print("===================================")
print(f"JSON: {OUTPUT_JSON}")
print(f"CSV : {OUTPUT_CSV}")
print(f"Noticias válidas: {len(resultado)}")
