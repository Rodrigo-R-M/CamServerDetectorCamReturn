import time
import tkinter as tk
import cv2
from tkinter import messagebox
import requests
import http.cookiejar as cookielib
import os
import socket
import threading
import json
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

API_BASE_URL = "https://apidetectorcamreturn.onrender.com"
PORT_CAMARA = 8081
TUNNEL_URL = None
cookie_file = "cookies.txt"
nombre_equipo = socket.gethostname()
direccion_ip = socket.gethostbyname(nombre_equipo)

session = requests.Session()
session.cookies = cookielib.MozillaCookieJar(cookie_file)

camara_encendida = False
camaras_disponibles = []
camaras_activas = {}  # Diccionario para mantener las cámaras abiertas

# Cargar cookies previas si existen
if os.path.exists(cookie_file):
    try:
        session.cookies.load(ignore_discard=True)
    except:
        pass

# Variables globales
usuario_autenticado = None
httpd = None
server_thread = None
alternar_estado_pendiente = False


def detectar_camaras():
    """Detecta automáticamente las cámaras disponibles en el sistema"""
    camaras_encontradas = []
    print("🔍 Detectando cámaras disponibles...")

    # Probar hasta 10 índices de cámara
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap is not None and cap.isOpened():
            # Verificar si realmente puede leer frames
            ret, frame = cap.read()
            if ret and frame is not None:
                camaras_encontradas.append(i)
                print(f"📷 Cámara encontrada en índice {i}")
            cap.release()
        else:
            if cap:
                cap.release()

    print(f"✅ Total de cámaras detectadas: {len(camaras_encontradas)}")
    return camaras_encontradas


def abrir_camaras(indices):
    """Abre las cámaras especificadas y las mantiene en memoria"""
    global camaras_activas

    # Cerrar cámaras previas
    cerrar_todas_camaras()

    for idx in indices:
        try:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                # Configurar propiedades de la cámara
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                camaras_activas[idx] = cap
                print(f"✅ Cámara {idx} abierta y configurada")
            else:
                print(f"❌ No se pudo abrir la cámara {idx}")
        except Exception as e:
            print(f"❌ Error al abrir cámara {idx}: {e}")

def iniciar_ngrok():
    global TUNNEL_URL
    try:
        # Iniciar ngrok en segundo plano
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", str(PORT_CAMARA)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Esperar a que ngrok se inicie
        time.sleep(2)

        # Obtener la URL pública
        import requests
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                TUNNEL_URL = tunnel["public_url"]
                print(f"🌐 Túnel público: {TUNNEL_URL}")
                break

        if not TUNNEL_URL:
            raise Exception("No se pudo obtener URL de ngrok")

    except Exception as e:
        print(f"❌ Error al iniciar ngrok: {e}")
        TUNNEL_URL = None

def cerrar_todas_camaras():
    """Cierra todas las cámaras activas"""
    global camaras_activas

    for idx, cap in camaras_activas.items():
        try:
            cap.release()
            print(f"🔒 Cámara {idx} cerrada")
        except Exception as e:
            print(f"❌ Error al cerrar cámara {idx}: {e}")

    camaras_activas.clear()


class SimpleHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suprimir logs de HTTP para limpiar la consola
        pass

    def do_GET(self):
        global alternar_estado_pendiente, camaras_disponibles

        parsed_path = urlparse(self.path)
        route = parsed_path.path

        if route == "/activar-camara":
            alternar_estado_pendiente = True
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Para CORS
            self.end_headers()
            response = {
                "status": "ok",
                "message": "Cambio de estado solicitado",
                "camaras_disponibles": camaras_disponibles
            }
            self.wfile.write(json.dumps(response).encode())

        elif route == "/desactivar-camara":
            # Agregar endpoint para desactivar
            global camara_encendida
            camara_encendida = False
            cerrar_todas_camaras()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"status": "ok", "message": "Cámaras desactivadas"}
            self.wfile.write(json.dumps(response).encode())

        elif route == "/listar-camaras":
            # Nuevo endpoint para listar cámaras
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "camaras": camaras_disponibles,
                "camara_activa": camara_encendida,
                "total_camaras": len(camaras_disponibles)
            }
            self.wfile.write(json.dumps(response).encode())

        elif route == "/info-camaras":
            # Endpoint para obtener información de cámaras disponibles
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "camaras_disponibles": camaras_disponibles,
                "camara_activa": camara_encendida,
                "total_camaras": len(camaras_disponibles)
            }
            self.wfile.write(json.dumps(response).encode())

        elif route.startswith("/video/"):
            try:
                id_str = route.split("/")[-1]
                cam_index = int(id_str)
            except (ValueError, IndexError):
                self.send_error(400, "Índice de cámara inválido")
                return

            if not camara_encendida:
                self.send_error(503, "Sistema de cámaras desactivado")
                return

            if cam_index not in camaras_activas:
                self.send_error(404, f"Cámara {cam_index} no disponible")
                return

            # Configurar headers para streaming
            self.send_response(200)
            self.send_header("Content-type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            cap = camaras_activas[cam_index]

            try:
                while camara_encendida and cam_index in camaras_activas:
                    success, frame = cap.read()
                    if not success:
                        print(f"⚠️ No se pudo leer frame de cámara {cam_index}")
                        break

                    # Redimensionar frame si es muy grande
                    height, width = frame.shape[:2]
                    if width > 800:
                        scale = 800 / width
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height))

                    # Codificar frame a JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if not ret:
                        continue

                    try:
                        # Enviar frame en formato multipart
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(buffer)}\r\n\r\n".encode())
                        self.wfile.write(buffer.tobytes())
                        self.wfile.write(b"\r\n")
                    except BrokenPipeError:
                        # El cliente se desconectó
                        break

                    # Pequeña pausa para controlar FPS
                    time.sleep(0.033)  # ~30 FPS

            except Exception as e:
                print(f"⚠️ Stream de cámara {cam_index} interrumpido: {e}")
            finally:
                print(f"🔚 Stream de cámara {cam_index} terminado")

        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b"Servidor de camara activo")


def iniciar_servidor():
    global httpd
    try:
        httpd = HTTPServer((direccion_ip, PORT_CAMARA), SimpleHandler)
        print(f"📡 Servidor iniciado en {direccion_ip}:{PORT_CAMARA}")
        httpd.serve_forever()
    except Exception as e:
        print("❌ Error al iniciar servidor:", e)


def detener_servidor():
    global httpd
    if httpd:
        print("🛑 Deteniendo servidor...")
        httpd.shutdown()
        httpd = None


def registrar_estado_camara(activa):
    if activa and TUNNEL_URL:
        payload = {"estado": activa, "ip": TUNNEL_URL, "puerto": ""}  # Puerto no necesario
    else:
        payload = {"estado": False}

    try:
        response = session.post(f"{API_BASE_URL}/estado-camara", json=payload)
        print(f"📨 Estado de cámara enviado: {payload}, respuesta: {response.status_code}")
    except Exception as e:
        print("❌ Error al notificar estado de cámara:", e)


def verificar_sesion_guardada():
    global usuario_autenticado
    print("🔎 Verificando sesión guardada...")
    try:
        resp = session.get(f"{API_BASE_URL}/check-auth")
        print(f"➡️ Respuesta status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            usuario_autenticado = data["user"]
            print(f"✅ Sesión activa: {usuario_autenticado}")
            mostrar_ventana_principal()
            return True
        else:
            print("⚠️ Sesión no válida.")
    except Exception as e:
        print("❌ Error al verificar sesión:", e)
    return False


def verificar_login():
    global usuario_autenticado, server_thread, camaras_disponibles

    usuario = entry_usuario.get() + "_server"
    contrasena = entry_contrasena.get()
    payload = {"username": usuario, "password": contrasena}

    try:
        print("🔐 Intentando login...")
        response = session.post(f"{API_BASE_URL}/login", json=payload)
        if response.status_code == 200:
            session.cookies.save(ignore_discard=True)
            check = session.get(f"{API_BASE_URL}/check-auth")
            if check.status_code == 200:
                usuario_autenticado = check.json()["user"]

                # Iniciar ngrok
                ngrok_thread = threading.Thread(target=iniciar_ngrok, daemon=True)
                ngrok_thread.start()
                time.sleep(3)  # Esperar a que ngrok se inicie

                if not TUNNEL_URL:
                    messagebox.showerror("Error", "No se pudo iniciar ngrok")
                    return

                # Detectar cámaras disponibles
                camaras_disponibles = detectar_camaras()

                # Iniciar servidor en hilo
                server_thread = threading.Thread(target=iniciar_servidor, daemon=True)
                server_thread.start()

                registrar_estado_camara(True)
                ventana_login.destroy()
                mostrar_ventana_principal()
            else:
                messagebox.showerror("Error", "Sesión inválida tras login.")
        else:
            messagebox.showerror("Error", "Credenciales inválidas.")
    except Exception as e:
        print("❌ Error en login:", e)
        messagebox.showerror("Error de conexión", str(e))


def cerrar_sesion(ventana):
    global camaras_activas

    registrar_estado_camara(False)

    # Cerrar todas las cámaras
    cerrar_todas_camaras()

    try:
        session.post(f"{API_BASE_URL}/logout")
    except:
        pass

    session.cookies.clear()
    if os.path.exists(cookie_file):
        os.remove(cookie_file)

    detener_servidor()
    ventana.destroy()
    iniciar_login()


def mostrar_ventana_principal():
    global camara_encendida, camaras_disponibles

    ventana = tk.Tk()
    ventana.title("Panel Principal - Servidor de Cámara")
    ventana.geometry("400x300")

    tk.Label(ventana, text=f"👤 Usuario: {usuario_autenticado}", anchor="w").place(x=10, y=5)
    tk.Label(ventana, text=f"🌐 IP: {direccion_ip}:{PORT_CAMARA}", anchor="w").place(x=10, y=25)
    tk.Label(ventana, text=f"📹 Cámaras detectadas: {len(camaras_disponibles)}", anchor="w").place(x=10, y=45)

    # Mostrar índices de cámaras disponibles
    camaras_text = ", ".join(map(str, camaras_disponibles)) if camaras_disponibles else "Ninguna"
    tk.Label(ventana, text=f"📋 Índices: {camaras_text}", anchor="w").place(x=10, y=65)

    tk.Button(ventana, text="Cerrar sesión", command=lambda: cerrar_sesion(ventana)).place(x=10, y=90)

    estado_label = tk.StringVar()
    estado_label.set("🔴 Sistema de cámaras desactivado")

    def alternar_estado():
        global camara_encendida
        camara_encendida = not camara_encendida

        if camara_encendida:
            if camaras_disponibles:
                estado_label.set("🟢 Sistema de cámaras activado")
                abrir_camaras(camaras_disponibles)
                print("✅ Sistema de cámaras activado")
                print(f"📷 Cámaras activas: {list(camaras_activas.keys())}")
            else:
                estado_label.set("⚠️ No hay cámaras disponibles")
                camara_encendida = False
                print("⚠️ No se pueden activar cámaras: no hay dispositivos disponibles")
        else:
            estado_label.set("🔴 Sistema de cámaras desactivado")
            cerrar_todas_camaras()
            print("🛑 Sistema de cámaras desactivado")

    tk.Button(ventana, text="🎥 Alternar Estado Cámaras",
              command=alternar_estado).place(x=10, y=130)

    estado_frame = tk.Frame(ventana)
    estado_frame.place(x=10, y=170, width=380, height=40)
    tk.Label(estado_frame, textvariable=estado_label,
             wraplength=370, justify="left").pack()

    # Función para revisar eventos remotos - CORREGIDO
    def procesar_eventos_remotos():
        global alternar_estado_pendiente
        try:
            if alternar_estado_pendiente:
                alternar_estado_pendiente = False
                alternar_estado()
                print("🔄 Estado alterado por petición remota")
        except Exception as e:
            print(f"❌ Error en procesar_eventos_remotos: {e}")
        finally:
            # Programar la siguiente verificación
            ventana.after(1000, procesar_eventos_remotos)

    # Botón para redetectar cámaras
    def redetectar_camaras():
        global camaras_disponibles
        camaras_disponibles = detectar_camaras()
        camaras_text = ", ".join(map(str, camaras_disponibles)) if camaras_disponibles else "Ninguna"
        # Actualizar la etiqueta (necesitaríamos una referencia, simplificamos con print)
        print(f"🔄 Cámaras redetectadas: {camaras_text}")
        messagebox.showinfo("Redetección", f"Cámaras encontradas: {len(camaras_disponibles)}\nÍndices: {camaras_text}")

    tk.Button(ventana, text="🔄 Redetectar Cámaras",
              command=redetectar_camaras).place(x=200, y=130)

    # Iniciar el procesamiento de eventos remotos
    procesar_eventos_remotos()

    ventana.mainloop()


def iniciar_login():
    global entry_usuario, entry_contrasena, ventana_login
    ventana_login = tk.Tk()
    ventana_login.title("Servidor de Cámara - Login")
    ventana_login.geometry("350x250")

    tk.Label(ventana_login, text="🎥 Servidor de DetectorCam",
             font=("Arial", 14, "bold")).pack(pady=10)

    tk.Label(ventana_login, text="Usuario:").pack(pady=5)
    entry_usuario = tk.Entry(ventana_login)
    entry_usuario.pack()

    tk.Label(ventana_login, text="Contraseña:").pack(pady=5)
    entry_contrasena = tk.Entry(ventana_login, show="*")
    entry_contrasena.pack()

    tk.Button(ventana_login, text="Iniciar sesión",
              command=verificar_login).pack(pady=20)

    # Info del servidor
    info_frame = tk.Frame(ventana_login)
    info_frame.pack(pady=10)
    tk.Label(info_frame, text=f"IP: {direccion_ip}",
             font=("Arial", 9)).pack()
    tk.Label(info_frame, text=f"Puerto: {PORT_CAMARA}",
             font=("Arial", 9)).pack()

    ventana_login.mainloop()


if __name__ == "__main__":
    print("🚀 Iniciando servidor de cámaras...")
    print(f"🌐 IP del equipo: {direccion_ip}")
    print(f"🔌 Puerto configurado: {PORT_CAMARA}")

    # Detectar cámaras al inicio
    camaras_disponibles = detectar_camaras()

    resultado = verificar_sesion_guardada()
    print(f"🧪 Resultado de verificación: {resultado}")
    if not resultado:
        print("🔒 Mostrando ventana de login")
        iniciar_login()