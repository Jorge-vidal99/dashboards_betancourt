import os
import requests
from auth_onedrive import get_token


GRAPH_ROOT_CHILDREN = "https://graph.microsoft.com/v1.0/me/drive/root/children"


def graph_get(url: str, headers: dict) -> dict:
    """GET a Graph con validación y mensajes claros."""
    r = requests.get(url, headers=headers, timeout=60)

    # Intentar parsear JSON siempre
    try:
        payload = r.json()
    except Exception:
        payload = {"_raw_text": r.text}

    if r.status_code != 200:
        print(" Error llamando a Microsoft Graph")
        print("URL:", url)
        print("Status:", r.status_code)
        print("Respuesta:", payload)
        raise SystemExit(1)

    return payload


def get_all_children(folder_children_url: str, headers: dict) -> list[dict]:
    """Obtiene todos los hijos de una carpeta manejando paginación."""
    items = []
    url = folder_children_url

    while url:
        payload = graph_get(url, headers)
        batch = payload.get("value", [])
        items.extend(batch)
        url = payload.get("@odata.nextLink")  # si hay más páginas

    return items


def main():
    print("1) Obteniendo token...")
    token = get_token()

    headers = {"Authorization": f"Bearer {token}"}

    print("2) Buscando carpeta FACTURAS_2026 en el root...")
    root_payload = graph_get(GRAPH_ROOT_CHILDREN, headers)

    root_items = root_payload.get("value", [])
    folder_id = None

    for item in root_items:
        # Solo carpetas tienen "folder"
        if item.get("name") == "FACTURAS_2026" and "folder" in item:
            folder_id = item["id"]
            break

    if not folder_id:
        print(" No se encontró la carpeta FACTURAS_2026 en el root.")
        print("Carpetas/archivos vistos en root:")
        for it in root_items:
            print("-", it.get("name"))
        raise SystemExit(1)

    print(" Carpeta encontrada. ID:", folder_id)

    # URL hijos de la carpeta
    children_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children"

    print("3) Listando archivos dentro de FACTURAS_2026 (con paginación si aplica)...")
    files = get_all_children(children_url, headers)

    print(f"Items encontrados en carpeta: {len(files)}")

    # Ruta local
    base_path = os.path.dirname(os.path.dirname(__file__))  # ...\REPORTE
    download_path = os.path.join(base_path, "data_raw")
    os.makedirs(download_path, exist_ok=True)

    print("4) Descargando .xlsx ...")
    descargados = 0

    for f in files:
        name = f.get("name", "")

        # solo archivos excel
        if not name.lower().endswith(".xlsx"):
            continue

        # @microsoft.graph.downloadUrl puede no venir si no es archivo
        download_url = f.get("@microsoft.graph.downloadUrl")
        if not download_url:
            continue

        file_path = os.path.join(download_path, name)
        print(f" - Descargando {name}...")

        rr = requests.get(download_url, timeout=120)
        if rr.status_code != 200:
            print(f"    No se pudo descargar {name}. Status={rr.status_code}")
            continue

        with open(file_path, "wb") as out:
            out.write(rr.content)

        descargados += 1

    print(f" Descarga completada. Archivos .xlsx descargados: {descargados}")
    print("Carpeta local:", download_path)


if __name__ == "__main__":
    main()