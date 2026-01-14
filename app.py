from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import json
from pathlib import Path

app = FastAPI(title="Willaykuna - Quechua News")
templates = Jinja2Templates(directory="templates")

# -------------------------
# CONFIG (Windows)
# -------------------------
TEXT_DIR = Path(r"C:\Compartido\quechua_texto")
AUDIO_DIR = Path(r"C:\Compartido\quechua_audio")

# Si tu archivo tiene otro nombre, cámbialo aquí
JSON_FILE = TEXT_DIR / "noticias.json"   # <-- por ejemplo: noticias.json

# Static del proyecto (CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")


def normalize_item(raw: dict) -> dict:
    """
    Normaliza diferentes estructuras a:
    { id, titulo, texto, imagen_url, audio_filename }
    """
    news_id = str(raw.get("id", "")).strip()
    if not news_id:
        raise ValueError("Item sin 'id'")

    titulo = (raw.get("titulo") or "").strip()

    # Caso 1: estructura simple: "texto" string
    if isinstance(raw.get("texto"), str):
        texto = raw["texto"].strip()
    else:
        # Caso 2 (tu ejemplo real): "contenido" lista de párrafos
        contenido = raw.get("contenido", "")
        if isinstance(contenido, list):
            texto = "\n\n".join([str(x).strip() for x in contenido if str(x).strip()])
        else:
            texto = str(contenido).strip()

    # Imagen:
    # - estructura simple: "imagen" (url)
    # - o tu ejemplo real: "imagenes":[{"url": "..."}]
    imagen_url = ""
    if isinstance(raw.get("imagen"), str):
        imagen_url = raw["imagen"].strip()
    else:
        imagenes = raw.get("imagenes", [])
        if isinstance(imagenes, list) and len(imagenes) > 0:
            first = imagenes[0] or {}
            if isinstance(first, dict):
                imagen_url = str(first.get("url", "")).strip()

    audio_filename = f"{news_id}.wav"

    return {
        "id": news_id,
        "titulo": titulo,
        "texto": texto,
        "imagen_url": imagen_url,
        "audio_filename": audio_filename,
    }


def load_news() -> list[dict]:
    if not JSON_FILE.exists():
        return []

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = data.get("items", [])

    if not isinstance(data, list):
        return []

    out = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        try:
            out.append(normalize_item(raw))
        except Exception:
            continue

    # 🔹 ORDEN ASCENDENTE POR ID
    out.sort(key=lambda x: int(x["id"]))

    return out

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    news = load_news()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "news": news, "title": "Willaykuna"}
    )


@app.get("/noticia/{news_id}", response_class=HTMLResponse)
def detail(request: Request, news_id: str):
    news = load_news()
    item = next((n for n in news if n["id"] == str(news_id)), None)
    if not item:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")

    return templates.TemplateResponse(
        "noticia.html",
        {"request": request, "item": item, "title": item.get("titulo", "Noticia")}
    )


@app.get("/audio/{filename}")
def serve_audio(filename: str):
    # Solo permitir .wav
    if not filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Formato de audio no permitido")

    path = AUDIO_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio no encontrado")

    return FileResponse(path, media_type="audio/wav", filename=filename)
