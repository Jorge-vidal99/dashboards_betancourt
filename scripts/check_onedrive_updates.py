from pathlib import Path
import json
import sys
import requests

from auth_onedrive import get_token


BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(exist_ok=True)

CONTROL_FILE = STATE_DIR / "onedrive_control.json"

FOLDER_NAME = "FACTURAS_2026"
GRAPH_ROOT = "https://graph.microsoft.com/v1.0"


def graph_get(url: str, headers: dict, params: dict | None = None) -> dict:
    response = requests.get(url, headers=headers, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def find_folder_id(headers: dict, folder_name: str) -> str:
    url = f"{GRAPH_ROOT}/me/drive/root/children"
    data = graph_get(url, headers=headers)

    for item in data.get("value", []):
        if item.get("name") == folder_name and "folder" in item:
            return item["id"]

    raise FileNotFoundError(f"No se encontro la carpeta '{folder_name}' en OneDrive.")


def list_folder_items(headers: dict, folder_id: str) -> list[dict]:
    items: list[dict] = []
    url = f"{GRAPH_ROOT}/me/drive/items/{folder_id}/children"

    while url:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return items


def build_remote_state(items: list[dict]) -> dict:
    excel_items = [
        item for item in items
        if item.get("name", "").lower().endswith(".xlsx")
    ]

    state = {}
    for item in sorted(excel_items, key=lambda x: x.get("name", "")):
        state[item["name"]] = {
            "id": item.get("id"),
            "size": item.get("size"),
            "lastModifiedDateTime": item.get("lastModifiedDateTime"),
            "eTag": item.get("eTag"),
        }

    return state


def load_last_state():
    if not CONTROL_FILE.exists():
        return None

    with open(CONTROL_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("state")


def save_state(state: dict):
    with open(CONTROL_FILE, "w", encoding="utf-8") as f:
        json.dump({"state": state}, f, indent=2, ensure_ascii=False)


def compare_states(old: dict | None, new: dict) -> list[str]:
    if old is None:
        return list(new.keys())

    changed = []

    old_keys = set(old.keys())
    new_keys = set(new.keys())

    added = new_keys - old_keys
    removed = old_keys - new_keys
    common = old_keys & new_keys

    for k in sorted(added):
        changed.append(f"AGREGADO: {k}")

    for k in sorted(removed):
        changed.append(f"ELIMINADO: {k}")

    for k in sorted(common):
        if old[k] != new[k]:
            changed.append(f"MODIFICADO: {k}")

    return changed


def main():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    folder_id = find_folder_id(headers, FOLDER_NAME)
    items = list_folder_items(headers, folder_id)

    current_state = build_remote_state(items)
    last_state = load_last_state()

    if not current_state:
        print(json.dumps({
            "ok": False,
            "should_run": False,
            "reason": "NO_XLSX_EN_ONEDRIVE",
            "changed_files": []
        }, ensure_ascii=False))
        sys.exit(1)

    changed_files = compare_states(last_state, current_state)

    result = {
        "ok": True,
        "should_run": len(changed_files) > 0,
        "reason": "CAMBIOS_DETECTADOS_EN_ONEDRIVE" if changed_files else "SIN_CAMBIOS_EN_ONEDRIVE",
        "changed_files": changed_files,
        "files": list(current_state.keys()),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if changed_files:
        save_state(current_state)

    # Si no había baseline, lo tratamos como cambio inicial y guardamos estado
    if last_state is None:
        save_state(current_state)

    sys.exit(0)


if __name__ == "__main__":
    main()