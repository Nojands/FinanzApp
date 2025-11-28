# -*- coding: utf-8 -*-
# routes/ingresos.py - Income and recurring income routes
from flask import request, redirect, flash
from routes import ingresos_bp
from database import get_db_connection
from utils import validar_fecha, validar_monto, validar_dia_mes, calcular_fecha_inicio_inteligente, validar_texto
from config import Config

@ingresos_bp.route('/agregar_ingreso', methods=['POST'])
def agregar_ingreso():
    """Add new income"""
    try:
        # Get form data
        fecha = request.form.get('fecha', '').strip()
        concepto = request.form.get('concepto', '').strip()
        monto_str = request.form.get('monto', '0')
        categoria_id = request.form.get('categoria_id', None)

        # Validate data
        valido_fecha, fecha, error_fecha = validar_fecha(fecha, "Fecha", requerido=True)
        if not valido_fecha:
            flash(f'Error: {error_fecha}', 'error')
            return redirect('/')

        valido_concepto, concepto, error_concepto = validar_texto(concepto, "Concepto", min_length=1, max_length=200)
        if not valido_concepto:
            flash(f'Error: {error_concepto}', 'error')
            return redirect('/')

        valido_monto, monto, error_monto = validar_monto(monto_str, "Monto", minimo=0.01)
        if not valido_monto:
            flash(f'Error: {error_monto}', 'error')
            return redirect('/')

        # Insert into database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO ingresos (fecha, concepto, monto, categoria_id) VALUES (?, ?, ?, ?)',
                  (fecha, concepto, monto, categoria_id if categoria_id else None))
        conn.commit()
        conn.close()

        flash(f'Income added successfully: {concepto} - ${monto:.2f}', 'success')
        print(f"[INCOME] {concepto} - ${monto:.2f}")

    except Exception as e:
        flash(f'Error adding income: {str(e)}', 'error')
        print(f"[ERROR] Error adding income: {str(e)}")

    return redirect('/')


@ingresos_bp.route('/borrar_ingreso/<int:id>')
def borrar_ingreso(id):
    """Delete specific income entry"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM ingresos WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash(f'Income deleted successfully', 'success')
        print(f"[DELETE] Income {id} deleted")

    except Exception as e:
        flash(f'Error deleting income: {str(e)}', 'error')
        print(f"[ERROR] Error deleting income: {str(e)}")

    return redirect('/')


@ingresos_bp.route('/agregar_ingreso_recurrente', methods=['POST'])
def agregar_ingreso_recurrente():
    """Add recurring income with different frequencies"""
    try:
        # Get form data
        nombre = request.form.get('nombre', '').strip()
        monto_str = request.form.get('monto', '0')
        dia_pago_str = request.form.get('dia_pago', '1')
        fecha_inicio = request.form.get('fecha_inicio', '').strip()
        fecha_fin = request.form.get('fecha_fin', '').strip()
        frecuencia = request.form.get('frecuencia', 'mensual')
        mes_especifico_str = request.form.get('mes_especifico', '')

        # Validate name
        valido_nombre, nombre, error_nombre = validar_texto(nombre, "Nombre", min_length=1, max_length=200)
        if not valido_nombre:
            flash(f'Error: {error_nombre}', 'error')
            return redirect('/')

        # Validate amount
        valido_monto, monto, error_monto = validar_monto(monto_str, "Monto", minimo=0.01)
        if not valido_monto:
            flash(f'Error: {error_monto}', 'error')
            return redirect('/')

        # Validate payment day
        valido_dia, dia_pago, error_dia = validar_dia_mes(dia_pago_str, "Día de pago")
        if not valido_dia:
            flash(f'Error: {error_dia}', 'error')
            return redirect('/')

        # Validate/calculate start date
        if not fecha_inicio or fecha_inicio == '':
            # Calculate intelligently
            fecha_inicio = calcular_fecha_inicio_inteligente(dia_pago)
        else:
            valido_fecha_inicio, fecha_inicio, error_fecha_inicio = validar_fecha(fecha_inicio, "Fecha de inicio")
            if not valido_fecha_inicio:
                flash(f'Error: {error_fecha_inicio}', 'error')
                return redirect('/')

        # Validate end date (optional)
        if not fecha_fin or fecha_fin == '':
            fecha_fin = Config.FECHA_INDEFINIDA
        else:
            valido_fecha_fin, fecha_fin, error_fecha_fin = validar_fecha(fecha_fin, "Fecha fin", requerido=False)
            if not valido_fecha_fin:
                flash(f'Error: {error_fecha_fin}', 'error')
                return redirect('/')

        # Validate specific month for annual frequency
        mes_especifico = None
        if frecuencia == 'anual' and mes_especifico_str:
            try:
                mes_especifico = int(mes_especifico_str)
                if mes_especifico < 1 or mes_especifico > 12:
                    flash('Error: Month must be between 1 and 12', 'error')
                    return redirect('/')
            except:
                flash('Error: Invalid specific month', 'error')
                return redirect('/')

        # Insert into database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO ingresos_recurrentes
                     (nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, mes_especifico)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, mes_especifico))
        conn.commit()
        conn.close()

        # Customized message based on frequency
        frecuencia_texto = {
            'semanal': 'every week',
            'quincenal': 'every two weeks',
            'mensual': 'every month',
            'bimestral': 'every 2 months',
            'trimestral': 'every 3 months',
            'semestral': 'every 6 months',
            'anual': 'every year'
        }.get(frecuencia, 'periodically')

        flash(f'Recurring income added: {nombre} - ${monto:.2f} {frecuencia_texto}', 'success')
        print(f"[RECURRING] Income added: {nombre} - ${monto:.2f} {frecuencia_texto} (from {fecha_inicio} to {fecha_fin})")

    except Exception as e:
        flash(f'Error adding recurring income: {str(e)}', 'error')
        print(f"[ERROR] Error adding recurring income: {str(e)}")

    return redirect('/')


@ingresos_bp.route('/desactivar_ingreso_recurrente/<int:id>')
def desactivar_ingreso_recurrente(id):
    """Deactivate recurring income"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE ingresos_recurrentes SET activo=0 WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('Recurring income deactivated', 'success')
        print(f"[DEACTIVATE] Recurring income {id} deactivated")

    except Exception as e:
        flash(f'Error deactivating recurring income: {str(e)}', 'error')
        print(f"[ERROR] Error deactivating recurring income: {str(e)}")

    return redirect('/')


@ingresos_bp.route('/borrar_ingreso_recurrente/<int:id>')
def borrar_ingreso_recurrente(id):
    """Completely delete recurring income"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM ingresos_recurrentes WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('Recurring income deleted', 'success')
        print(f"[DELETE] Recurring income {id} deleted")

    except Exception as e:
        flash(f'Error deleting recurring income: {str(e)}', 'error')
        print(f"[ERROR] Error deleting recurring income: {str(e)}")

    return redirect('/')
