from pathlib import Path
import json
import sys
import hashlib

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data_raw"
CONTROL_FILE = DATA_RAW / ".control.json"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_current_state():
    files = sorted(DATA_RAW.glob("*.xlsx"))
    if not files:
        return None

    state = {}
    for f in files:
        state[f.name] = {
            "size": f.stat().st_size,
            "sha256": file_sha256(f),
        }
    return state


def load_last_state():
    if not CONTROL_FILE.exists():
        return None

    with open(CONTROL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("state")


def save_state(state):
    with open(CONTROL_FILE, "w", encoding="utf-8") as f:
        json.dump({"state": state}, f, indent=2)


def main():
    current_state = get_current_state()
    last_state = load_last_state()

    if current_state is None:
        print(json.dumps({
            "ok": False,
            "should_run": False,
            "reason": "NO_XLSX_EN_DATA_RAW"
        }))
        sys.exit(1)

    if last_state is None:
        save_state(current_state)
        print(json.dumps({
            "ok": True,
            "should_run": True,
            "reason": "PRIMERA_EJECUCION"
        }))
        sys.exit(0)

    if current_state != last_state:
        save_state(current_state)
        print(json.dumps({
            "ok": True,
            "should_run": True,
            "reason": "CAMBIOS_DETECTADOS"
        }))
        sys.exit(0)

    print(json.dumps({
        "ok": True,
        "should_run": False,
        "reason": "SIN_CAMBIOS"
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()