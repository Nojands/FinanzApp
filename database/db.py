# database/db.py - Database functions
import sqlite3
from config import Config

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn


def init_db():
    """Initialize database"""
    conn = get_db_connection()
    c = conn.cursor()

    # Categories table
    c.execute('''CREATE TABLE IF NOT EXISTS categorias
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT UNIQUE NOT NULL,
                  tipo TEXT NOT NULL,
                  color TEXT DEFAULT '#6c757d',
                  icono TEXT DEFAULT 'circle')''')

    # Income table
    c.execute('''CREATE TABLE IF NOT EXISTS ingresos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fecha TEXT,
                  concepto TEXT,
                  monto REAL,
                  categoria_id INTEGER,
                  FOREIGN KEY (categoria_id) REFERENCES categorias(id))''')

    # Expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS gastos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fecha TEXT,
                  tipo TEXT,
                  nombre TEXT,
                  monto REAL,
                  categoria_id INTEGER,
                  FOREIGN KEY (categoria_id) REFERENCES categorias(id))''')

    # Scheduled credits table (fixed monthly payments)
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

    # Interest-free installments table (MSI)
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

    # Configuration table (new structure with direct columns)
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion
                 (id INTEGER PRIMARY KEY,
                  balance_inicial REAL DEFAULT 0,
                  primera_vez INTEGER DEFAULT 1,
                  vista_quincenal INTEGER DEFAULT 0,
                  fecha_pago_1 INTEGER DEFAULT 15,
                  fecha_pago_2 INTEGER DEFAULT 30,
                  usuario_id INTEGER DEFAULT 1)''')

    # Recurring income table
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

    # Loans table
    c.execute('''CREATE TABLE IF NOT EXISTS prestamos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT NOT NULL,
                  monto_mensual REAL NOT NULL,
                  dia_pago INTEGER NOT NULL,
                  fecha_inicio TEXT NOT NULL,
                  fecha_fin TEXT NOT NULL,
                  dias_alerta INTEGER DEFAULT 10,
                  activo INTEGER DEFAULT 1)''')

    # Credit cards table
    c.execute('''CREATE TABLE IF NOT EXISTS tarjetas_credito
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT NOT NULL,
                  fecha_corte INTEGER NOT NULL,
                  fecha_pago_estimada INTEGER NOT NULL,
                  limite_credito REAL DEFAULT 0,
                  activo INTEGER DEFAULT 1)''')

    # Credit card expenses table
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

    # Simulation history table
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

    # Add usuario_id column to all tables if it doesn't exist
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
            # Check if table exists
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}'")
            if c.fetchone():
                # Check if column already exists
                c.execute(f"PRAGMA table_info({tabla})")
                columnas = [col[1] for col in c.fetchall()]

                if 'usuario_id' not in columnas:
                    c.execute(f'ALTER TABLE {tabla} ADD COLUMN usuario_id INTEGER DEFAULT 1')
                    print(f"[OK] Column usuario_id added to '{tabla}'")
        except Exception as e:
            print(f"[WARN] Error adding usuario_id to '{tabla}': {str(e)}")

    # Add frecuencia and mes_especifico columns to ingresos_recurrentes if they don't exist
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingresos_recurrentes'")
        if c.fetchone():
            c.execute("PRAGMA table_info(ingresos_recurrentes)")
            columnas_ing_rec = [col[1] for col in c.fetchall()]

            if 'frecuencia' not in columnas_ing_rec:
                c.execute('ALTER TABLE ingresos_recurrentes ADD COLUMN frecuencia TEXT DEFAULT "mensual"')
                print("[OK] Column frecuencia added to 'ingresos_recurrentes'")

            if 'mes_especifico' not in columnas_ing_rec:
                c.execute('ALTER TABLE ingresos_recurrentes ADD COLUMN mes_especifico INTEGER DEFAULT NULL')
                print("[OK] Column mes_especifico added to 'ingresos_recurrentes'")
    except Exception as e:
        print(f"[WARN] Error adding columns to ingresos_recurrentes: {str(e)}")

    # Insert configuration record if it doesn't exist
    c.execute("INSERT OR IGNORE INTO configuracion (id, balance_inicial, primera_vez) VALUES (1, 0.0, 1)")

    # Insert default categories
    categorias_default = [
        # Expense Categories
        ('Alimentación', 'gasto', '#FF6384', 'utensils'),
        ('Transporte', 'gasto', '#36A2EB', 'car'),
        ('Vivienda', 'gasto', '#FFCE56', 'home'),
        ('Servicios', 'gasto', '#4BC0C0', 'bolt'),
        ('Entretenimiento', 'gasto', '#9966FF', 'gamepad'),
        ('Salud', 'gasto', '#FF9F40', 'heartbeat'),
        ('Educación', 'gasto', '#C9CBCF', 'graduation-cap'),
        ('Ropa', 'gasto', '#FF6384', 'tshirt'),
        ('Otros Gastos', 'gasto', '#6c757d', 'circle'),

        # Income Categories
        ('Salario', 'ingreso', '#28a745', 'money-bill-wave'),
        ('Freelance', 'ingreso', '#20c997', 'laptop-code'),
        ('Inversiones', 'ingreso', '#17a2b8', 'chart-line'),
        ('Ventas', 'ingreso', '#ffc107', 'shopping-cart'),
        ('Otros Ingresos', 'ingreso', '#6c757d', 'circle')
    ]

    for categoria in categorias_default:
        c.execute('''INSERT OR IGNORE INTO categorias (nombre, tipo, color, icono)
                     VALUES (?, ?, ?, ?)''', categoria)

    # Insert demo data ONLY in production (Render)
    # Check USAR_DATOS_DEMO environment variable
    import os
    usar_datos_demo = os.environ.get('USAR_DATOS_DEMO', 'false').lower() == 'true'

    c.execute('SELECT COUNT(*) FROM tarjetas_credito')
    if c.fetchone()[0] == 0 and usar_datos_demo:
        print("[INFO] Inserting demo data (USAR_DATOS_DEMO=true)...")

        # Initial balance
        c.execute('UPDATE configuracion SET balance_inicial=25000.0, primera_vez=0 WHERE id=1')

        # Recurring income (biweekly payroll)
        c.execute('''INSERT INTO ingresos_recurrentes
                    (nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, activo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)''',
                 ('Nómina Quincenal 1', 12500.00, 10, '2025-01-01', '2099-12-31', 'mensual'))

        c.execute('''INSERT INTO ingresos_recurrentes
                    (nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, activo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)''',
                 ('Nómina Quincenal 2', 12500.00, 25, '2025-01-01', '2099-12-31', 'mensual'))

        # Loans
        c.execute('''INSERT INTO prestamos
                    (nombre, monto_mensual, dia_pago, fecha_inicio, fecha_fin, activo)
                    VALUES (?, ?, ?, ?, ?, 1)''',
                 ('Préstamo Personal', 3500.00, 15, '2025-01-01', '2026-12-31'))

        # Credit cards
        c.execute('''INSERT INTO tarjetas_credito
                    (nombre, fecha_corte, fecha_pago_estimada, limite_credito, activo)
                    VALUES (?, ?, ?, ?, 1)''',
                 ('Visa Platino', 28, 16, 50000.00))

        c.execute('''INSERT INTO tarjetas_credito
                    (nombre, fecha_corte, fecha_pago_estimada, limite_credito, activo)
                    VALUES (?, ?, ?, ?, 1)''',
                 ('Mastercard Gold', 25, 10, 30000.00))

        # Regular credit card expenses
        c.execute('''INSERT INTO gastos_tdc
                    (tarjeta_id, fecha, concepto, monto, tipo, activo)
                    VALUES (?, ?, ?, ?, ?, 1)''',
                 (1, '2025-11-20', 'Supermercado', 2500.50, 'corriente'))

        c.execute('''INSERT INTO gastos_tdc
                    (tarjeta_id, fecha, concepto, monto, tipo, activo)
                    VALUES (?, ?, ?, ?, ?, 1)''',
                 (2, '2025-11-18', 'Gasolina', 1200.00, 'corriente'))

        # Interest-free installments (MSI)
        c.execute('''INSERT INTO gastos_tdc
                    (tarjeta_id, fecha, concepto, monto, tipo, meses_msi, mensualidad_msi, meses_restantes, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
                 (1, '2025-10-15', 'Laptop', 24000.00, 'msi', 12, 2000.00, 10))

        c.execute('''INSERT INTO gastos_tdc
                    (tarjeta_id, fecha, concepto, monto, tipo, meses_msi, mensualidad_msi, meses_restantes, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
                 (2, '2025-09-10', 'Celular', 18000.00, 'msi', 18, 1000.00, 15))

        print("[OK] Demo data inserted")

    conn.commit()
    conn.close()
    print("[OK] Database initialized")
