"""
Alta de usuarios con hash bcrypt.

  python crear_usuario.py recepcion ana@club.com          (pide el PIN)
  python crear_usuario.py comision cristian@club.com      (pide la contrasena)
  python crear_usuario.py socio 30123456 --socio-id <uuid> (pide la contrasena)
"""
import argparse
import getpass

import db

p = argparse.ArgumentParser()
p.add_argument("rol", choices=["recepcion", "comision", "socio", "admin"])
p.add_argument("identificador", help="email (recepcion/comision/admin) o DNI (socio)")
p.add_argument("--socio-id", help="uuid del socio (obligatorio para rol socio)")
a = p.parse_args()

if a.rol == "socio" and not a.socio_id:
    p.error("el rol socio requiere --socio-id")

clave = getpass.getpass("PIN: " if a.rol == "recepcion" else "Contrasena: ")
if not clave or clave != getpass.getpass("Repetir: "):
    raise SystemExit("Vacio o no coincide")

u = db.crear_usuario(a.rol, a.identificador, clave, a.socio_id)
print("Usuario creado:", u["id"])
