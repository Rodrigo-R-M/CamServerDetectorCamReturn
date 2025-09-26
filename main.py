# main.py (servidor)
from gui import iniciar_login
from auth import verificar_sesion_guardada
from camera import detectar_camaras  # Solo importamos la función
from server import iniciar_servidor
from api_client import registrar_estado_camara
import threading


def main():
    try:
        print("🚀 Iniciando servidor de cámaras...")
        usuario = verificar_sesion_guardada()
        if usuario:
            detectar_camaras()

            # 1. Iniciar el servidor de cámaras
            server_thread = threading.Thread(target=iniciar_servidor, daemon=True)
            server_thread.start()

            # 2. ✅ INICIAR NGROK Y OBTENER LA URL
            from ngrok import obtener_url_publica
            url_publica = obtener_url_publica()  # ← Esta línea es clave

            # 3. Registrar en la API
            registrar_estado_camara(True)

            # 4. Mostrar GUI
            from gui import mostrar_ventana_principal
            mostrar_ventana_principal(usuario, server_thread)
        else:
            iniciar_login()

    except KeyboardInterrupt:
        print("\n🛑 Cerrando servidor...")
        from ngrok import detener_ngrok
        detener_ngrok()
        from server import detener_servidor
        detener_servidor()
        exit(0)

if __name__ == "__main__":
    main()