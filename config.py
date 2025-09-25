import socket
import os

# URLs y puertos
API_BASE_URL = "https://apidetectorcamreturn.onrender.com"
PORT_CAMARA = 8081

# Archivos
COOKIE_FILE = "cookies.txt"

# Información del sistema
NOMBRE_EQUIPO = socket.gethostname()
DIRECCION_IP = socket.gethostbyname(NOMBRE_EQUIPO)

# Rutas
CLOUDFLARED_PATH = "cloudflared.exe" if os.name == "nt" else "cloudflared"