# gui.py
import tkinter as tk
from tkinter import messagebox
import threading
from config import DIRECCION_IP, PORT_CAMARA
from camera import detectar_camaras, abrir_camaras, cerrar_todas_camaras, camaras_disponibles
from auth import verificar_login, cerrar_sesion_completa
from api_client import registrar_estado_camara
import estado


def mostrar_ventana_principal(usuario_autenticado, camaras_disponibles, server_thread):
    ventana = tk.Tk()
    ventana.title("Panel Principal - Servidor de Cámara")
    ventana.geometry("450x350")

    tk.Label(ventana, text=f"👤 Usuario: {usuario_autenticado}").place(x=10, y=5)
    tk.Label(ventana, text=f"🌐 IP Local: {DIRECCION_IP}:{PORT_CAMARA}").place(x=10, y=25)

    # Etiqueta para la URL pública (inicialmente en "Cargando...")
    url_label = tk.Label(ventana, text="🌍 URL Pública: Cargando...", fg="blue", wraplength=430)
    url_label.place(x=10, y=45)

    tk.Label(ventana, text=f"📹 Cámaras: {len(camaras_disponibles)}").place(x=10, y=85)
    camaras_str = ", ".join(map(str, camaras_disponibles)) if camaras_disponibles else "Ninguna"
    tk.Label(ventana, text=f"📋 Índices: {camaras_str}").place(x=10, y=105)

    def cerrar_sesion():
        from server import detener_servidor
        registrar_estado_camara(False)
        cerrar_todas_camaras()
        cerrar_sesion_completa()
        detener_servidor()
        from tunnel import detener_cloudflare_tunnel
        detener_cloudflare_tunnel()
        ventana.destroy()
        iniciar_login()

    tk.Button(ventana, text="Cerrar sesión", command=cerrar_sesion).place(x=10, y=135)

    estado_label = tk.StringVar()
    estado_label.set("🔴 Cámaras desactivadas")

    def alternar_estado():
        estado.camara_encendida = not estado.camara_encendida
        if estado.camara_encendida:
            if camaras_disponibles:
                estado_label.set("🟢 Cámaras activadas")
                abrir_camaras(camaras_disponibles)
            else:
                estado_label.set("⚠️ Sin cámaras")
                estado.camara_encendida = False
        else:
            estado_label.set("🔴 Cámaras desactivadas")
            cerrar_todas_camaras()

    tk.Button(ventana, text="🎥 Alternar Cámaras", command=alternar_estado).place(x=10, y=170)
    tk.Label(ventana, textvariable=estado_label, wraplength=400).place(x=10, y=210)

    def procesar_eventos():
        if estado.alternar_estado_pendiente_global:
            estado.alternar_estado_pendiente_global = False
            alternar_estado()
            print("🔄 Estado alterado por petición remota")
        ventana.after(1000, procesar_eventos)

    def redetectar_camaras():
        global camaras_disponibles
        camaras_disponibles = detectar_camaras()
        camaras_str = ", ".join(map(str, camaras_disponibles)) if camaras_disponibles else "Ninguna"
        messagebox.showinfo("Éxito", f"Cámaras: {len(camaras_disponibles)}\nÍndices: {camaras_str}")

    tk.Button(ventana, text="🔄 Redetectar", command=redetectar_camaras).place(x=220, y=170)

    # === FUNCIÓN CLAVE: Actualiza la URL pública en la GUI ===
    def actualizar_url_publica():
        from tunnel import cloudflare_url
        if cloudflare_url and cloudflare_url != "Cargando...":
            url_label.config(text=f"🌍 URL Pública: {cloudflare_url}", fg="blue")
        else:
            # Si aún no está lista, intenta de nuevo en 1 segundo
            ventana.after(1000, actualizar_url_publica)

    # Iniciar la verificación de la URL pública
    ventana.after(1000, actualizar_url_publica)

    procesar_eventos()
    ventana.mainloop()


def iniciar_login():
    ventana = tk.Tk()
    ventana.title("Login - Servidor de Cámara")
    ventana.geometry("350x250")

    tk.Label(ventana, text="🎥 Servidor DetectorCam", font=("Arial", 14)).pack(pady=10)
    tk.Label(ventana, text="Usuario:").pack()
    entry_user = tk.Entry(ventana)
    entry_user.pack()
    tk.Label(ventana, text="Contraseña:").pack()
    entry_pass = tk.Entry(ventana, show="*")
    entry_pass.pack()

    def _login():
        user = entry_user.get()
        pwd = entry_pass.get()
        usuario_ok = verificar_login(user, pwd)
        if usuario_ok:
            camaras = detectar_camaras()
            server_thread = threading.Thread(target=lambda: __import__('server').iniciar_servidor(), daemon=True)
            server_thread.start()
            registrar_estado_camara(True)
            ventana.destroy()
            mostrar_ventana_principal(usuario_ok, camaras, server_thread)
        else:
            messagebox.showerror("Error", "Credenciales inválidas")

    tk.Button(ventana, text="Iniciar sesión", command=_login).pack(pady=15)
    tk.Label(ventana, text=f"IP: {DIRECCION_IP} | Puerto: {PORT_CAMARA}").pack()
    ventana.mainloop()