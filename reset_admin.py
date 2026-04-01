import sqlite3

conn = sqlite3.connect("erp_universal.db")
cursor = conn.cursor()

# Contraseña "admin123" hasheada
cursor.execute("UPDATE usuarios SET password = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918' WHERE usuario = 'admin'")

conn.commit()
conn.close()

print("Contraseña de admin restablecida a: admin123")