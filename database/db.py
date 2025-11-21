# database/db.py - Funciones de base de datos
import sqlite3
from config import Config

def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn


def init_db():
    """Inicializar base de datos"""
    conn = get_db_connection()
    c = conn.cursor()

    # Tabla de categorías
    c.execute('''CREATE TABLE IF NOT EXISTS categorias
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT UNIQUE NOT NULL,
                  tipo TEXT NOT NULL,
                  color TEXT DEFAULT '#6c757d',
                  icono TEXT DEFAULT 'circle')''')

    # Tabla de ingresos
    c.execute('''CREATE TABLE IF NOT EXISTS ingresos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fecha TEXT,
                  concepto TEXT,
                  monto REAL,
                  categoria_id INTEGER,
                  FOREIGN KEY (categoria_id) REFERENCES categorias(id))''')

    # Tabla de gastos
    c.execute('''CREATE TABLE IF NOT EXISTS gastos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fecha TEXT,
                  tipo TEXT,
                  nombre TEXT,
                  monto REAL,
                  categoria_id INTEGER,
                  FOREIGN KEY (categoria_id) REFERENCES categorias(id))''')

    # Tabla de créditos programados (pagos fijos mensuales)
    c.execute('''CREATE TABLE IF NOT EXISTS creditos_programados
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT,
                  monto_mensual REAL,
                  dia_pago INTEGER,
                  fecha_inicio TEXT,
                  fecha_fin TEXT,
                  fecha_corte INTEGER,
                  fecha_limite_pago INTEGER,
                  fecha_apartado INTEGER,
                  dias_alerta INTEGER DEFAULT 10,
                  notas TEXT,
                  activo INTEGER DEFAULT 1)''')

    # Tabla de compras MSI
    c.execute('''CREATE TABLE IF NOT EXISTS compras_msi
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  producto TEXT,
                  precio_total REAL,
                  meses INTEGER,
                  mensualidad REAL,
                  fecha_primera_mensualidad TEXT,
                  meses_restantes INTEGER,
                  dia_pago INTEGER,
                  dias_alerta INTEGER DEFAULT 10,
                  activo INTEGER DEFAULT 1)''')

    # Tabla de configuración (nueva estructura con columnas directas)
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion
                 (id INTEGER PRIMARY KEY,
                  balance_inicial REAL DEFAULT 0,
                  primera_vez INTEGER DEFAULT 1,
                  vista_quincenal INTEGER DEFAULT 0,
                  fecha_pago_1 INTEGER DEFAULT 15,
                  fecha_pago_2 INTEGER DEFAULT 30,
                  usuario_id INTEGER DEFAULT 1)''')

    # Tabla de ingresos recurrentes
    c.execute('''CREATE TABLE IF NOT EXISTS ingresos_recurrentes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT,
                  monto REAL,
                  dia_pago INTEGER,
                  fecha_inicio TEXT,
                  fecha_fin TEXT,
                  frecuencia TEXT DEFAULT 'mensual',
                  mes_especifico INTEGER DEFAULT NULL,
                  activo INTEGER DEFAULT 1)''')

    # Tabla de préstamos
    c.execute('''CREATE TABLE IF NOT EXISTS prestamos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT NOT NULL,
                  monto_mensual REAL NOT NULL,
                  dia_pago INTEGER NOT NULL,
                  fecha_inicio TEXT NOT NULL,
                  fecha_fin TEXT NOT NULL,
                  dias_alerta INTEGER DEFAULT 10,
                  activo INTEGER DEFAULT 1)''')

    # Tabla de tarjetas de crédito
    c.execute('''CREATE TABLE IF NOT EXISTS tarjetas_credito
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT NOT NULL,
                  fecha_corte INTEGER NOT NULL,
                  fecha_pago_estimada INTEGER NOT NULL,
                  limite_credito REAL DEFAULT 0,
                  activo INTEGER DEFAULT 1)''')

    # Tabla de gastos de tarjeta de crédito
    c.execute('''CREATE TABLE IF NOT EXISTS gastos_tdc
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tarjeta_id INTEGER NOT NULL,
                  fecha TEXT NOT NULL,
                  concepto TEXT NOT NULL,
                  monto REAL NOT NULL,
                  tipo TEXT DEFAULT 'corriente',
                  meses_msi INTEGER DEFAULT 0,
                  mensualidad_msi REAL DEFAULT 0,
                  meses_restantes INTEGER DEFAULT 0,
                  categoria_id INTEGER,
                  activo INTEGER DEFAULT 1,
                  FOREIGN KEY (tarjeta_id) REFERENCES tarjetas_credito(id),
                  FOREIGN KEY (categoria_id) REFERENCES categorias(id))''')

    # Tabla de historial de simulaciones
    c.execute('''CREATE TABLE IF NOT EXISTS simulaciones_historial
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fecha_simulacion TEXT,
                  producto TEXT,
                  precio_total REAL,
                  meses INTEGER,
                  mensualidad REAL,
                  veredicto TEXT,
                  saldo_inicial REAL,
                  saldo_final_proyectado REAL,
                  mes_critico TEXT,
                  saldo_minimo REAL)''')

    # Agregar columna usuario_id a todas las tablas si no existe
    tablas = [
        'ingresos',
        'gastos',
        'creditos_programados',
        'compras_msi',
        'ingresos_recurrentes',
        'configuracion',
        'prestamos',
        'tarjetas_credito',
        'gastos_tdc',
        'categorias',
        'simulaciones_historial'
    ]

    for tabla in tablas:
        try:
            # Verificar si la tabla existe
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}'")
            if c.fetchone():
                # Verificar si la columna ya existe
                c.execute(f"PRAGMA table_info({tabla})")
                columnas = [col[1] for col in c.fetchall()]

                if 'usuario_id' not in columnas:
                    c.execute(f'ALTER TABLE {tabla} ADD COLUMN usuario_id INTEGER DEFAULT 1')
                    print(f"[OK] Columna usuario_id agregada a '{tabla}'")
        except Exception as e:
            print(f"[WARN] Error agregando usuario_id a '{tabla}': {str(e)}")

    # Agregar columnas frecuencia y mes_especifico a ingresos_recurrentes si no existen
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingresos_recurrentes'")
        if c.fetchone():
            c.execute("PRAGMA table_info(ingresos_recurrentes)")
            columnas_ing_rec = [col[1] for col in c.fetchall()]

            if 'frecuencia' not in columnas_ing_rec:
                c.execute('ALTER TABLE ingresos_recurrentes ADD COLUMN frecuencia TEXT DEFAULT "mensual"')
                print("[OK] Columna frecuencia agregada a 'ingresos_recurrentes'")

            if 'mes_especifico' not in columnas_ing_rec:
                c.execute('ALTER TABLE ingresos_recurrentes ADD COLUMN mes_especifico INTEGER DEFAULT NULL')
                print("[OK] Columna mes_especifico agregada a 'ingresos_recurrentes'")
    except Exception as e:
        print(f"[WARN] Error agregando columnas a ingresos_recurrentes: {str(e)}")

    # Insertar registro de configuración si no existe
    c.execute("INSERT OR IGNORE INTO configuracion (id, balance_inicial, primera_vez) VALUES (1, 0.0, 1)")

    # Insertar categorías predeterminadas
    categorias_default = [
        # Categorías de Gastos
        ('Alimentación', 'gasto', '#FF6384', 'utensils'),
        ('Transporte', 'gasto', '#36A2EB', 'car'),
        ('Vivienda', 'gasto', '#FFCE56', 'home'),
        ('Servicios', 'gasto', '#4BC0C0', 'bolt'),
        ('Entretenimiento', 'gasto', '#9966FF', 'gamepad'),
        ('Salud', 'gasto', '#FF9F40', 'heartbeat'),
        ('Educación', 'gasto', '#C9CBCF', 'graduation-cap'),
        ('Ropa', 'gasto', '#FF6384', 'tshirt'),
        ('Otros Gastos', 'gasto', '#6c757d', 'circle'),

        # Categorías de Ingresos
        ('Salario', 'ingreso', '#28a745', 'money-bill-wave'),
        ('Freelance', 'ingreso', '#20c997', 'laptop-code'),
        ('Inversiones', 'ingreso', '#17a2b8', 'chart-line'),
        ('Ventas', 'ingreso', '#ffc107', 'shopping-cart'),
        ('Otros Ingresos', 'ingreso', '#6c757d', 'circle')
    ]

    for categoria in categorias_default:
        c.execute('''INSERT OR IGNORE INTO categorias (nombre, tipo, color, icono)
                     VALUES (?, ?, ?, ?)''', categoria)

    # Insertar datos de demostración si la base de datos está vacía
    c.execute('SELECT COUNT(*) FROM ingresos')
    if c.fetchone()[0] == 0:
        print("[INFO] Insertando datos de demostración...")

        # Balance inicial
        c.execute('UPDATE configuracion SET balance_inicial=25000.0, primera_vez=0 WHERE id=1')

        # Ingresos recurrentes (nómina quincenal)
        c.execute('''INSERT INTO ingresos_recurrentes
                    (nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, activo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)''',
                 ('Nómina Quincenal 1', 12500.00, 10, '2025-01-01', '2099-12-31', 'mensual'))

        c.execute('''INSERT INTO ingresos_recurrentes
                    (nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, activo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)''',
                 ('Nómina Quincenal 2', 12500.00, 25, '2025-01-01', '2099-12-31', 'mensual'))

        # Préstamos
        c.execute('''INSERT INTO prestamos
                    (nombre, monto_mensual, dia_pago, fecha_inicio, fecha_fin, activo)
                    VALUES (?, ?, ?, ?, ?, 1)''',
                 ('Préstamo Personal', 3500.00, 15, '2025-01-01', '2026-12-31'))

        # Tarjetas de crédito
        c.execute('''INSERT INTO tarjetas_credito
                    (nombre, fecha_corte, fecha_pago_estimada, limite_credito, activo)
                    VALUES (?, ?, ?, ?, 1)''',
                 ('Visa Platino', 28, 16, 50000.00))

        c.execute('''INSERT INTO tarjetas_credito
                    (nombre, fecha_corte, fecha_pago_estimada, limite_credito, activo)
                    VALUES (?, ?, ?, ?, 1)''',
                 ('Mastercard Gold', 25, 10, 30000.00))

        # Gastos de TDC corrientes
        c.execute('''INSERT INTO gastos_tdc
                    (tarjeta_id, fecha, concepto, monto, tipo, activo)
                    VALUES (?, ?, ?, ?, ?, 1)''',
                 (1, '2025-11-20', 'Supermercado', 2500.50, 'corriente'))

        c.execute('''INSERT INTO gastos_tdc
                    (tarjeta_id, fecha, concepto, monto, tipo, activo)
                    VALUES (?, ?, ?, ?, ?, 1)''',
                 (2, '2025-11-18', 'Gasolina', 1200.00, 'corriente'))

        # Gastos MSI
        c.execute('''INSERT INTO gastos_tdc
                    (tarjeta_id, fecha, concepto, monto, tipo, meses_msi, mensualidad_msi, meses_restantes, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
                 (1, '2025-10-15', 'Laptop', 24000.00, 'msi', 12, 2000.00, 10))

        c.execute('''INSERT INTO gastos_tdc
                    (tarjeta_id, fecha, concepto, monto, tipo, meses_msi, mensualidad_msi, meses_restantes, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
                 (2, '2025-09-10', 'Celular', 18000.00, 'msi', 18, 1000.00, 15))

        print("[OK] Datos de demostración insertados")

    conn.commit()
    conn.close()
    print("[OK] Base de datos inicializada")
