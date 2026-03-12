import sys
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


def run_step(title: str, args: list[str], log_file) -> None:
    sep = "\n" + "=" * 70 + "\n"
    header = f"{sep}{title}\nCMD: {' '.join(args)}\n" + "=" * 70 + "\n"

    print(header, end="")
    log_file.write(header)
    log_file.flush()

    # Ejecuta y “tee” a consola + archivo
    proc = subprocess.Popen(
        args,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in proc.stdout:
        print(line, end="")
        log_file.write(line)
    proc.wait()

    if proc.returncode != 0:
        msg = f"\n❌ Falló: {title} (exit code={proc.returncode})\n"
        print(msg, end="")
        log_file.write(msg)
        raise SystemExit(proc.returncode)


def main() -> None:
    py = sys.executable
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"pipeline_{ts}.log"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Pipeline start: {datetime.now().isoformat()}\n")
        f.write(f"Python: {py}\n")
        f.write(f"Base dir: {BASE_DIR}\n")

        run_step("1) DESCARGA OneDrive → data_raw", [py, "scripts/download_facturas_2026.py"], f)
        run_step("2) PROCESO data_raw → data_processed", [py, "scripts/process_facturas.py"], f)

        done = "\n✅ Pipeline completo OK.\n   - data_raw actualizado\n   - data_processed actualizado\n"
        print(done, end="")
        f.write(done)

    print(f"\n🧾 Log guardado en: {log_path}")


if __name__ == "__main__":
    main()