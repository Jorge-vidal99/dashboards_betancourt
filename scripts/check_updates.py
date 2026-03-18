from pathlib import Path
import json
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data_raw"
CONTROL_FILE = DATA_RAW / ".control.json"


def get_latest_modification():
    files = list(DATA_RAW.glob("*.xlsx"))
    if not files:
        return None
    return max(f.stat().st_mtime for f in files)


def load_last():
    if not CONTROL_FILE.exists():
        return None

    with open(CONTROL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("last_mod")


def save_last(value):
    with open(CONTROL_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_mod": value}, f)


def main():
    current = get_latest_modification()
    last = load_last()

    if current is None:
        print(json.dumps({
            "ok": False,
            "should_run": False,
            "reason": "No hay archivos XLSX en data_raw",
            "last": last,
            "current": current
        }))
        sys.exit(1)

    if last is None:
        save_last(current)
        print(json.dumps({
            "ok": True,
            "should_run": True,
            "reason": "PRIMERA_EJECUCION",
            "last": last,
            "current": current
        }))
        sys.exit(0)

    if current != last:
        save_last(current)
        print(json.dumps({
            "ok": True,
            "should_run": True,
            "reason": "CAMBIOS_DETECTADOS",
            "last": last,
            "current": current
        }))
        sys.exit(0)

    print(json.dumps({
        "ok": True,
        "should_run": False,
        "reason": "SIN_CAMBIOS",
        "last": last,
        "current": current
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()