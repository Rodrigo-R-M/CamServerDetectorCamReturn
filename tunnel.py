import subprocess
import platform
import re
import os
import shutil
import requests
from config import CLOUDFLARED_PATH, DIRECCION_IP, PORT_CAMARA

cloudflared_process = None
cloudflare_url = None


def descargar_cloudflared():
    sistema = platform.system().lower()
    arquitectura = platform.machine().lower()

    if sistema == "windows":
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        bin_name = "cloudflared.exe"
    elif sistema == "darwin":
        if "arm" in arquitectura or "aarch" in arquitectura:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
        else:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
        bin_name = "cloudflared"
    else:
        if "arm" in arquitectura or "aarch" in arquitectura:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
        else:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        bin_name = "cloudflared"

    print(f"⬇️ Descargando cloudflared para {sistema}...")
    try:
        response = requests.get(url)
        response.raise_for_status()

        if sistema == "darwin" and url.endswith(".tgz"):
            import tarfile
            with open("cloudflared.tgz", "wb") as f:
                f.write(response.content)
            with tarfile.open("cloudflared.tgz") as tar:
                tar.extractall()
            os.chmod("cloudflared", 0o755)
            os.remove("cloudflared.tgz")
        else:
            with open(bin_name, "wb") as f:
                f.write(response.content)
            os.chmod(bin_name, 0o755)
        return os.path.abspath(bin_name)
    except Exception as e:
        print(f"❌ Error al descargar cloudflared: {e}")
        return None


def iniciar_cloudflare_tunnel(puerto_local=PORT_CAMARA):
    global cloudflared_process, cloudflare_url

    bin_path = CLOUDFLARED_PATH
    if not os.path.exists(bin_path):
        if shutil.which("cloudflared"):
            bin_path = "cloudflared"
        else:
            ruta = descargar_cloudflared()
            if not ruta:
                return f"http://{DIRECCION_IP}:{puerto_local}"
            bin_path = ruta

    try:
        cmd = [bin_path, "tunnel", "--url", f"http://localhost:{puerto_local}", "--no-autoupdate"]
        cloudflared_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        print("⏳ Esperando URL de Cloudflare...")

        for line in iter(cloudflared_process.stdout.readline, ''):
            match = url_pattern.search(line)
            if match:
                cloudflare_url = match.group(0)
                print(f"✅ Túnel listo: {cloudflare_url}")
                break

        if not cloudflare_url:
            return f"http://{DIRECCION_IP}:{puerto_local}"

        import atexit
        atexit.register(detener_cloudflare_tunnel)
        return cloudflare_url

    except Exception as e:
        print(f"❌ Error en Cloudflare Tunnel: {e}")
        return f"http://{DIRECCION_IP}:{puerto_local}"


def detener_cloudflare_tunnel():
    global cloudflared_process
    if cloudflared_process:
        print("🛑 Cerrando túnel de Cloudflare...")
        cloudflared_process.terminate()
        try:
            cloudflared_process.wait(timeout=5)
        except:
            cloudflared_process.kill()
        cloudflared_process = None


def obtener_url_publica():
    global cloudflare_url
    if cloudflare_url is None:
        cloudflare_url = iniciar_cloudflare_tunnel()
    return cloudflare_url