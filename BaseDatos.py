"""
BaseDatos.py - Motor SQLite optimizado
Singleton pattern, connection pooling manual, queries preparadas
"""

import sqlite3
import threading
import json
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

class Database:
    """
    Clase singleton para manejo de base de datos.
    Implementa thread-safe, conexiones bajo demanda y queries optimizadas.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "erp_universal.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = "erp_universal.db"):
        if self._initialized:
            return
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()
        self._initialized = True
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene conexión thread-safe"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=20,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            self._local.connection.row_factory = sqlite3.Row
            # Optimizaciones críticas
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            self._local.connection.execute("PRAGMA synchronous = NORMAL")
            self._local.connection.execute("PRAGMA cache_size = 10000")
            self._local.connection.execute("PRAGMA temp_store = MEMORY")
        return self._local.connection
    
    @contextmanager
    def cursor(self):
        """Context manager para queries seguras"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    def _init_database(self):
        """Inicializa todas las tablas con estructura optimizada"""
        with self.cursor() as cur:
            # Tabla de usuarios
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    usuario TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL CHECK(rol IN ('admin', 'supervisor', 'vendedor', 'cajero')),
                    activo INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de productos con JSON para listas de precios
            cur.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    rubro TEXT,
                    marca TEXT,
                    costo REAL DEFAULT 0,
                    precio_listas TEXT NOT NULL DEFAULT '{}',
                    stock REAL DEFAULT 0,
                    unidad TEXT DEFAULT 'unidad',
                    foto BLOB,
                    activo INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de clientes
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento TEXT UNIQUE,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT,
                    saldo REAL DEFAULT 0,
                    limite_credito REAL DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de ventas (cabecera)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cliente_id INTEGER REFERENCES clientes(id),
                    usuario_id INTEGER REFERENCES usuarios(id),
                    subtotal REAL DEFAULT 0,
                    descuento REAL DEFAULT 0,
                    total REAL DEFAULT 0,
                    metodo_pago TEXT,
                    estado TEXT DEFAULT 'completada'
                )
            """)
            
            # Tabla de detalle de ventas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ventas_detalle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad REAL NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            """)
            
            # Tabla de proveedores
            cur.execute("""
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cuit TEXT UNIQUE,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT,
                    saldo REAL DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de compras
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    proveedor_id INTEGER REFERENCES proveedores(id),
                    usuario_id INTEGER REFERENCES usuarios(id),
                    total REAL DEFAULT 0,
                    estado TEXT DEFAULT 'pendiente'
                )
            """)
            
            # Tabla de gastos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    concepto TEXT NOT NULL,
                    categoria TEXT,
                    monto REAL NOT NULL,
                    usuario_id INTEGER REFERENCES usuarios(id),
                    comprobante TEXT
                )
            """)
            
            # Tabla de cuentas corrientes
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cuentas_corrientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cliente_id INTEGER REFERENCES clientes(id),
                    tipo TEXT CHECK(tipo IN ('debito', 'credito')),
                    concepto TEXT,
                    monto REAL NOT NULL,
                    saldo_despues REAL NOT NULL,
                    venta_id INTEGER REFERENCES ventas(id)
                )
            """)
            
            # Crear índices después de las tablas
            cur.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_usuario_activo ON usuarios(usuario, activo)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_codigo_activo ON productos(codigo, activo)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_rubro ON productos(rubro)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_documento ON clientes(documento)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas(estado)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_detalle_venta_producto ON ventas_detalle(venta_id, producto_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras(fecha)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cuentas_corrientes_cliente_fecha ON cuentas_corrientes(cliente_id, fecha)")
            
            # Crear triggers para actualizar timestamps
            cur.execute("""
                CREATE TRIGGER IF NOT EXISTS update_productos_timestamp 
                AFTER UPDATE ON productos
                BEGIN
                    UPDATE productos SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            """)
            
            # Usuario admin por defecto (password: admin123)
            cur.execute("""
                INSERT OR IGNORE INTO usuarios (nombre, usuario, password, rol)
                VALUES ('Administrador', 'admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin')
            """)
    
    # ============ MÉTODOS CRUD GENÉRICOS (POTENTES) ============
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Inserta un registro y retorna el ID"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.cursor() as cur:
            cur.execute(query, list(data.values()))
            return cur.lastrowid
    
    def update(self, table: str, id: int, data: Dict[str, Any]) -> bool:
        """Actualiza un registro por ID"""
        if not data:
            return False
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        
        with self.cursor() as cur:
            cur.execute(query, list(data.values()) + [id])
            return cur.rowcount > 0
    
    def get(self, table: str, id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un registro por ID"""
        with self.cursor() as cur:
            cur.execute(f"SELECT * FROM {table} WHERE id = ?", (id,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    def get_by(self, table: str, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Obtiene un registro por campo exacto"""
        with self.cursor() as cur:
            cur.execute(f"SELECT * FROM {table} WHERE {field} = ? LIMIT 1", (value,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Query directa con parámetros (potente y segura)"""
        with self.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    
    def execute(self, sql: str, params: tuple = ()) -> int:
        """Ejecuta SQL y retorna filas afectadas"""
        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount
    
    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """Inserción masiva optimizada"""
        if not data_list:
            return 0
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['?' for _ in data_list[0]])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.cursor() as cur:
            values_list = [list(data.values()) for data in data_list]
            cur.executemany(query, values_list)
            return len(values_list)


# Instancia global
db = Database()