"""
LicenciamientoPermanente.py - Validación de licencia única
"""

import flet as ft
import hashlib
import json
import os
import platform
import uuid
import socket
from datetime import datetime, timedelta

# ==================== COLORES GLOBALES ====================
COLORS = {
    'primary': '#0f172a',      # slate-900
    'secondary': '#1e293b',    # slate-800
    'accent': '#3b82f6',       # blue-500
    'success': '#22c55e',      # green-500
    'danger': '#ef4444',       # red-500
    'warning': '#f59e0b',      # amber-500
    'background': '#f8fafc',   # slate-50
    'text': '#0f172a',         # slate-900
    'text_secondary': '#64748b' # slate-500
}

class LicenseManager:
    """Gestor de licencias permanentes"""
    
    def __init__(self):
        self.license_file = "license.json"
        self.license_data = self.load_license()
        self.hardware_id = self.get_hardware_id()
    
    def get_hardware_id(self):
        """Obtener ID único del hardware"""
        try:
            # Combinar múltiples identificadores
            identifiers = []
            
            # MAC address
            mac = uuid.getnode()
            identifiers.append(str(mac))
            
            # Nombre del equipo
            identifiers.append(platform.node())
            
            # ID del procesador
            try:
                import wmi
                c = wmi.WMI()
                for processor in c.Win32_Processor():
                    identifiers.append(processor.ProcessorId)
            except:
                pass
            
            # ID del disco
            try:
                import psutil
                for partition in psutil.disk_partitions():
                    if 'C:' in partition.mountpoint:
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            identifiers.append(str(usage.total))
                        except:
                            pass
            except:
                pass
            
            # Crear hash único
            combined = "".join(identifiers)
            return hashlib.sha256(combined.encode()).hexdigest()
        except:
            return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()
    
    def load_license(self):
        """Cargar datos de licencia"""
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'activated': False,
            'license_key': None,
            'hardware_id': None,
            'activation_date': None,
            'expiration_date': None
        }
    
    def save_license(self):
        """Guardar datos de licencia"""
        try:
            with open(self.license_file, 'w') as f:
                json.dump(self.license_data, f, indent=2)
            return True
        except:
            return False
    
    def validate_license(self):
        """Validar licencia actual"""
        if not self.license_data.get('activated', False):
            return False, "Licencia no activada"
        
        if self.license_data.get('hardware_id') != self.hardware_id:
            return False, "Licencia válida para otro equipo"
        
        if self.license_data.get('expiration_date'):
            expiration = datetime.fromisoformat(self.license_data['expiration_date'])
            if datetime.now() > expiration:
                return False, "Licencia expirada"
        
        return True, "Licencia válida"
    
    def generate_license_key(self, hardware_id, duration_days=365):
        """Generar clave de licencia"""
        expiration = datetime.now() + timedelta(days=duration_days)
        
        # Crear datos para la licencia
        data = f"{hardware_id}|{expiration.isoformat()}"
        license_key = hashlib.sha256(data.encode()).hexdigest()
        
        return license_key, expiration
    
    def activate_license(self, license_key):
        """Activar licencia con clave proporcionada"""
        # Aquí normalmente se verificaría con un servidor
        # Para este ejemplo, verificamos localmente
        
        # Simular verificación (en producción, esto sería una API)
        expected_key = hashlib.sha256(
            f"{self.hardware_id}|{(datetime.now() + timedelta(days=365)).isoformat()}".encode()
        ).hexdigest()
        
        if license_key == expected_key:
            self.license_data = {
                'activated': True,
                'license_key': license_key,
                'hardware_id': self.hardware_id,
                'activation_date': datetime.now().isoformat(),
                'expiration_date': (datetime.now() + timedelta(days=365)).isoformat()
            }
            self.save_license()
            return True, "Licencia activada correctamente"
        
        return False, "Clave de licencia inválida"
    
    def deactivate_license(self):
        """Desactivar licencia"""
        self.license_data = {
            'activated': False,
            'license_key': None,
            'hardware_id': None,
            'activation_date': None,
            'expiration_date': None
        }
        self.save_license()
        return True, "Licencia desactivada"
    
    def get_license_info(self):
        """Obtener información de la licencia actual"""
        valid, message = self.validate_license()
        
        info = {
            'activated': self.license_data.get('activated', False),
            'valid': valid,
            'message': message,
            'hardware_id': self.hardware_id,
            'activation_date': self.license_data.get('activation_date'),
            'expiration_date': self.license_data.get('expiration_date')
        }
        
        if info['expiration_date']:
            expiration = datetime.fromisoformat(info['expiration_date'])
            info['days_left'] = (expiration - datetime.now()).days
        
        return info
    
    def license_page(self):
        """Crear página de gestión de licencia"""
        license_info = self.get_license_info()
        
        status_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE if license_info['valid'] else ft.Icons.ERROR,
            color=COLORS['success'] if license_info['valid'] else COLORS['danger'],
            size=48
        )
        
        status_text = ft.Text(
            license_info['message'],
            size=16,
            color=COLORS['success'] if license_info['valid'] else COLORS['danger']
        )
        
        hardware_id_field = ft.TextField(
            label="ID del Hardware",
            value=license_info['hardware_id'],
            read_only=True,
            width=500
        )
        
        license_key_input = ft.TextField(
            label="Clave de Licencia",
            hint_text="Ingrese la clave de activación",
            width=400
        )
        
        info_text = ft.Text("", size=12, color=COLORS['text_secondary'])
        
        if license_info['activation_date']:
            activation_date = datetime.fromisoformat(license_info['activation_date']).strftime('%d/%m/%Y %H:%M')
            info_text.value += f"Activado: {activation_date}\n"
        
        if license_info.get('expiration_date'):
            expiration_date = datetime.fromisoformat(license_info['expiration_date']).strftime('%d/%m/%Y')
            info_text.value += f"Expira: {expiration_date}\n"
        
        if license_info.get('days_left') is not None:
            info_text.value += f"Días restantes: {license_info['days_left']}"
        
        def activate_license(e):
            if not license_key_input.value:
                e.page.snack_bar = ft.SnackBar(
                    ft.Text("Ingrese una clave de licencia"),
                    bgcolor=COLORS['warning']
                )
                e.page.snack_bar.open = True
                e.page.update()
                return
            
            success, message = self.activate_license(license_key_input.value)
            
            e.page.snack_bar = ft.SnackBar(
                ft.Text(message),
                bgcolor=COLORS['success'] if success else COLORS['danger']
            )
            e.page.snack_bar.open = True
            e.page.update()
            
            if success:
                # Recargar página
                e.page.clean()
                e.page.add(self.license_page())
                e.page.update()
        
        def deactivate_license(e):
            def confirm_deactivate(confirm_e):
                success, message = self.deactivate_license()
                confirm_e.page.snack_bar = ft.SnackBar(
                    ft.Text(message),
                    bgcolor=COLORS['success'] if success else COLORS['danger']
                )
                confirm_e.page.snack_bar.open = True
                confirm_e.page.update()
                
                if success:
                    confirm_e.page.clean()
                    confirm_e.page.add(self.license_page())
                    confirm_e.page.update()
                
                dialog.open = False
                confirm_e.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Confirmar Desactivación"),
                content=ft.Text("¿Está seguro de desactivar la licencia?\nEl sistema quedará sin acceso."),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda de: setattr(dialog, 'open', False)),
                    ft.ElevatedButton("Desactivar", bgcolor=COLORS['danger'], on_click=confirm_deactivate)
                ]
            )
            e.page.dialog = dialog
            dialog.open = True
            e.page.update()
        
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Sistema de Licencias", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([status_icon, ft.Column([ft.Text("Estado de Licencia", size=18, weight=ft.FontWeight.BOLD), status_text])], spacing=20),
                    ft.Divider(height=20),
                    hardware_id_field,
                    ft.Text("Para activar, solicite una clave de licencia proporcionando el ID del hardware", size=12, color=COLORS['text_secondary']),
                    ft.Divider(height=10),
                    license_key_input,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Activar Licencia",
                                on_click=activate_license,
                                bgcolor=COLORS['success'],
                                color=ft.Colors.WHITE,
                                icon=ft.Icons.VERIFIED
                            )
                        ] + (
                            [ft.ElevatedButton(
                                "Desactivar Licencia",
                                on_click=deactivate_license,
                                bgcolor=COLORS['danger'],
                                color=ft.Colors.WHITE,
                                icon=ft.Icons.LOGOUT
                            )] if license_info['activated'] else []
                        ),
                        spacing=10
                    ),
                    ft.Divider(height=20),
                    ft.Text(info_text.value, size=12, color=COLORS['text_secondary'])
                ],
                spacing=15,
                expand=True
            ),
            padding=20,
            expand=True,
            bgcolor=COLORS['background']
        )
        
        return content