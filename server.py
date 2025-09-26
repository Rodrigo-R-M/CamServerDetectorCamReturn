# server.py
import json
import time
import cv2
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from config import DIRECCION_IP, PORT_CAMARA
from camera import camaras_activas, camaras_disponibles, cerrar_todas_camaras,obtener_camaras_disponibles
import estado

httpd = None

class CameraHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def add_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self.add_cors_headers()
        self.end_headers()

    def do_GET(self):
        route = urlparse(self.path).path

        if route == "/":
            camaras = obtener_camaras_disponibles()
            if camaras and estado.camara_encendida:
                # Usar la primera cámara disponible
                self._stream_video(f"/video/{camaras[0]}")
            else:
                # Devolver un stream de error o placeholder
                self.send_response(200)
                self.add_cors_headers()
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Servidor de camara activo (sin camaras)")
            return

        if route == "/activar-camara":
            estado.camara_encendida = True
            from camera import abrir_camaras
            abrir_camaras([0])  # 👈 forzar cámara 0
            self._send_json({"status": "ok", "message": "Cámara activada"})

        elif route == "/desactivar-camara":
            estado.camara_encendida = False
            cerrar_todas_camaras()
            self._send_json({"status": "ok", "message": "Cámaras desactivadas"})


        elif route in ("/listar-camaras", "/info-camaras"):
            camaras = obtener_camaras_disponibles()
            self._send_json({
                "camaras": camaras,
                "camara_activa": estado.camara_encendida,
                "total_camaras": len(camaras)
            })

        elif route.startswith("/video/"):
            self._stream_video(route)

        else:
            self.send_response(200)
            self.add_cors_headers()
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Servidor de camara activo")

    def _send_json(self, data):
        self.send_response(200)
        self.add_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _stream_video(self, route):
        try:
            cam_index = int(route.split("/")[-1])
        except ValueError:
            self.send_error(400, "Índice inválido")
            return

        if not estado.camara_encendida or cam_index not in camaras_activas:
            # Si la cámara no está activa o no existe, devolver 404
            self.send_error(503 if not estado.camara_encendida else 404, "Cámara no disponible")
            return

        self.send_response(200)
        self.add_cors_headers()
        self.send_header("Content-type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        cap = camaras_activas[cam_index]
        try:
            while estado.camara_encendida and cam_index in camaras_activas:
                success, frame = cap.read()
                if not success:
                    break
                if frame.shape[1] > 800:
                    scale = 800 / frame.shape[1]
                    frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(buffer)}\r\n\r\n".encode())
                    self.wfile.write(buffer.tobytes())
                    self.wfile.write(b"\r\n")
                time.sleep(0.033)
        except Exception as e:
            print(f"⚠️ Error en stream: {e}")


def iniciar_servidor():
    global httpd
    try:
        httpd = HTTPServer(("", PORT_CAMARA), CameraHandler)
        print(f"📡 Servidor en http://localhost:{PORT_CAMARA}")
        httpd.serve_forever()
    except Exception as e:
        print("❌ Error al iniciar servidor:", e)


def detener_servidor():
    global httpd
    if httpd:
        print("🛑 Deteniendo servidor...")
        httpd.shutdown()
        httpd.server_close()
        httpd = None