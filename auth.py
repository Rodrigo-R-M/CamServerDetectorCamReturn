from api_client import login, check_auth, save_cookies, clear_session
from config import DIRECCION_IP

def verificar_login(usuario, contrasena):
    usuario_server = usuario + "_server"
    resp = login(usuario_server, contrasena)
    if resp.status_code == 200:
        check = check_auth()
        if check.status_code == 200:
            save_cookies()
            return check.json()["user"]
    return None

def verificar_sesion_guardada():
    try:
        resp = check_auth()
        if resp.status_code == 200:
            return resp.json()["user"]
    except:
        pass
    return None

def cerrar_sesion_completa():
    from api_client import logout
    logout()
    clear_session()