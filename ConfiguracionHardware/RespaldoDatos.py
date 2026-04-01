"""
RespaldoDatos.py - Backups automáticos y sincronización en la nube
"""

import flet as ft
import os
import shutil
import json
import zipfile
from datetime import datetime, timedelta
import threading
import time

# ==================== COLORES GLOBALES ====================
COLORS = {
    'primary': '#0f172a',
    'secondary': '#1e293b',
    'accent': '#3b82f6',
    'success': '#22c55e',
    'danger': '#ef4444',
    'warning': '#f59e0b',
    'background': '#f8fafc',
    'text': '#0f172a',
    'text_secondary': '#64748b'
}

class BackupManager:
    """Gestor de respaldos automáticos"""
    
    def __init__(self, db_path="database.db", page=None):
        self.db_path = db_path
        self.backup_folder = "backups"
        self.config_file = "backup_config.json"
        self.config = self.load_config()
        self.backup_thread = None
        self.running = False
        self.page = page
        
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)
    
    def set_page(self, page):
        """Establecer referencia a la página"""
        self.page = page
    
    def load_config(self):
        """Cargar configuración de backups"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'auto_backup': True,
            'backup_interval': 24,
            'keep_backups': 30,
            'last_backup': None,
            'cloud_sync': False,
            'cloud_type': None,
            'cloud_folder': None
        }
    
    def save_config(self):
        """Guardar configuración de backups"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except:
            return False
    
    def create_backup(self, name=None):
        """Crear un respaldo de la base de datos"""
        if not name:
            name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.backup_folder, f"{name}.db")
        
        try:
            # Verificar si existe la base de datos
            if not os.path.exists(self.db_path):
                return False, "Base de datos no encontrada"
            
            # Copiar base de datos
            shutil.copy2(self.db_path, backup_path)
            
            # Crear archivo de metadatos
            metadata = {
                'name': name,
                'date': datetime.now().isoformat(),
                'source': self.db_path,
                'size': os.path.getsize(backup_path)
            }
            
            with open(os.path.join(self.backup_folder, f"{name}.json"), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Crear zip
            zip_path = os.path.join(self.backup_folder, f"{name}.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(backup_path, f"{name}.db")
                zipf.write(os.path.join(self.backup_folder, f"{name}.json"), f"{name}.json")
            
            # Eliminar archivos temporales
            os.remove(backup_path)
            os.remove(os.path.join(self.backup_folder, f"{name}.json"))
            
            self.config['last_backup'] = datetime.now().isoformat()
            self.save_config()
            
            self.clean_old_backups()
            
            return True, zip_path
        except Exception as e:
            return False, str(e)
    
    def clean_old_backups(self):
        """Limpiar backups antiguos"""
        keep_days = self.config.get('keep_backups', 30)
        cutoff = datetime.now() - timedelta(days=keep_days)
        
        for file in os.listdir(self.backup_folder):
            if file.endswith('.zip'):
                file_path = os.path.join(self.backup_folder, file)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                if file_time < cutoff:
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    def restore_backup(self, backup_path):
        """Restaurar un respaldo"""
        if not os.path.exists(backup_path):
            return False, "Archivo no encontrado"
        
        try:
            # Crear backup del estado actual antes de restaurar
            self.create_backup("before_restore")
            
            # Extraer zip
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(self.backup_folder)
            
            # Obtener nombre del backup
            base_name = os.path.splitext(os.path.basename(backup_path))[0]
            db_file = os.path.join(self.backup_folder, f"{base_name}.db")
            
            # Restaurar
            shutil.copy2(db_file, self.db_path)
            
            # Limpiar archivos extraídos
            os.remove(db_file)
            json_file = os.path.join(self.backup_folder, f"{base_name}.json")
            if os.path.exists(json_file):
                os.remove(json_file)
            
            return True, "Base de datos restaurada exitosamente"
        except Exception as e:
            return False, str(e)
    
    def get_backups_list(self):
        """Obtener lista de backups disponibles"""
        backups = []
        
        for file in os.listdir(self.backup_folder):
            if file.endswith('.zip'):
                file_path = os.path.join(self.backup_folder, file)
                stat = os.stat(file_path)
                
                backups.append({
                    'name': file.replace('.zip', ''),
                    'path': file_path,
                    'date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'size': stat.st_size
                })
        
        return sorted(backups, key=lambda x: x['date'], reverse=True)
    
    def start_auto_backup(self):
        """Iniciar thread de backup automático"""
        if self.backup_thread and self.backup_thread.is_alive():
            return
        
        self.running = True
        self.backup_thread = threading.Thread(target=self._auto_backup_worker, daemon=True)
        self.backup_thread.start()
    
    def stop_auto_backup(self):
        """Detener thread de backup automático"""
        self.running = False
    
    def _auto_backup_worker(self):
        """Worker para backups automáticos"""
        while self.running and self.config.get('auto_backup', False):
            interval = self.config.get('backup_interval', 24)
            
            if self.config.get('last_backup'):
                try:
                    last = datetime.fromisoformat(self.config['last_backup'])
                    next_backup = last + timedelta(hours=interval)
                    
                    if datetime.now() >= next_backup:
                        self.create_backup()
                except:
                    self.create_backup()
            else:
                self.create_backup()
            
            time.sleep(3600)
    
    def backup_config_page(self):
        """Crear página de configuración de backups"""
        auto_backup_switch = ft.Switch(
            label="Backup Automático",
            value=self.config.get('auto_backup', True)
        )
        
        backup_interval = ft.Dropdown(
            label="Intervalo de Backup (horas)",
            options=[
                ft.dropdown.Option("12", "12 horas"),
                ft.dropdown.Option("24", "24 horas"),
                ft.dropdown.Option("48", "48 horas"),
                ft.dropdown.Option("168", "7 días")
            ],
            value=str(self.config.get('backup_interval', 24))
        )
        
        keep_backups = ft.Dropdown(
            label="Mantener Backups (días)",
            options=[
                ft.dropdown.Option("7", "7 días"),
                ft.dropdown.Option("15", "15 días"),
                ft.dropdown.Option("30", "30 días"),
                ft.dropdown.Option("60", "60 días"),
                ft.dropdown.Option("90", "90 días")
            ],
            value=str(self.config.get('keep_backups', 30))
        )
        
        backups_list = ft.Column([])
        
        def refresh_backups():
            backups_list.controls.clear()
            backups = self.get_backups_list()
            
            for backup in backups[:10]:
                try:
                    date = datetime.fromisoformat(backup['date']).strftime('%d/%m/%Y %H:%M:%S')
                except:
                    date = backup['date']
                size = f"{backup['size'] / 1024:.2f} KB"
                
                backups_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.ARCHIVE, color=COLORS['accent']),
                                ft.Text(backup['name'], expand=True),
                                ft.Text(date, size=12),
                                ft.Text(size, size=12),
                                ft.IconButton(
                                    ft.Icons.RESTORE,
                                    tooltip="Restaurar",
                                    on_click=lambda e, b=backup: self.show_restore_dialog(e, b, refresh_backups)
                                ),
                                ft.IconButton(
                                    ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, b=backup: self.show_delete_dialog(e, b, refresh_backups)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                        border_radius=5,
                        margin=5
                    )
                )
        
        def save_config(e):
            self.config['auto_backup'] = auto_backup_switch.value
            self.config['backup_interval'] = int(backup_interval.value)
            self.config['keep_backups'] = int(keep_backups.value)
            
            if self.save_config():
                if self.config['auto_backup']:
                    self.start_auto_backup()
                else:
                    self.stop_auto_backup()
                
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Configuración de backups guardada"),
                        bgcolor=COLORS['success']
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
        
        def create_now(e):
            success, result = self.create_backup()
            if success:
                refresh_backups()
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Backup creado: {os.path.basename(result)}"),
                        bgcolor=COLORS['success']
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            else:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Error al crear backup: {result}"),
                        bgcolor=COLORS['danger']
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
        
        refresh_backups()
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Gestión de Respaldo de Datos", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Text("Configuración Automática", size=18, weight=ft.FontWeight.BOLD),
                    auto_backup_switch,
                    backup_interval,
                    keep_backups,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Crear Backup Ahora",
                                on_click=create_now,
                                bgcolor=COLORS['success'],
                                color=ft.Colors.WHITE,
                                icon=ft.Icons.BACKUP
                            ),
                            ft.ElevatedButton(
                                "Guardar Configuración",
                                on_click=save_config,
                                bgcolor=COLORS['accent'],
                                color=ft.Colors.WHITE
                            )
                        ],
                        spacing=10
                    ),
                    ft.Divider(height=20),
                    ft.Text("Backups Disponibles", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(backups_list, expand=True, height=400)
                ],
                spacing=15,
                expand=True,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True,
            bgcolor=COLORS['background']
        )
    
    def show_restore_dialog(self, e, backup, refresh_callback):
        """Mostrar diálogo de confirmación para restaurar"""
        def confirm_restore(confirm_e):
            success, msg = self.restore_backup(backup['path'])
            if success:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(msg),
                        bgcolor=COLORS['success']
                    )
                    self.page.snack_bar.open = True
                    refresh_callback()
                    self.page.update()
            else:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Error: {msg}"),
                        bgcolor=COLORS['danger']
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            dialog.open = False
            if self.page:
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Restauración"),
            content=ft.Text(f"¿Restaurar backup {backup['name']}?\nSe perderán los datos actuales."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda de: self.close_dialog(de, dialog)),
                ft.ElevatedButton("Restaurar", bgcolor=COLORS['danger'], on_click=confirm_restore)
            ]
        )
        
        if self.page:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def show_delete_dialog(self, e, backup, refresh_callback):
        """Mostrar diálogo de confirmación para eliminar"""
        def confirm_delete(confirm_e):
            try:
                os.remove(backup['path'])
                refresh_callback()
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Backup {backup['name']} eliminado"),
                        bgcolor=COLORS['success']
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            except Exception as ex:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Error al eliminar backup: {str(ex)}"),
                        bgcolor=COLORS['danger']
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            dialog.open = False
            if self.page:
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Eliminar backup {backup['name']}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda de: self.close_dialog(de, dialog)),
                ft.ElevatedButton("Eliminar", bgcolor=COLORS['danger'], on_click=confirm_delete)
            ]
        )
        
        if self.page:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
    
    def close_dialog(self, e, dialog):
        """Cerrar diálogo"""
        dialog.open = False
        if self.page:
            self.page.update()