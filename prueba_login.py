import hashlib
from BaseDatos import db

# Probar login
usuario = "admin"
password = "admin123"
hashed = hashlib.sha256(password.encode()).hexdigest()

user = db.get_by("usuarios", "usuario", usuario)
print(f"Usuario encontrado: {user}")
print(f"Hash ingresado: {hashed}")
print(f"Hash en BD: {user['password'] if user else 'None'}")
print(f"Coinciden: {user['password'] == hashed if user else False}")