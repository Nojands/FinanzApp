# -*- coding: utf-8 -*-
# app.py - FinanzApp Modular - Main Application
from flask import Flask, render_template, session
from config import Config
from database import init_db, get_db_connection
from services import calcular_proyeccion_meses, obtener_proximas_alertas

# Import blueprints
from routes import (
    ingresos_bp,
    gastos_bp,
    creditos_bp,
    msi_bp,
    dashboard_bp,
    config_bp,
    reportes_bp,
    prestamos_bp,
    tarjetas_bp,
    api_bp,
    cashback_bp,
    investments_bp
)

# Create Flask application
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Register blueprints
app.register_blueprint(ingresos_bp)
app.register_blueprint(gastos_bp)
app.register_blueprint(creditos_bp)
app.register_blueprint(msi_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(config_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(prestamos_bp)
app.register_blueprint(tarjetas_bp)
app.register_blueprint(api_bp)
app.register_blueprint(cashback_bp)
app.register_blueprint(investments_bp)


@app.route('/')
def home():
    """Main page with dashboard"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get usuario_id (currently always 1 due to SKIP_LOGIN)
        usuario_id = Config.DEFAULT_USER_ID if Config.SKIP_LOGIN else session.get('usuario_id', 1)

        # Get configuration (including biweekly view)
        c.execute('SELECT balance_inicial, primera_vez, vista_quincenal, fecha_pago_1, fecha_pago_2 FROM configuracion WHERE id=1 AND usuario_id=?', (usuario_id,))
        config_row = c.fetchone()

        if config_row:
            balance_inicial = config_row['balance_inicial']
            primera_vez = config_row['primera_vez']
            vista_quincenal = config_row['vista_quincenal'] if config_row['vista_quincenal'] is not None else 0
            fecha_pago_1 = config_row['fecha_pago_1'] if config_row['fecha_pago_1'] is not None else 15
            fecha_pago_2 = config_row['fecha_pago_2'] if config_row['fecha_pago_2'] is not None else 30
        else:
            balance_inicial = 0.0
            primera_vez = 1
            vista_quincenal = 0
            fecha_pago_1 = 15
            fecha_pago_2 = 30

        # Current data (filtered by user)
        c.execute('SELECT * FROM ingresos WHERE usuario_id=? ORDER BY fecha DESC LIMIT 10', (usuario_id,))
        ingresos = c.fetchall()

        c.execute('SELECT * FROM gastos WHERE usuario_id=? ORDER BY fecha DESC LIMIT 10', (usuario_id,))
        gastos = c.fetchall()

        # Credit card expenses (with card info)
        c.execute('''SELECT gt.*, tc.nombre as tarjeta_nombre, tc.fecha_pago_estimada, tc.fecha_corte
                     FROM gastos_tdc gt
                     JOIN tarjetas_credito tc ON gt.tarjeta_id = tc.id
                     WHERE gt.usuario_id=? AND gt.activo=1
                     ORDER BY tc.nombre, gt.fecha DESC''', (usuario_id,))
        gastos_tdc = c.fetchall()

        c.execute('SELECT SUM(monto) as total FROM ingresos WHERE usuario_id=?', (usuario_id,))
        total_ingresos_row = c.fetchone()
        total_ingresos = total_ingresos_row['total'] if total_ingresos_row['total'] else 0.0

        c.execute('SELECT SUM(monto) as total FROM gastos WHERE usuario_id=?', (usuario_id,))
        total_gastos_row = c.fetchone()
        total_gastos = total_gastos_row['total'] if total_gastos_row['total'] else 0.0

        # NOTE: Credit card expenses are NOT summed here because they haven't been paid yet.
        # They will appear as pending in alerts and projections until their payment date.

        # Credits and MSI (keep for compatibility)
        c.execute('SELECT * FROM creditos_programados WHERE activo=1 AND usuario_id=?', (usuario_id,))
        creditos = c.fetchall()

        c.execute('SELECT * FROM compras_msi WHERE activo=1 AND usuario_id=?', (usuario_id,))
        msis = c.fetchall()

        # Loans (new system)
        c.execute('SELECT * FROM prestamos WHERE activo=1 AND usuario_id=?', (usuario_id,))
        prestamos = c.fetchall()

        # Credit Cards (new system)
        c.execute('SELECT * FROM tarjetas_credito WHERE activo=1 AND usuario_id=?', (usuario_id,))
        tarjetas = c.fetchall()

        # Recurring income
        c.execute('SELECT * FROM ingresos_recurrentes WHERE activo=1 AND usuario_id=?', (usuario_id,))
        ingresos_recurrentes = c.fetchall()

        # Simulation history (last 10)
        c.execute('''SELECT * FROM simulaciones_historial
                     WHERE usuario_id=?
                     ORDER BY fecha_simulacion DESC
                     LIMIT 10''', (usuario_id,))
        historial_simulaciones = c.fetchall()

        # Get categories (filtered by user)
        c.execute('SELECT * FROM categorias WHERE usuario_id=? ORDER BY tipo, nombre', (usuario_id,))
        categorias = c.fetchall()

        # Real balance = Initial balance + Income - Expenses
        balance = balance_inicial + total_ingresos - total_gastos

        conn.close()

        # Calculate monthly projection (always)
        proyeccion = calcular_proyeccion_meses(Config.PROYECCION_MESES_DEFAULT)

        # Calculate biweekly projection if enabled
        proyeccion_quincenal = None
        if vista_quincenal == 1:
            from services import calcular_quincenas_a_proyectar, calcular_proyeccion_quincenal
            # Dynamically calculate how many biweekly periods to project
            num_quincenas = calcular_quincenas_a_proyectar()
            # Calculate biweekly projection with user's custom payment dates
            proyeccion_quincenal = calcular_proyeccion_quincenal(num_quincenas, fecha_pago_1, fecha_pago_2)

        # Get upcoming alerts
        alertas = obtener_proximas_alertas(15)

        return render_template('index.html',
                             ingresos=ingresos,
                             gastos=gastos,
                             gastos_tdc=gastos_tdc,
                             creditos=creditos,
                             msis=msis,
                             prestamos=prestamos,
                             tarjetas=tarjetas,
                             ingresos_recurrentes=ingresos_recurrentes,
                             historial_simulaciones=historial_simulaciones,
                             balance_inicial=balance_inicial,
                             total_ingresos=total_ingresos,
                             total_gastos=total_gastos,
                             balance=balance,
                             primera_vez=primera_vez,
                             proyeccion=proyeccion,
                             proyeccion_quincenal=proyeccion_quincenal,
                             vista_quincenal=vista_quincenal,
                             fecha_pago_1=fecha_pago_1,
                             fecha_pago_2=fecha_pago_2,
                             alertas=alertas,
                             categorias=categorias)

    except Exception as e:
        print(f"[ERROR] Error on main page: {str(e)}")
        return f"Error loading page: {str(e)}", 500


if __name__ == '__main__':
    import os

    # Initialize database on startup
    init_db()

    # Start server
    print("=" * 60)
    print("  FINANZAPP - Personal Financial Management System")
    print("=" * 60)

    # Railway provides port via environment variable
    port = int(os.environ.get('PORT', 5000))

    print(f"  Server: http://0.0.0.0:{port}")
    print(f"  Dashboard: http://0.0.0.0:{port}/dashboard")
    print("=" * 60)
    print("")

    app.run(debug=False, host='0.0.0.0', port=port)
