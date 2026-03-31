from pathlib import Path
import hashlib
import requests

from auth_onedrive import get_token


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data_raw"
DATA_RAW_DIR.mkdir(exist_ok=True)

FOLDER_NAME = "FACTURAS_2026"
GRAPH_ROOT = "https://graph.microsoft.com/v1.0"


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def graph_get(url: str, headers: dict, params: dict | None = None) -> dict:
    response = requests.get(url, headers=headers, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def find_folder_id(headers: dict, folder_name: str) -> str:
    print("1) Buscando carpeta en OneDrive root...")

    url = f"{GRAPH_ROOT}/me/drive/root/children"
    data = graph_get(url, headers=headers)

    for item in data.get("value", []):
        if item.get("name") == folder_name and "folder" in item:
            folder_id = item["id"]
            print(f"Carpeta encontrada: {folder_name}")
            print(f"Folder ID: {folder_id}")
            return folder_id

    raise FileNotFoundError(f"No se encontro la carpeta '{folder_name}' en OneDrive.")


def list_folder_items(headers: dict, folder_id: str) -> list[dict]:
    print("2) Listando archivos de la carpeta...")

    items: list[dict] = []
    url = f"{GRAPH_ROOT}/me/drive/items/{folder_id}/children"

    while url:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    print(f"Items encontrados: {len(items)}")
    return items


def download_file_content(item: dict, headers: dict) -> bytes:
    download_url = item.get("@microsoft.graph.downloadUrl")

    if download_url:
        response = requests.get(download_url, timeout=120)
        response.raise_for_status()
        return response.content

    item_id = item["id"]
    content_url = f"{GRAPH_ROOT}/me/drive/items/{item_id}/content"
    response = requests.get(content_url, headers=headers, timeout=120)
    response.raise_for_status()
    return response.content


def save_if_changed(file_name: str, content: bytes) -> tuple[bool, str]:
    """
    Guarda el archivo solo si el contenido es distinto.
    Retorna:
    - changed: bool
    - status: str
    """
    output_path = DATA_RAW_DIR / file_name
    new_hash = sha256_bytes(content)

    if output_path.exists():
        current_hash = sha256_file(output_path)

        if current_hash == new_hash:
            return False, "SIN_CAMBIOS"

    with open(output_path, "wb") as f:
        f.write(content)

    return True, "ACTUALIZADO"


def main() -> None:
    print("INICIO DESCARGA ONEDRIVE -> DATA_RAW")
    print("Obteniendo token...")

    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}"
    }

    folder_id = find_folder_id(headers, FOLDER_NAME)
    items = list_folder_items(headers, folder_id)

    excel_items = [
        item for item in items
        if item.get("name", "").lower().endswith(".xlsx")
    ]

    print(f"Archivos XLSX detectados: {len(excel_items)}")

    downloaded = 0
    updated = 0
    skipped = 0

    for item in excel_items:
        file_name = item["name"]
        print(f"Procesando archivo: {file_name}")

        try:
            content = download_file_content(item, headers)
            downloaded += 1

            changed, status = save_if_changed(file_name, content)

            if changed:
                updated += 1
            else:
                skipped += 1

            print(f"Resultado: {file_name} -> {status}")

        except Exception as e:
            print(f"ERROR descargando {file_name}: {e}")
            # Continuar con el siguiente archivo en lugar de detener

    print("\nRESUMEN DESCARGA")
    print(f"Carpeta local: {DATA_RAW_DIR}")
    print(f"Archivos descargados leidos: {downloaded}")
    print(f"Archivos actualizados: {updated}")
    print(f"Archivos sin cambios: {skipped}")


if __name__ == "__main__":
    main()