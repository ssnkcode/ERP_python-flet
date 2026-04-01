"""
MainFletApp.py - Interfaz Flet
Minimalista, modular, con navegación dinámica y componentes reutilizables
"""

import flet as ft
from BaseDatos import db
import hashlib
from datetime import datetime
import threading
import asyncio

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

# ==================== COMPONENTES REUTILIZABLES ====================

class Card(ft.Container):
    """Tarjeta estilizada reutilizable"""
    def __init__(self, content, padding=20, **kwargs):
        super().__init__(
            content=content,
            padding=padding,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
            ),
            **kwargs
        )

class DataTable(ft.DataTable):
    """Tabla de datos optimizada con paginación integrada"""
    def __init__(self, columns, rows, **kwargs):
        super().__init__(
            columns=[ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD)) for col in columns],
            rows=[
                ft.DataRow(
                    cells=[ft.DataCell(ft.Text(str(cell))) for cell in row]
                ) for row in rows
            ],
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
            border_radius=10,
            vertical_lines=ft.BorderSide(0, ft.Colors.TRANSPARENT),
            **kwargs
        )

class InputField(ft.TextField):
    """Campo de texto estilizado"""
    def __init__(self, label, **kwargs):
        super().__init__(
            label=label,
            border_color=COLORS['text_secondary'],
            focused_border_color=COLORS['accent'],
            bgcolor=ft.Colors.WHITE,
            **kwargs
        )

# ==================== CLASE BASE CON MENÚ LATERAL ====================

class BasePageWithMenu:
    """Clase base para páginas que necesitan el menú lateral"""
    
    def __init__(self, app):
        self.app = app
        self.page = app.page
    
    def sidebar(self):
        """Menú lateral dinámico - IGUAL al de DashboardPage"""
        menu_items = [
            {"icon": ft.Icons.DASHBOARD, "label": "Dashboard", "page": None},
            {"icon": ft.Icons.SHOPPING_CART, "label": "Ventas", "page": "ventas"},
            {"icon": ft.Icons.INVENTORY, "label": "Inventario", "page": "inventario"},
            {"icon": ft.Icons.PEOPLE, "label": "Clientes", "page": "clientes"},
            {"icon": ft.Icons.TRENDING_UP, "label": "Reportes", "page": "reportes"},
            {"icon": ft.Icons.SETTINGS, "label": "Configuración", "page": "config"}
        ]
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text("ERP Universal", size=20, weight=ft.FontWeight.BOLD, color=COLORS['accent']),
                        padding=20
                    ),
                    ft.Divider(),
                    *[
                        ft.ListTile(
                            leading=ft.Icon(item["icon"], color=COLORS['text_secondary']),
                            title=ft.Text(item["label"], color=COLORS['text']),
                            on_click=lambda e, p=item["page"]: self.navigate(p)
                        ) for item in menu_items
                    ],
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ARROW_BACK, color=COLORS['accent']),
                        title=ft.Text("Volver", color=COLORS['accent']),
                        on_click=self.go_back
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.HOME, color=COLORS['accent']),
                        title=ft.Text("Inicio", color=COLORS['accent']),
                        on_click=lambda e: self.navigate(None)
                    ),
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOGOUT, color=COLORS['danger']),
                        title=ft.Text("Salir", color=COLORS['danger']),
                        on_click=self.logout
                    )
                ],
                spacing=5
            ),
            width=250,
            bgcolor=ft.Colors.WHITE,
            expand=False
        )
    
    def navigate(self, page_name):
        """Navegación dinámica - usar el historial global"""
        if page_name is None:
            DashboardPage(self.app)
        else:
            # Guardar en historial
            current = None
            if hasattr(self.app, 'dashboard_instance') and self.app.dashboard_instance:
                current = self.app.dashboard_instance.current_page
            
            if current is not None and current != page_name:
                self.app.dashboard_instance.history.append(current)
            
            self.app.dashboard_instance.current_page = page_name
            
            if page_name == "ventas":
                VentasPage(self.app)
            elif page_name == "inventario":
                InventarioPage(self.app)
            elif page_name == "clientes":
                ClientesPage(self.app)
            elif page_name == "config":
                ConfigPage(self.app)
            elif page_name == "reportes":
                ReportesPage(self.app)    
    
    def go_back(self, e):
        """Volver a la página anterior"""
        if hasattr(self.app, 'dashboard_instance') and self.app.dashboard_instance:
            dashboard = self.app.dashboard_instance
            if dashboard.history:
                last_page = dashboard.history.pop()
                dashboard.current_page = last_page
                
                if last_page == "ventas":
                    VentasPage(self.app)
                elif last_page == "inventario":
                    InventarioPage(self.app)
                elif last_page == "clientes":
                    ClientesPage(self.app)
                elif last_page == "config":
                    ConfigPage(self.app)
                elif last_page is None:
                    DashboardPage(self.app)
                elif last_page == "reportes":
                    ReportesPage(self.app)    
    
    def logout(self, e):
        LoginPage(self.app)

# ==================== PÁGINAS (Módulos) ====================

class LoginPage:
    """Página de login - punto de entrada"""
    
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.build()
    
    def build(self):
        self.page.title = "ERP Universal - Login"
        self.page.bgcolor = COLORS['background']
        self.page.window_width = 450
        self.page.window_height = 600

        self.usuario_input = InputField("Usuario", width=300, on_submit=self.login)
        self.password_input = InputField("Contraseña", password=True, width=300, on_submit=self.login, can_reveal_password=True)
        
        self.error_text = ft.Text("", color=COLORS['danger'], size=12)
        
        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.STORE, size=60, color=COLORS['accent']),
                        ft.Text("ERP Universal", size=32, weight=ft.FontWeight.BOLD, color=COLORS['primary']),
                        ft.Text("Sistema de Gestión Integral", size=14, color=COLORS['text_secondary']),
                        ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                        self.usuario_input,
                        self.password_input,
                        ft.ElevatedButton(
                            "Ingresar",
                            width=300,
                            bgcolor=COLORS['accent'],
                            color=ft.Colors.WHITE,
                            on_click=self.login
                        ),
                        self.error_text
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                ),
                expand=True
            )
        )
        self.page.update()
    
    def login(self, e):
        """Autenticación de usuario"""
        usuario = self.usuario_input.value
        password = hashlib.sha256(self.password_input.value.encode()).hexdigest()
        
        user = db.get_by("usuarios", "usuario", usuario)
        
        if user and user['password'] == password and int(user.get('activo', 0)) == 1:
            self.app.user = user
            DashboardPage(self.app)
        else:
            self.error_text.value = "Usuario o contraseña incorrectos"
            self.page.update()


class DashboardPage:
    """Dashboard principal con cards y acceso rápido"""
    
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.history = []
        self.current_page = None
        app.dashboard_instance = self
        self.build()
    
    def build(self):
        self.page.title = "ERP Universal - Dashboard"
        self.page.bgcolor = COLORS['background']
        self.page.window_width = 1400
        self.page.window_height = 800
        
        # Métricas del dashboard
        self.load_metrics()
        
        # Barra lateral y contenido principal
        self.page.clean()
        self.page.add(
            ft.Row(
                [
                    self.sidebar(),
                    ft.VerticalDivider(width=1),
                    self.main_content()
                ],
                expand=True,
                spacing=0
            )
        )
        self.page.update()
    
    def sidebar(self):
        """Menú lateral dinámico"""
        menu_items = [
            {"icon": ft.Icons.DASHBOARD, "label": "Dashboard", "page": None},
            {"icon": ft.Icons.SHOPPING_CART, "label": "Ventas", "page": "ventas"},
            {"icon": ft.Icons.INVENTORY, "label": "Inventario", "page": "inventario"},
            {"icon": ft.Icons.PEOPLE, "label": "Clientes", "page": "clientes"},
            {"icon": ft.Icons.TRENDING_UP, "label": "Reportes", "page": "reportes"},
            {"icon": ft.Icons.SETTINGS, "label": "Configuración", "page": "config"}
        ]
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text("ERP Universal", size=20, weight=ft.FontWeight.BOLD, color=COLORS['accent']),
                        padding=20
                    ),
                    ft.Divider(),
                    *[
                        ft.ListTile(
                            leading=ft.Icon(item["icon"], color=COLORS['text_secondary']),
                            title=ft.Text(item["label"], color=COLORS['text']),
                            on_click=lambda e, p=item["page"]: self.navigate(p)
                        ) for item in menu_items
                    ],
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ARROW_BACK, color=COLORS['accent']),
                        title=ft.Text("Volver", color=COLORS['accent']),
                        on_click=self.go_back
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.HOME, color=COLORS['accent']),
                        title=ft.Text("Inicio", color=COLORS['accent']),
                        on_click=lambda e: self.navigate(None)
                    ),
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOGOUT, color=COLORS['danger']),
                        title=ft.Text("Salir", color=COLORS['danger']),
                        on_click=self.logout
                    )
                ],
                spacing=5
            ),
            width=250,
            bgcolor=ft.Colors.WHITE,
            expand=False
        )
    
    def main_content(self):
        """Contenido principal del dashboard"""
        self.content_area = ft.Column(
            [
                ft.Text(f"Bienvenido, {self.app.user['nombre']}", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Panel de control y métricas", size=14, color=COLORS['text_secondary']),
                ft.Divider(height=20),
                ft.ResponsiveRow(self.metric_cards, spacing=20),
                ft.Divider(height=20),
                ft.Text("Últimas ventas", size=18, weight=ft.FontWeight.BOLD),
                self.recent_sales_table()
            ],
            spacing=10,
            expand=True
        )
        
        return ft.Container(
            content=self.content_area,
            padding=20,
            expand=True,
            bgcolor=COLORS['background']
        )
    
    def load_metrics(self):
        """Carga métricas en tiempo real"""
        metrics = db.query("""
            SELECT 
                (SELECT COUNT(*) FROM productos WHERE activo = 1) as total_productos,
                (SELECT COUNT(*) FROM clientes WHERE activo = 1) as total_clientes,
                (SELECT COALESCE(SUM(total), 0) FROM ventas WHERE date(fecha) = date('now')) as ventas_hoy,
                (SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE date(fecha) = date('now')) as gastos_hoy
        """)
        
        m = metrics[0] if metrics else {}
        
        self.metric_cards = [
            self._metric_card("Productos", str(m.get('total_productos', 0)), ft.Icons.INVENTORY, COLORS['accent']),
            self._metric_card("Clientes", str(m.get('total_clientes', 0)), ft.Icons.PEOPLE, COLORS['success']),
            self._metric_card("Ventas Hoy", f"${m.get('ventas_hoy', 0):,.0f}", ft.Icons.ATTACH_MONEY, COLORS['success']),
            self._metric_card("Gastos Hoy", f"${m.get('gastos_hoy', 0):,.0f}", ft.Icons.MONEY_OFF, COLORS['danger']),
        ]
    
    def _metric_card(self, title, value, icon, color):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([ft.Icon(icon, color=color), ft.Text(title, size=14, color=COLORS['text_secondary'])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=COLORS['primary'])
                ],
                spacing=10
            ),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            expand=True,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK))
        )
    
    def recent_sales_table(self):
        """Tabla de últimas ventas"""
        ventas = db.query("""
            SELECT v.numero, v.fecha, c.nombre as cliente, v.total
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            ORDER BY v.fecha DESC
            LIMIT 10
        """)
        
        if not ventas:
            return ft.Text("No hay ventas registradas", color=COLORS['text_secondary'])
        
        rows = [[v['numero'][:10], v['fecha'][:10], v['cliente'] or 'Consumidor Final', f"${v['total']:,.0f}"] for v in ventas]
        
        return Card(
            DataTable(
                ["N°", "Fecha", "Cliente", "Total"],
                rows
            ),
            padding=10
        )
    
    def navigate(self, page_name):
        """Navegación dinámica entre módulos"""
        if page_name is None:
            self.build()
        else:
            if self.current_page is not None and self.current_page != page_name:
                self.history.append(self.current_page)
            self.current_page = page_name
            
            if page_name == "ventas":
                VentasPage(self.app)
            elif page_name == "inventario":
                InventarioPage(self.app)
            elif page_name == "clientes":
                ClientesPage(self.app)
            elif page_name == "reportes":
                ReportesPage(self.app)
            elif page_name == "config":
                ConfigPage(self.app)
    
    def go_back(self, e):
        """Volver a la página anterior"""
        if self.history:
            last_page = self.history.pop()
            self.current_page = last_page
            
            if last_page == "ventas":
                VentasPage(self.app)
            elif last_page == "inventario":
                InventarioPage(self.app)
            elif last_page == "clientes":
                ClientesPage(self.app)
            elif last_page == "reportes":
                ReportesPage(self.app)
            elif last_page == "config":
                ConfigPage(self.app)
            elif last_page is None:
                self.build()
    
    def logout(self, e):
        LoginPage(self.app)


class VentasPage(BasePageWithMenu):
    """Módulo de ventas - punto de venta rápido"""
    
    def __init__(self, app):
        super().__init__(app)
        self.carrito = []
        self.build()
    
    def build(self):
        self.page.title = "ERP Universal - Ventas"
        self.page.bgcolor = COLORS['background']
        self.page.window_width = 1400
        self.page.window_height = 800
        
        self.page.clean()
        self.page.add(
            ft.Row(
                [
                    self.sidebar(),
                    ft.VerticalDivider(width=1),
                    self.main_content()
                ],
                expand=True,
                spacing=0
            )
        )
        self.page.update()
    
    def main_content(self):
        """Contenido principal con ventas"""
        return ft.Container(
            content=ft.Row(
                [
                    self.productos_panel(),
                    ft.VerticalDivider(width=1),
                    self.carrito_panel()
                ],
                expand=True,
                spacing=0
            ),
            expand=True,
            bgcolor=COLORS['background']
        )
    
    def productos_panel(self):
        """Panel de búsqueda y selección de productos"""
        self.busqueda = InputField("Buscar producto por código o nombre", expand=True)
        
        self.productos_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=200,
            child_aspect_ratio=1,
            spacing=10,
            run_spacing=10
        )
        
        self.busqueda.on_change = self.search_products
        self.load_products()
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Seleccionar Producto", size=20, weight=ft.FontWeight.BOLD),
                    self.busqueda,
                    ft.Text("Resultados:", size=14, weight=ft.FontWeight.BOLD),
                    self.productos_grid
                ],
                spacing=15,
                expand=True
            ),
            padding=20,
            expand=True,
            bgcolor=ft.Colors.WHITE
        )
    
    def load_products(self, search=""):
        """Carga productos con filtro"""
        if search:
            products = db.query("""
                SELECT * FROM productos 
                WHERE (codigo LIKE ? OR nombre LIKE ?) AND activo = 1
                LIMIT 20
            """, (f"%{search}%", f"%{search}%"))
        else:
            products = db.query("SELECT * FROM productos WHERE activo = 1 LIMIT 20")
        
        self.productos_grid.controls.clear()
        
        for p in products:
            precios = eval(p['precio_listas']) if p['precio_listas'] else {}
            precio = precios.get('lista1', p['costo'] * 1.3 if p['costo'] else 0)
            
            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.PRODUCTION_QUANTITY_LIMITS, size=40, color=COLORS['accent']),
                        ft.Text(p['nombre'], size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"${precio:,.0f}", size=14, color=COLORS['success'], weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Agregar",
                            bgcolor=COLORS['accent'],
                            color=ft.Colors.WHITE,
                            on_click=lambda e, prod=p, pr=precio: self.add_to_cart(prod, pr)
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8
                ),
                padding=10,
                bgcolor=COLORS['background'],
                border_radius=10,
                ink=True
            )
            self.productos_grid.controls.append(card)
        
        self.page.update()
    
    def search_products(self, e):
        self.load_products(e.control.value)
    
    def add_to_cart(self, producto, precio):
        """Agrega producto al carrito"""
        for item in self.carrito:
            if item['id'] == producto['id']:
                item['cantidad'] += 1
                item['subtotal'] = item['cantidad'] * item['precio']
                self.update_cart_display()
                return
        
        self.carrito.append({
            'id': producto['id'],
            'codigo': producto['codigo'],
            'nombre': producto['nombre'],
            'precio': precio,
            'cantidad': 1,
            'subtotal': precio
        })
        self.update_cart_display()
    
    def carrito_panel(self):
        """Panel del carrito de compras"""
        self.cart_list = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
        self.total_label = ft.Text("Total: $0", size=24, weight=ft.FontWeight.BOLD, color=COLORS['primary'])
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Carrito de Compras", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Text("Productos:", weight=ft.FontWeight.BOLD),
                    ft.Container(self.cart_list, expand=True, height=400),
                    ft.Divider(),
                    self.total_label,
                    ft.Row(
                        [
                            ft.ElevatedButton("Cancelar", bgcolor=COLORS['danger'], color=ft.Colors.WHITE, on_click=self.clear_cart),
                            ft.ElevatedButton("Finalizar Venta", bgcolor=COLORS['success'], color=ft.Colors.WHITE, on_click=self.finish_sale)
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=10
                    )
                ],
                spacing=15,
                expand=True
            ),
            padding=20,
            width=400,
            bgcolor=ft.Colors.WHITE
        )
    
    def update_cart_display(self):
        """Actualiza visualización del carrito"""
        self.cart_list.controls.clear()
        
        for i, item in enumerate(self.carrito):
            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(item['nombre'], expand=True, size=14),
                        ft.Text(f"x{item['cantidad']}", size=12),
                        ft.Text(f"${item['subtotal']:,.0f}", size=14, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            ft.Icons.DELETE,
                            icon_size=18,
                            on_click=lambda e, idx=i: self.remove_from_cart(idx)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=5
            )
            self.cart_list.controls.append(row)
        
        total = sum(item['subtotal'] for item in self.carrito)
        self.total_label.value = f"Total: ${total:,.0f}"
        self.page.update()
    
    def remove_from_cart(self, index):
        self.carrito.pop(index)
        self.update_cart_display()
    
    def clear_cart(self, e):
        self.carrito = []
        self.update_cart_display()
    
    def finish_sale(self, e):
        """Finaliza la venta y guarda en BD"""
        if not self.carrito:
            return
        
        numero = f"V{datetime.now().strftime('%Y%m%d%H%M%S')}"
        total = sum(item['subtotal'] for item in self.carrito)
        
        venta_id = db.insert("ventas", {
            'numero': numero,
            'fecha': datetime.now().isoformat(),
            'cliente_id': None,
            'usuario_id': self.app.user['id'],
            'subtotal': total,
            'descuento': 0,
            'total': total,
            'metodo_pago': 'efectivo',
            'estado': 'completada'
        })
        
        for item in self.carrito:
            db.insert("ventas_detalle", {
                'venta_id': venta_id,
                'producto_id': item['id'],
                'cantidad': item['cantidad'],
                'precio_unitario': item['precio'],
                'subtotal': item['subtotal']
            })
            
            db.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", 
                      (item['cantidad'], item['id']))
        
        self.clear_cart(None)
        
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"Venta #{numero} completada - Total: ${total:,.0f}"),
            bgcolor=COLORS['success']
        )
        self.page.snack_bar.open = True
        self.page.update()


class InventarioPage(BasePageWithMenu):
    """Módulo de gestión de inventario"""
    
    def __init__(self, app):
        super().__init__(app)
        self.build()
    
    def build(self):
        self.page.title = "ERP Universal - Inventario"
        self.page.bgcolor = COLORS['background']
        self.page.window_width = 1400
        self.page.window_height = 800
        
        self.productos = db.query("SELECT * FROM productos WHERE activo = 1 ORDER BY id DESC LIMIT 50")
        
        self.page.clean()
        self.page.add(
            ft.Row(
                [
                    self.sidebar(),
                    ft.VerticalDivider(width=1),
                    self.main_content()
                ],
                expand=True,
                spacing=0
            )
        )
        self.page.update()
    
    def main_content(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Gestión de Inventario", size=24, weight=ft.FontWeight.BOLD),
                            ft.ElevatedButton("+ Nuevo Producto", bgcolor=COLORS['accent'], color=ft.Colors.WHITE, on_click=self.show_product_form)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(),
                    Card(
                        DataTable(
                            ["ID", "Código", "Nombre", "Stock", "Precio Venta", "Estado"],
                            [[p['id'], p['codigo'], p['nombre'], p['stock'], f"${eval(p['precio_listas']).get('lista1', 0):,.0f}", "Activo"] for p in self.productos]
                        ),
                        padding=10
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
    
    def show_product_form(self, e):
        """Diálogo para crear/editar producto"""
        codigo = InputField("Código", width=200)
        nombre = InputField("Nombre", width=300)
        costo = InputField("Costo", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        precio1 = InputField("Precio Lista 1", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        stock = InputField("Stock inicial", width=150, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        
        def save(e):
            if not codigo.value or not nombre.value:
                return
            
            precios = {
                'lista1': float(precio1.value) if precio1.value else (float(costo.value) * 1.3 if costo.value else 0),
                'lista2': 0,
                'lista3': 0,
                'lista4': 0
            }
            
            db.insert("productos", {
                'codigo': codigo.value,
                'nombre': nombre.value,
                'costo': float(costo.value) if costo.value else 0,
                'precio_listas': str(precios),
                'stock': float(stock.value) if stock.value else 0,
                'unidad': 'unidad',
                'activo': 1
            })
            
            dialog.open = False
            self.build()
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Nuevo Producto"),
            content=ft.Column([codigo, nombre, costo, precio1, stock], spacing=10, width=400, height=300),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Guardar", bgcolor=COLORS['success'], on_click=save)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()


class ClientesPage(BasePageWithMenu):
    """Módulo de gestión de clientes"""
    
    def __init__(self, app):
        super().__init__(app)
        self.build()
    
    def build(self):
        self.page.title = "ERP Universal - Clientes"
        self.page.bgcolor = COLORS['background']
        self.page.window_width = 1400
        self.page.window_height = 800
        
        self.clientes = db.query("SELECT * FROM clientes WHERE activo = 1 ORDER BY id DESC LIMIT 50")
        
        self.page.clean()
        self.page.add(
            ft.Row(
                [
                    self.sidebar(),
                    ft.VerticalDivider(width=1),
                    self.main_content()
                ],
                expand=True,
                spacing=0
            )
        )
        self.page.update()
    
    def main_content(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Gestión de Clientes", size=24, weight=ft.FontWeight.BOLD),
                            ft.ElevatedButton("+ Nuevo Cliente", bgcolor=COLORS['accent'], color=ft.Colors.WHITE, on_click=self.show_client_form)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(),
                    Card(
                        DataTable(
                            ["ID", "Documento", "Nombre", "Teléfono", "Saldo", "Estado"],
                            [[c['id'], c['documento'] or '-', c['nombre'], c['telefono'] or '-', f"${c['saldo']:,.0f}", "Activo"] for c in self.clientes]
                        ),
                        padding=10
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
    
    def show_client_form(self, e):
        nombre = InputField("Nombre")
        documento = InputField("Documento")
        telefono = InputField("Teléfono")
        
        def save(e):
            db.insert("clientes", {
                'nombre': nombre.value,
                'documento': documento.value,
                'telefono': telefono.value,
                'activo': 1
            })
            dialog.open = False
            self.build()
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Nuevo Cliente"),
            content=ft.Column([nombre, documento, telefono], spacing=10, width=400),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Guardar", bgcolor=COLORS['success'], on_click=save)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()


class ConfigPage(BasePageWithMenu):
    """Módulo de configuración"""
    
    def __init__(self, app):
        super().__init__(app)
        self.build()
    
    def build(self):
        self.page.title = "ERP Universal - Configuración"
        self.page.bgcolor = COLORS['background']
        self.page.window_width = 1400
        self.page.window_height = 800
        
        self.page.clean()
        self.page.add(
            ft.Row(
                [
                    self.sidebar(),
                    ft.VerticalDivider(width=1),
                    self.main_content()
                ],
                expand=True,
                spacing=0
            )
        )
        self.page.update()
    
    def main_content(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Configuración del Sistema", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Text("Usuarios del Sistema", size=18, weight=ft.FontWeight.BOLD),
                    Card(
                        self.users_table(),
                        padding=10
                    ),
                    ft.ElevatedButton("+ Nuevo Usuario", bgcolor=COLORS['accent'], color=ft.Colors.WHITE, on_click=self.show_user_form)
                ],
                spacing=15,
                expand=True,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True,
            bgcolor=COLORS['background']
        )
    
    def users_table(self):
        usuarios = db.query("SELECT id, nombre, usuario, rol, activo FROM usuarios")
        return DataTable(
            ["ID", "Nombre", "Usuario", "Rol", "Estado"],
            [[u['id'], u['nombre'], u['usuario'], u['rol'], "Activo" if u['activo'] else "Inactivo"] for u in usuarios]
        )
    
    def show_user_form(self, e):
        nombre = InputField("Nombre completo")
        usuario = InputField("Usuario")
        password = InputField("Contraseña", password=True)
        rol = ft.Dropdown(
            label="Rol",
            options=[
                ft.dropdown.Option("admin", "Administrador"),
                ft.dropdown.Option("supervisor", "Supervisor"),
                ft.dropdown.Option("vendedor", "Vendedor"),
                ft.dropdown.Option("cajero", "Cajero")
            ],
            value="vendedor"
        )
        
        def save(e):
            if not nombre.value or not usuario.value or not password.value:
                return
            
            hashed = hashlib.sha256(password.value.encode()).hexdigest()
            
            db.insert("usuarios", {
                'nombre': nombre.value,
                'usuario': usuario.value,
                'password': hashed,
                'rol': rol.value,
                'activo': 1
            })
            
            dialog.open = False
            self.build()
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Nuevo Usuario"),
            content=ft.Column([nombre, usuario, password, rol], spacing=10, width=400),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Guardar", bgcolor=COLORS['success'], on_click=save)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()


class ReportesPage(BasePageWithMenu):
    """Módulo de reportes y estadísticas"""
    
    def __init__(self, app):
        super().__init__(app)
        self.build()
    
    def build(self):
        self.page.title = "ERP Universal - Reportes"
        self.page.bgcolor = COLORS['background']
        self.page.window_width = 1400
        self.page.window_height = 800
        
        self.page.clean()
        self.page.add(
            ft.Row(
                [
                    self.sidebar(),
                    ft.VerticalDivider(width=1),
                    self.main_content()
                ],
                expand=True,
                spacing=0
            )
        )
        self.page.update()
    
    def main_content(self):
        """Contenido principal con tabs de reportes"""
        
        # Crear los tabs de forma manual
        self.tab_ventas = ft.Container(content=self.ventas_tab(), visible=True)
        self.tab_productos = ft.Container(content=self.productos_tab(), visible=False)
        self.tab_clientes = ft.Container(content=self.clientes_tab(), visible=False)
        self.tab_rentabilidad = ft.Container(content=self.rentabilidad_tab(), visible=False)
        
        # Crear los botones de las pestañas
        tab_buttons = ft.Row(
            [
                ft.ElevatedButton(
                    "Ventas",
                    on_click=lambda e: self.switch_tab(0),
                    bgcolor=COLORS['accent'] if 0 == 0 else COLORS['text_secondary'],
                    color=ft.Colors.WHITE
                ),
                ft.ElevatedButton(
                    "Productos",
                    on_click=lambda e: self.switch_tab(1),
                    bgcolor=COLORS['accent'] if 1 == 0 else COLORS['text_secondary'],
                    color=ft.Colors.WHITE
                ),
                ft.ElevatedButton(
                    "Clientes",
                    on_click=lambda e: self.switch_tab(2),
                    bgcolor=COLORS['accent'] if 2 == 0 else COLORS['text_secondary'],
                    color=ft.Colors.WHITE
                ),
                ft.ElevatedButton(
                    "Rentabilidad",
                    on_click=lambda e: self.switch_tab(3),
                    bgcolor=COLORS['accent'] if 3 == 0 else COLORS['text_secondary'],
                    color=ft.Colors.WHITE
                ),
            ],
            spacing=10
        )
        
        self.tab_content = ft.Column(
            [
                self.tab_ventas,
                self.tab_productos,
                self.tab_clientes,
                self.tab_rentabilidad
            ],
            spacing=20,
            expand=True
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Reportes y Estadísticas", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    tab_buttons,
                    ft.Divider(height=10),
                    self.tab_content
                ],
                spacing=15,
                expand=True,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True,
            bgcolor=COLORS['background']
        )
    
    def switch_tab(self, index):
        """Cambiar entre pestañas"""
        # Ocultar todos los tabs
        self.tab_ventas.visible = (index == 0)
        self.tab_productos.visible = (index == 1)
        self.tab_clientes.visible = (index == 2)
        self.tab_rentabilidad.visible = (index == 3)
        
        # Actualizar la interfaz
        self.page.update()
    
    def ventas_tab(self):
        """Tabla de reportes de ventas"""
        # Ventas por día (últimos 7 días)
        ventas_diarias = db.query("""
            SELECT date(fecha) as dia, COUNT(*) as cantidad, SUM(total) as total
            FROM ventas
            WHERE fecha >= date('now', '-7 days')
            GROUP BY date(fecha)
            ORDER BY dia DESC
        """)
        
        # Ventas por mes (últimos 6 meses)
        ventas_mensuales = db.query("""
            SELECT strftime('%Y-%m', fecha) as mes, COUNT(*) as cantidad, SUM(total) as total
            FROM ventas
            WHERE fecha >= date('now', '-6 months')
            GROUP BY strftime('%Y-%m', fecha)
            ORDER BY mes DESC
        """)
        
        return ft.Column(
            [
                ft.Text("Ventas por Día (Últimos 7 días)", size=18, weight=ft.FontWeight.BOLD),
                Card(
                    DataTable(
                        ["Fecha", "Cantidad de Ventas", "Total"],
                        [[v['dia'], v['cantidad'], f"${v['total']:,.0f}"] for v in ventas_diarias]
                    ),
                    padding=10
                ),
                ft.Divider(height=20),
                ft.Text("Ventas por Mes (Últimos 6 meses)", size=18, weight=ft.FontWeight.BOLD),
                Card(
                    DataTable(
                        ["Mes", "Cantidad de Ventas", "Total"],
                        [[v['mes'], v['cantidad'], f"${v['total']:,.0f}"] for v in ventas_mensuales]
                    ),
                    padding=10
                ),
                ft.Divider(height=20),
                ft.ElevatedButton(
                    "Exportar a Excel",
                    icon=ft.Icons.DOWNLOAD,
                    bgcolor=COLORS['accent'],
                    color=ft.Colors.WHITE,
                    on_click=self.exportar_ventas_excel
                )
            ],
            spacing=15,
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
    
    def productos_tab(self):
        """Tabla de reportes de productos"""
        # Productos más vendidos
        mas_vendidos = db.query("""
            SELECT p.nombre, SUM(vd.cantidad) as cantidad, SUM(vd.subtotal) as total
            FROM ventas_detalle vd
            JOIN productos p ON vd.producto_id = p.id
            GROUP BY p.id
            ORDER BY cantidad DESC
            LIMIT 20
        """)
        
        # Productos con bajo stock
        bajo_stock = db.query("""
            SELECT codigo, nombre, stock
            FROM productos
            WHERE stock < 10 AND activo = 1
            ORDER BY stock ASC
            LIMIT 20
        """)
        
        return ft.Column(
            [
                ft.Text("Productos Más Vendidos", size=18, weight=ft.FontWeight.BOLD),
                Card(
                    DataTable(
                        ["Producto", "Cantidad Vendida", "Total Vendido"],
                        [[p['nombre'], p['cantidad'], f"${p['total']:,.0f}"] for p in mas_vendidos]
                    ),
                    padding=10
                ),
                ft.Divider(height=20),
                ft.Text("Productos con Stock Crítico (menos de 10 unidades)", size=18, weight=ft.FontWeight.BOLD, color=COLORS['danger']),
                Card(
                    DataTable(
                        ["Código", "Nombre", "Stock"],
                        [[p['codigo'], p['nombre'], p['stock']] for p in bajo_stock]
                    ),
                    padding=10
                ),
                ft.ElevatedButton(
                    "Exportar a Excel",
                    icon=ft.Icons.DOWNLOAD,
                    bgcolor=COLORS['accent'],
                    color=ft.Colors.WHITE,
                    on_click=self.exportar_productos_excel
                )
            ],
            spacing=15,
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
    
    def clientes_tab(self):
        """Tabla de reportes de clientes"""
        # Clientes con mayor compra
        mejores_clientes = db.query("""
            SELECT c.nombre, COUNT(v.id) as compras, SUM(v.total) as total
            FROM clientes c
            JOIN ventas v ON c.id = v.cliente_id
            WHERE c.activo = 1
            GROUP BY c.id
            ORDER BY total DESC
            LIMIT 20
        """)
        
        return ft.Column(
            [
                ft.Text("Top 20 Clientes por Volumen de Compra", size=18, weight=ft.FontWeight.BOLD),
                Card(
                    DataTable(
                        ["Cliente", "Cantidad de Compras", "Total Comprado"],
                        [[c['nombre'], c['compras'], f"${c['total']:,.0f}"] for c in mejores_clientes]
                    ),
                    padding=10
                ),
                ft.ElevatedButton(
                    "Exportar a Excel",
                    icon=ft.Icons.DOWNLOAD,
                    bgcolor=COLORS['accent'],
                    color=ft.Colors.WHITE,
                    on_click=self.exportar_clientes_excel
                )
            ],
            spacing=15,
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
    
    def rentabilidad_tab(self):
        """Tabla de reportes de rentabilidad"""
        # Rentabilidad por producto
        rentabilidad = db.query("""
            SELECT p.nombre, p.costo, p.precio_listas
            FROM productos p
            WHERE p.activo = 1 AND p.costo > 0
            LIMIT 50
        """)
        
        # Calcular rentabilidad manualmente
        datos_rentabilidad = []
        for p in rentabilidad:
            try:
                precios = eval(p['precio_listas']) if p.get('precio_listas') else {}
                precio_venta = precios.get('lista1', 0)
                costo = p.get('costo', 0)
                if costo > 0 and precio_venta > 0:
                    ganancia = precio_venta - costo
                    margen = (ganancia / precio_venta) * 100
                    datos_rentabilidad.append([p['nombre'], f"${costo:,.0f}", f"${precio_venta:,.0f}", f"${ganancia:,.0f}", f"{margen:.1f}%"])
            except:
                continue
        
        return ft.Column(
            [
                ft.Text("Rentabilidad por Producto", size=18, weight=ft.FontWeight.BOLD),
                Card(
                    DataTable(
                        ["Producto", "Costo", "Precio Venta", "Ganancia", "Margen"],
                        datos_rentabilidad[:20]
                    ),
                    padding=10
                ),
                ft.ElevatedButton(
                    "Exportar a Excel",
                    icon=ft.Icons.DOWNLOAD,
                    bgcolor=COLORS['accent'],
                    color=ft.Colors.WHITE,
                    on_click=self.exportar_rentabilidad_excel
                )
            ],
            spacing=15,
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )
    
    def exportar_ventas_excel(self, e):
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Exportando reporte de ventas a Excel..."),
            bgcolor=COLORS['success']
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def exportar_productos_excel(self, e):
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Exportando reporte de productos a Excel..."),
            bgcolor=COLORS['success']
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def exportar_clientes_excel(self, e):
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Exportando reporte de clientes a Excel..."),
            bgcolor=COLORS['success']
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def exportar_rentabilidad_excel(self, e):
        self.page.snack_bar = ft.SnackBar(
            ft.Text("Exportando reporte de rentabilidad a Excel..."),
            bgcolor=COLORS['success']
        )
        self.page.snack_bar.open = True
        self.page.update()

# ==================== APP PRINCIPAL ====================

class ERPApp:
    """Aplicación principal - Orquestador"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user = None
        self.dashboard_instance = None 
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.spacing = 0
        self.page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"
        }
        self.page.theme = ft.Theme(font_family="Roboto")
        
        LoginPage(self)


def main():
    ft.app(target=ERPApp)


if __name__ == "__main__":
    main()