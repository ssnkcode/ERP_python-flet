"""
SeguridadAccesos.py - Gestión de login y niveles de permisos
"""

import flet as ft
import hashlib
from BaseDatos import db

class SecurityManager:
    """Gestor de seguridad y permisos"""
    
    ROLES = {
        'admin': {
            'name': 'Administrador',
            'permissions': ['all'],
            'level': 100
        },
        'supervisor': {
            'name': 'Supervisor',
            'permissions': ['ventas', 'inventario', 'clientes', 'reportes', 'config_usuarios'],
            'level': 80
        },
        'vendedor': {
            'name': 'Vendedor',
            'permissions': ['ventas', 'clientes'],
            'level': 50
        },
        'cajero': {
            'name': 'Cajero',
            'permissions': ['ventas'],
            'level': 30
        }
    }
    
    def __init__(self, app=None):
        self.app = app
        self.current_user = None
    
    def authenticate(self, username, password):
        """Autenticar usuario"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user = db.get_by("usuarios", "usuario", username)
        
        if user and user['password'] == hashed_password and int(user.get('activo', 0)) == 1:
            self.current_user = user
            return True, user
        return False, None
    
    def has_permission(self, permission, user=None):
        """Verificar si el usuario tiene permiso"""
        user = user or self.current_user
        if not user:
            return False
        
        role = user.get('rol', 'vendedor')
        role_config = self.ROLES.get(role, self.ROLES['vendedor'])
        
        if 'all' in role_config['permissions']:
            return True
        
        return permission in role_config['permissions']
    
    def get_user_menu(self):
        """Obtener menú según permisos del usuario"""
        menu_items = [
            {"icon": ft.Icons.DASHBOARD, "label": "Dashboard", "page": None, "permission": "all"},
            {"icon": ft.Icons.SHOPPING_CART, "label": "Ventas", "page": "ventas", "permission": "ventas"},
            {"icon": ft.Icons.INVENTORY, "label": "Inventario", "page": "inventario", "permission": "inventario"},
            {"icon": ft.Icons.PEOPLE, "label": "Clientes", "page": "clientes", "permission": "clientes"},
            {"icon": ft.Icons.TRENDING_UP, "label": "Reportes", "page": "reportes", "permission": "reportes"},
            {"icon": ft.Icons.SETTINGS, "label": "Configuración", "page": "config", "permission": "config_usuarios"}
        ]
        
        filtered_menu = []
        for item in menu_items:
            if self.has_permission(item['permission']):
                filtered_menu.append(item)
        
        return filtered_menu
    
    def create_user(self, nombre, usuario, password, rol, activo=1):
        """Crear nuevo usuario"""
        hashed = hashlib.sha256(password.encode()).hexdigest()
        
        user_id = db.insert("usuarios", {
            'nombre': nombre,
            'usuario': usuario,
            'password': hashed,
            'rol': rol,
            'activo': activo
        })
        
        return user_id
    
    def update_user(self, user_id, data):
        """Actualizar usuario"""
        if 'password' in data and data['password']:
            data['password'] = hashlib.sha256(data['password'].encode()).hexdigest()
        
        return db.update("usuarios", data, f"id = {user_id}")
    
    def deactivate_user(self, user_id):
        """Desactivar usuario"""
        return db.update("usuarios", {'activo': 0}, f"id = {user_id}")
    
    def activate_user(self, user_id):
        """Activar usuario"""
        return db.update("usuarios", {'activo': 1}, f"id = {user_id}")
    
    def get_all_users(self):
        """Obtener todos los usuarios"""
        return db.query("SELECT id, nombre, usuario, rol, activo FROM usuarios ORDER BY id")
    
    def change_password(self, user_id, old_password, new_password):
        """Cambiar contraseña"""
        user = db.get_by_id("usuarios", user_id)
        if not user:
            return False
        
        old_hashed = hashlib.sha256(old_password.encode()).hexdigest()
        if user['password'] != old_hashed:
            return False
        
        new_hashed = hashlib.sha256(new_password.encode()).hexdigest()
        return db.update("usuarios", {'password': new_hashed}, f"id = {user_id}")
    
    def get_rol_info(self, rol):
        """Obtener información de un rol"""
        return self.ROLES.get(rol, self.ROLES['vendedor'])
    
    def get_available_roles(self):
        """Obtener lista de roles disponibles"""
        return [(key, value['name']) for key, value in self.ROLES.items()]