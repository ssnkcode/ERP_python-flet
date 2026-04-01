"""
ConfiguracionHardware.py - Gestión de lectores, impresoras térmicas y fiscales
"""

import flet as ft
import os
import platform
import subprocess
import json
from datetime import datetime

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

class HardwareManager:
    """Gestor de hardware para lectores, impresoras térmicas y fiscales"""
    
    def __init__(self, page=None):
        self.page = page
        self.config = self.load_config()
        self.printer_connected = False
        self.scanner_connected = False
        self.fiscal_printer_connected = False
        
    def load_config(self):
        """Cargar configuración de hardware"""
        config_file = "hardware_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'thermal_printer': {'name': '', 'port': '', 'enabled': False},
            'fiscal_printer': {'name': '', 'port': '', 'enabled': False},
            'barcode_scanner': {'port': '', 'enabled': False},
            'last_configured': None
        }
    
    def save_config(self):
        """Guardar configuración de hardware"""
        self.config['last_configured'] = datetime.now().isoformat()
        try:
            with open('hardware_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except:
            return False
    
    def detect_printers(self):
        """Detectar impresoras disponibles en el sistema"""
        printers = []
        system = platform.system()
        
        try:
            if system == "Windows":
                result = subprocess.run(['wmic', 'printer', 'get', 'name'], 
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]
                    printers = [line.strip() for line in lines if line.strip()]
            elif system == "Linux":
                result = subprocess.run(['lpstat', '-e'], capture_output=True, text=True)
                if result.returncode == 0:
                    printers = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            elif system == "Darwin":  # macOS
                result = subprocess.run(['lpstat', '-e'], capture_output=True, text=True)
                if result.returncode == 0:
                    printers = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        except:
            printers = ["Impresora Predeterminada", "Impresora Térmica", "Impresora Fiscal"]
        
        return printers if printers else ["Impresora Predeterminada"]
    
    def test_printer(self, printer_name, test_text="Test de impresión\nERP Universal\n" + datetime.now().strftime("%d/%m/%Y %H:%M:%S")):
        """Probar impresora térmica"""
        try:
            if platform.system() == "Windows":
                subprocess.run(['print', '/D:' + printer_name, test_text], 
                             capture_output=True, text=True, shell=True)
            else:
                subprocess.run(['lp', '-d', printer_name], 
                             input=test_text, text=True, capture_output=True)
            return True
        except:
            return False
    
    def print_ticket(self, printer_name, data):
        """Imprimir ticket de venta"""
        try:
            ticket = "\n" + "="*32 + "\n"
            ticket += "ERP Universal\n"
            ticket += "="*32 + "\n"
            ticket += f"Fecha: {data.get('fecha', datetime.now().strftime('%d/%m/%Y %H:%M'))}\n"
            ticket += f"Venta N°: {data.get('numero', 'N/A')}\n"
            ticket += "-"*32 + "\n"
            
            for item in data.get('items', []):
                ticket += f"{item['nombre'][:20]}\n"
                ticket += f"  {item['cantidad']} x ${item['precio']:,.0f} = ${item['subtotal']:,.0f}\n"
            
            ticket += "-"*32 + "\n"
            ticket += f"TOTAL: ${data.get('total', 0):,.0f}\n"
            ticket += "="*32 + "\n"
            ticket += "¡Gracias por su compra!\n"
            ticket += "="*32 + "\n\n"
            
            return self.test_printer(printer_name, ticket)
        except:
            return False
    
    def print_fiscal_ticket(self, fiscal_printer, data):
        """Imprimir ticket fiscal"""
        try:
            ticket = "\n" + "F"*32 + "\n"
            ticket += "COMPROBANTE FISCAL\n"
            ticket += "F"*32 + "\n"
            ticket += f"Fecha: {data.get('fecha', datetime.now().strftime('%d/%m/%Y %H:%M'))}\n"
            ticket += f"CAI: {data.get('cai', 'N/A')}\n"
            ticket += f"Punto Venta: {data.get('punto_venta', '001')}\n"
            ticket += f"Comprobante N°: {data.get('numero', 'N/A')}\n"
            ticket += "-"*32 + "\n"
            
            for item in data.get('items', []):
                ticket += f"{item['nombre'][:20]}\n"
                ticket += f"  {item['cantidad']} x ${item['precio']:,.0f} = ${item['subtotal']:,.0f}\n"
            
            ticket += "-"*32 + "\n"
            ticket += f"SUBTOTAL: ${data.get('subtotal', 0):,.0f}\n"
            ticket += f"IVA: ${data.get('iva', 0):,.0f}\n"
            ticket += f"TOTAL: ${data.get('total', 0):,.0f}\n"
            ticket += "F"*32 + "\n\n"
            
            return self.test_printer(fiscal_printer, ticket)
        except:
            return False
    
    def read_barcode(self):
        """Leer código de barras (simulado)"""
        # En implementación real, esto conectaría con el lector USB
        return None
    
    def hardware_config_page(self):
        """Crear página de configuración de hardware"""
        printers = self.detect_printers()
        
        thermal_printer_dropdown = ft.Dropdown(
            label="Impresora Térmica",
            options=[ft.dropdown.Option(p, p) for p in printers],
            value=self.config['thermal_printer']['name'] if self.config['thermal_printer']['name'] in printers else None
        )
        
        fiscal_printer_dropdown = ft.Dropdown(
            label="Impresora Fiscal",
            options=[ft.dropdown.Option(p, p) for p in printers],
            value=self.config['fiscal_printer']['name'] if self.config['fiscal_printer']['name'] in printers else None
        )
        
        thermal_enabled = ft.Switch(
            label="Habilitar Impresora Térmica",
            value=self.config['thermal_printer']['enabled']
        )
        
        fiscal_enabled = ft.Switch(
            label="Habilitar Impresora Fiscal",
            value=self.config['fiscal_printer']['enabled']
        )
        
        scanner_enabled = ft.Switch(
            label="Habilitar Lector de Códigos",
            value=self.config['barcode_scanner']['enabled']
        )
        
        status_text = ft.Text("Estado del Hardware:", size=14, weight=ft.FontWeight.BOLD)
        status_indicators = ft.Column([])
        
        def update_status():
            status_indicators.controls.clear()
            status_indicators.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.PRINT, color=COLORS['success'] if thermal_enabled.value else COLORS['danger']),
                    ft.Text("Impresora Térmica: " + ("Conectada" if thermal_enabled.value else "Desconectada"))
                ])
            )
            status_indicators.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.RECEIPT, color=COLORS['success'] if fiscal_enabled.value else COLORS['danger']),
                    ft.Text("Impresora Fiscal: " + ("Conectada" if fiscal_enabled.value else "Desconectada"))
                ])
            )
            status_indicators.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.QR_CODE, color=COLORS['success'] if scanner_enabled.value else COLORS['danger']),
                    ft.Text("Lector Códigos: " + ("Activo" if scanner_enabled.value else "Inactivo"))
                ])
            )
        
        def save_config(e):
            self.config['thermal_printer']['name'] = thermal_printer_dropdown.value
            self.config['thermal_printer']['enabled'] = thermal_enabled.value
            self.config['fiscal_printer']['name'] = fiscal_printer_dropdown.value
            self.config['fiscal_printer']['enabled'] = fiscal_enabled.value
            self.config['barcode_scanner']['enabled'] = scanner_enabled.value
            
            if self.save_config():
                update_status()
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Configuración de hardware guardada"),
                        bgcolor=COLORS['success']
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
        
        def test_thermal(e):
            if thermal_enabled.value and thermal_printer_dropdown.value:
                if self.test_printer(thermal_printer_dropdown.value):
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Prueba de impresión térmica exitosa"),
                        bgcolor=COLORS['success']
                    )
                else:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Error en prueba de impresión térmica"),
                        bgcolor=COLORS['danger']
                    )
                self.page.snack_bar.open = True
                self.page.update()
        
        def test_fiscal(e):
            if fiscal_enabled.value and fiscal_printer_dropdown.value:
                if self.test_printer(fiscal_printer_dropdown.value):
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Prueba de impresión fiscal exitosa"),
                        bgcolor=COLORS['success']
                    )
                else:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Error en prueba de impresión fiscal"),
                        bgcolor=COLORS['danger']
                    )
                self.page.snack_bar.open = True
                self.page.update()
        
        update_status()
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Configuración de Hardware", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Text("Impresoras", size=18, weight=ft.FontWeight.BOLD),
                    thermal_printer_dropdown,
                    thermal_enabled,
                    ft.ElevatedButton(
                        "Probar Impresora Térmica",
                        on_click=test_thermal,
                        bgcolor=COLORS['accent'],
                        color=ft.Colors.WHITE
                    ),
                    ft.Divider(height=10),
                    fiscal_printer_dropdown,
                    fiscal_enabled,
                    ft.ElevatedButton(
                        "Probar Impresora Fiscal",
                        on_click=test_fiscal,
                        bgcolor=COLORS['accent'],
                        color=ft.Colors.WHITE
                    ),
                    ft.Divider(height=10),
                    ft.Text("Lectores", size=18, weight=ft.FontWeight.BOLD),
                    scanner_enabled,
                    ft.Divider(height=20),
                    status_text,
                    status_indicators,
                    ft.Divider(height=20),
                    ft.ElevatedButton(
                        "Guardar Configuración",
                        on_click=save_config,
                        bgcolor=COLORS['success'],
                        color=ft.Colors.WHITE
                    )
                ],
                spacing=15,
                expand=True,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True,
            bgcolor=COLORS['background']
        )