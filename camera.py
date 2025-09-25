import cv2

camaras_activas = {}
camara_encendida = False
camaras_disponibles = []

def detectar_camaras(max_index=10):
    camaras = []
    print("🔍 Detectando cámaras...")
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                camaras.append(i)
                print(f"📷 Cámara encontrada: {i}")
            cap.release()
    print(f"✅ Cámaras detectadas: {len(camaras)}")
    return camaras


def abrir_camaras(indices):
    global camaras_activas
    cerrar_todas_camaras()
    for idx in indices:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            camaras_activas[idx] = cap
            print(f"✅ Cámara {idx} abierta")
        else:
            print(f"❌ No se pudo abrir cámara {idx}")


def cerrar_todas_camaras():
    global camaras_activas
    for idx, cap in camaras_activas.items():
        try:
            cap.release()
            print(f"🔒 Cámara {idx} cerrada")
        except:
            pass
    camaras_activas.clear()