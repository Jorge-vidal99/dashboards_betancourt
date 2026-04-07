import sys
import subprocess
import smtplib
import json
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ── Configuración email ──────────────────────────────────────────────
EMAIL_FROM    = "jorge.vidallaro@gmail.com"
EMAIL_TO      = "facturacion@transportesbetancourt.cl"
EMAIL_PASS    = "mngz sheu fbuj kpvh"  # ← reemplaza esto

def send_email(subject: str, body: str) -> None:
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_FROM
        msg["To"]      = EMAIL_TO
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_FROM, EMAIL_PASS)
            smtp.send_message(msg)
        print(f"Email enviado: {subject}")
    except Exception as e:
        print(f"Error enviando email: {e}")

# ── Ejecutar paso ────────────────────────────────────────────────────
def run_step(title: str, args: list[str], log_file) -> None:
    sep = "\n" + "=" * 70 + "\n"
    header = f"{sep}{title}\nCMD: {' '.join(args)}\n" + "=" * 70 + "\n"
    print(header, end="")
    log_file.write(header)
    log_file.flush()

    proc = subprocess.Popen(
        args, cwd=str(BASE_DIR),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in proc.stdout:
        print(line, end="")
        log_file.write(line)
    proc.wait()

    if proc.returncode != 0:
        msg = f"\nERROR: Falló {title} (exit code={proc.returncode})\n"
        print(msg, end="")
        log_file.write(msg)
        raise RuntimeError(msg)

# ── Verificar cambios en OneDrive ───────────────────────────────────
def check_onedrive() -> bool:
    result = subprocess.run(
        [sys.executable, "scripts/check_onedrive_updates.py"],
        cwd=str(BASE_DIR), capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
        print(f"OneDrive check: {data.get('reason', 'sin info')}")
        return data.get("should_run", False)
    except Exception:
        print("Error parseando respuesta OneDrive — ejecutando pipeline igual")
        return True

# ── Git push ─────────────────────────────────────────────────────────
def git_push(log_file) -> None:
    run_step("3) GIT ADD + COMMIT + PUSH", [
        "git", "-C", str(BASE_DIR), "add", "-A"
    ], log_file)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    run_step("3b) GIT COMMIT", [
        "git", "-C", str(BASE_DIR), "commit", "-m", f"auto: actualización {ts}"
    ], log_file)
    run_step("3c) GIT PUSH", [
        "git", "-C", str(BASE_DIR), "push"
    ], log_file)

# ── Main ─────────────────────────────────────────────────────────────
def main() -> None:
    py  = sys.executable
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"pipeline_{ts}.log"

    print(f"\n{'='*70}")
    print(f"Pipeline iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    # Verificar cambios
    if not check_onedrive():
        print("Sin cambios en OneDrive — pipeline omitido.")
        return

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Pipeline start: {datetime.now().isoformat()}\n")
        try:
            run_step("1) DESCARGA OneDrive → data_raw",
                     [py, "scripts/download_facturas_2026.py"], f)
            run_step("2) PROCESO data_raw → data_processed",
                     [py, "scripts/process_facturas.py"], f)
            git_push(f)

            msg = "\nPipeline completo OK ✅\n"
            print(msg)
            f.write(msg)
            send_email(
                "✅ Pipeline Betancourt OK",
                f"Pipeline ejecutado exitosamente.\nLog: {log_path}\nFecha: {datetime.now()}"
            )

        except RuntimeError as e:
            send_email(
                "❌ ERROR Pipeline Betancourt",
                f"Error en pipeline:\n{e}\nLog: {log_path}\nFecha: {datetime.now()}"
            )
            sys.exit(1)

    print(f"\nLog guardado en: {log_path}")

if __name__ == "__main__":
    main()