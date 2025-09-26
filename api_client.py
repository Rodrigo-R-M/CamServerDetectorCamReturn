# api_client.py
import requests
import http.cookiejar as cookielib
import os
from config import API_BASE_URL, COOKIE_FILE, DIRECCION_IP, PORT_CAMARA

# Crear sesión con soporte de cookies
session = requests.Session()
session.cookies = cookielib.MozillaCookieJar(COOKIE_FILE)

# Cargar cookies previas si el archivo existe
if os.path.exists(COOKIE_FILE):
    try:
        session.cookies.load(ignore_discard=True)
        print("🍪 Cookies cargadas desde archivo.")
    except Exception as e:
        print(f"⚠️ Error al cargar cookies: {e}")

# === Funciones de comunicación con el backend ===

def registrar_estado_camara(activa):
    if activa:
        from ngrok import obtener_url_publica
        url = obtener_url_publica()
        payload = {
            "estado": True,
            "ip": DIRECCION_IP,
            "puerto": str(PORT_CAMARA),
            "url_publica": url
        }
    else:
        payload = {"estado": False}

    try:
        resp = session.post(f"{API_BASE_URL}/estado-camara", json=payload, timeout=10)
        print(f"📨 Estado de cámara enviado. Código: {resp.status_code}")
        if resp.status_code not in (200, 201):
            print(f"⚠️ Respuesta inesperada del backend: {resp.text}")
    except requests.exceptions.Timeout:
        print("❌ Timeout al registrar estado en el backend.")
    except Exception as e:
        print(f"❌ Error al registrar estado en el backend: {e}")


def login(username, password):
    payload = {"username": username, "password": password}
    try:
        return session.post(f"{API_BASE_URL}/login", json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Error en login: {e}")
        raise


def check_auth():
    try:
        return session.get(f"{API_BASE_URL}/check-auth", timeout=10)
    except Exception as e:
        print(f"❌ Error al verificar autenticación: {e}")
        raise


def logout():
    try:
        session.post(f"{API_BASE_URL}/logout", timeout=5)
    except Exception as e:
        print(f"⚠️ Error al cerrar sesión en el backend: {e}")


def save_cookies():
    try:
        session.cookies.save(ignore_discard=True)
        print("💾 Cookies guardadas.")
    except Exception as e:
        print(f"❌ Error al guardar cookies: {e}")


def clear_session():
    session.cookies.clear()
    if os.path.exists(COOKIE_FILE):
        os.remove(COOKIE_FILE)
        print("🧹 Sesión local limpiada.")