# main.py (servidor)
from gui import iniciar_login
from auth import verificar_sesion_guardada
from camera import detectar_camaras
from server import iniciar_servidor
from api_client import registrar_estado_camara
import threading


def main():
    print("🚀 Iniciando servidor de cámaras...")
    camaras = detectar_camaras()
    usuario = verificar_sesion_guardada()
    if usuario:
        server_thread = threading.Thread(target=iniciar_servidor, daemon=True)
        server_thread.start()

        # ✅ Iniciar ngrok y registrar
        from ngrok import obtener_url_publica
        url_publica = obtener_url_publica()

        registrar_estado_camara(True)
        from gui import mostrar_ventana_principal
        mostrar_ventana_principal(usuario, server_thread)
    else:
        iniciar_login()


if __name__ == "__main__":
    main()