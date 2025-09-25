# ngrok.py
import subprocess
import requests
import time
import os
import platform
import shutil
from config import PORT_CAMARA

ngrok_process = None
ngrok_url = None

def descargar_ngrok():
    sistema = platform.system().lower()
    arquitectura = platform.machine().lower()

    if sistema == "windows":
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
        bin_name = "ngrok.exe"
    elif sistema == "darwin":
        if "arm" in arquitectura or "aarch" in arquitectura:
            url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-arm64.zip"
        else:
            url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-amd64.zip"
        bin_name = "ngrok"
    else:
        if "arm" in arquitectura or "aarch" in arquitectura:
            url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz"
        else:
            url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
        bin_name = "ngrok"

    print(f"⬇️ Descargando ngrok para {sistema} ({arquitectura})...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        if sistema in ("darwin", "linux"):
            import tarfile
            with open("ngrok.tgz", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            with tarfile.open("ngrok.tgz") as tar:
                tar.extractall()
            os.chmod("ngrok", 0o755)
            os.remove("ngrok.tgz")
        else:
            import zipfile
            with open("ngrok.zip", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            with zipfile.ZipFile("ngrok.zip", 'r') as zip_ref:
                zip_ref.extractall()
            os.remove("ngrok.zip")
        return os.path.abspath(bin_name)
    except Exception as e:
        print(f"❌ Error al descargar ngrok: {e}")
        return None

def iniciar_ngrok(puerto_local=PORT_CAMARA):
    global ngrok_process, ngrok_url

    bin_name = "ngrok.exe" if platform.system().lower() == "windows" else "ngrok"
    bin_path = bin_name

    # Buscar ngrok en PATH o en la carpeta actual
    if not os.path.exists(bin_path):
        if shutil.which("ngrok"):
            bin_path = "ngrok"
        else:
            ruta = descargar_ngrok()
            if not ruta:
                print("⚠️ No se pudo iniciar ngrok. Usando URL local.")
                return f"http://localhost:{puerto_local}"
            bin_path = ruta

    try:
        # Iniciar ngrok en segundo plano
        cmd = [bin_path, "http", str(puerto_local), "--log=stdout"]
        ngrok_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        print("⏳ Iniciando ngrok...")
        time.sleep(3)  # Esperar a que ngrok se estabilice

        # Obtener la URL desde la API local de ngrok
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                data = response.json()
                for tunnel in data.get("tunnels", []):
                    if tunnel["proto"] == "https":
                        ngrok_url = tunnel["public_url"]
                        print(f"✅ Túnel público listo: {ngrok_url}")
                        break
        except Exception as e:
            print(f"⚠️ No se pudo obtener la URL de ngrok: {e}")

        if not ngrok_url:
            print("⚠️ No se encontró URL HTTPS. Usando URL local.")
            return f"http://localhost:{puerto_local}"

        import atexit
        atexit.register(detener_ngrok)
        return ngrok_url

    except Exception as e:
        print(f"❌ Error al iniciar ngrok: {e}")
        return f"http://localhost:{puerto_local}"

def detener_ngrok():
    global ngrok_process
    if ngrok_process:
        print("🛑 Cerrando túnel de ngrok...")
        ngrok_process.terminate()
        try:
            ngrok_process.wait(timeout=5)
        except:
            ngrok_process.kill()
        ngrok_process = None

def obtener_url_publica():
    global ngrok_url
    if ngrok_url is None:
        ngrok_url = iniciar_ngrok()
    return ngrok_url