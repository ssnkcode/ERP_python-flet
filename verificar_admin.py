import sqlite3
import hashlib

conn = sqlite3.connect("erp_universal.db")
cursor = conn.cursor()

# Ver todos los usuarios
cursor.execute("SELECT id, nombre, usuario, password FROM usuarios")
print("USUARIOS EN BD:")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Nombre: {row[1]}, Usuario: {row[2]}, Password: {row[3]}")

# Hashear admin123
hash_correcto = hashlib.sha256("admin123".encode()).hexdigest()
print(f"\nHash de 'admin123': {hash_correcto}")

# Forzar actualización
cursor.execute("UPDATE usuarios SET password = ? WHERE usuario = 'admin'", (hash_correcto,))
conn.commit()

# Verificar que quedó bien
cursor.execute("SELECT password FROM usuarios WHERE usuario = 'admin'")
password_bd = cursor.fetchone()[0]

print(f"\nPassword en BD después de actualizar: {password_bd}")
print(f"Coincide con admin123: {password_bd == hash_correcto}")

conn.close()