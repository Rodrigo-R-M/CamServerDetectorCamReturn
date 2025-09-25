# camera.py
import cv2

camaras_activas = {}
camara_encendida = False
camaras_disponibles = []

def detectar_camaras(max_index=5):
    global camaras_disponibles
    camaras = []
    print("🔍 Detectando cámaras...")
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                camaras.append(i)
                print(f"📷 Cámara {i}: Frame size {frame.shape}")
            else:
                print(f"⚠️ Cámara {i}: Abierta pero sin frames")
            cap.release()
        else:
            print(f"❌ Cámara {i}: No se pudo abrir")
    camaras_disponibles = camaras
    print(f"✅ Cámaras detectadas: {len(camaras_disponibles)} -> {camaras_disponibles}")
    return camaras_disponibles

def obtener_camaras_disponibles():
    """Devuelve la lista actual de cámaras disponibles"""
    return camaras_disponibles  # ← Siempre devuelve la variable global

def abrir_camaras(indices):
    global camaras_activas
    cerrar_todas_camaras()
    print(f"🔓 Intentando abrir cámaras: {indices}")
    for idx in indices:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                camaras_activas[idx] = cap
                print(f"✅ Cámara {idx} abierta y funcionando")
            else:
                print(f"⚠️ Cámara {idx} abierta pero no devuelve frames")
                cap.release()
        else:
            print(f"❌ No se pudo abrir cámara {idx}")
    print(f"📊 Cámaras activas: {list(camaras_activas.keys())}")

def cerrar_todas_camaras():
    global camaras_activas
    for idx, cap in camaras_activas.items():
        try:
            cap.release()
            print(f"🔒 Cámara {idx} cerrada")
        except Exception as e:
            print(f"⚠️ Error al cerrar cámara {idx}: {e}")
    camaras_activas.clear()