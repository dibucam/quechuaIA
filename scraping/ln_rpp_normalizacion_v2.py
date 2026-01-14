import json
import re
from datetime import datetime
import pytz
import csv
import os

#  CONFIGURACIÓN 
INPUT_JSON = "rpp_detalle.json"

TZ = pytz.timezone("America/Lima")
now = datetime.now(TZ)
timestamp = now.strftime("%Y%m%d_%H%M")

OUTPUT_JSON = "rpp_normalizado.json"
OUTPUT_CSV  = "rpp_normalizado.csv"

# FUNCIONES 

EDITORIAL_SYMBOLS_ANYWHERE = r'[►▶●•]'

EDITORIAL_PATTERNS = [
    r'\[\s*VIDEO\s*\]',
    r'\(\s*VIDEO\s*\)',
    r'\bVIDEO\s*:\b',
    r'\bVER\s+VIDEO\b',
    r'\bMIRA\s+EL\s+VIDEO\b',
    r'\bEN\s+VIVO\b',
    r'\bTRANSMISI[ÓO]N\b',
    r'\bPODCAST\b',
    r'\bESCUCHA\b',
    r'\bAQU[IÍ]\s+EL\s+VIDEO\b',
    r'\bM[ÁA]S\s+INFORMACI[ÓO]N\b',
    r'\bLEE\s+TAMBI[ÉE]N\b\s*:?'
]

def limpieza_basica(texto: str) -> str:
    if not texto:
        return ""

    texto = re.sub(r'https?://\S+', '', texto)
    texto = texto.replace("\u00a0", " ")
    texto = re.sub(EDITORIAL_SYMBOLS_ANYWHERE, '', texto)

    for pat in EDITORIAL_PATTERNS:
        texto = re.sub(pat, '', texto, flags=re.IGNORECASE)

    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\s+([,.;:!?])', r'\1', texto)

    return texto.strip()


def normalizacion_ortografica_minima(texto: str) -> str:
    if not texto:
        return ""

    reemplazos = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "—": "-",
        "–": "-",
        "…": "...",
        "´": "'"
    }

    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    if texto.isupper() and len(texto) > 8:
        texto = texto.capitalize()

    return texto.strip()


def normalizar_contenido_lista_a_texto(contenido):
    if isinstance(contenido, list):
        partes = []
        for x in contenido:
            s = normalizacion_ortografica_minima(limpieza_basica(str(x)))
            if s:
                partes.append(s)
        return " ".join(partes).strip()
    else:
        return normalizacion_ortografica_minima(limpieza_basica(str(contenido)))

#  VALIDACIÓN 
if not os.path.exists(INPUT_JSON):
    raise FileNotFoundError(f"No existe el archivo: {INPUT_JSON}")

#  CARGAR JSON 
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

resultado = []

# PROCESAR 
for item in data:
    nuevo = dict(item)  # 👈 el ID ya viene aquí

    titulo_norm = normalizacion_ortografica_minima(
        limpieza_basica(item.get("titulo", ""))
    )

    contenido_norm = normalizar_contenido_lista_a_texto(
        item.get("contenido", [])
    )

    contenido_norm = normalizacion_ortografica_minima(
        limpieza_basica(contenido_norm)
    )

    nuevo["titulo_normalizado"] = titulo_norm
    nuevo["contenido_normalizado"] = contenido_norm

    resultado.append(nuevo)

# GUARDAR JSON 
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

# GUARDAR CSV 
csv_fieldnames = [
    "id",                      # ✅ ID incluido
    "diario",
    "fecha_extraccion",
    "fecha_publicacion",
    "url",
    "titulo_normalizado",
    "contenido_normalizado",
]

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=csv_fieldnames, delimiter=";")
    writer.writeheader()

    for r in resultado:
        writer.writerow({
            "id": r.get("id", ""),  # ✅ ID preservado
            "diario": r.get("diario", ""),
            "fecha_extraccion": r.get("fecha_extraccion", ""),
            "fecha_publicacion": r.get("fecha_publicacion", ""),
            "url": r.get("url", ""),
            "titulo_normalizado": r.get("titulo_normalizado", ""),
            "contenido_normalizado": r.get("contenido_normalizado", ""),
        })

print("===================================")
print("Normalización completada")
print(f"JSON: {OUTPUT_JSON}")
print(f"CSV : {OUTPUT_CSV}")
print(f"Registros procesados: {len(resultado)}")
