# -*- coding: utf-8 -*-
# routes/creditos.py - Scheduled credit routes
from flask import request, redirect, flash
from routes import creditos_bp
from database import get_db_connection
from utils import validar_fecha, validar_monto, validar_dia_mes, validar_texto, calcular_fecha_inicio_inteligente
from config import Config

@creditos_bp.route('/agregar_credito', methods=['POST'])
def agregar_credito():
    """Add scheduled credit"""
    try:
        nombre = request.form.get('nombre', '').strip()
        monto_str = request.form.get('monto', '0')
        dia_pago_str = request.form.get('dia_pago', '1')
        fecha_inicio = request.form.get('fecha_inicio', '').strip()
        fecha_fin = request.form.get('fecha_fin', '').strip()

        # Optional fields
        fecha_corte = int(request.form.get('fecha_corte', 0))
        fecha_limite_pago = int(request.form.get('fecha_limite_pago', 0))
        fecha_apartado = int(request.form.get('fecha_apartado', 0))
        dias_alerta = int(request.form.get('dias_alerta', 3))
        notas = request.form.get('notas', '')

        # Validate name
        valido_nombre, nombre, error_nombre = validar_texto(nombre, "Nombre")
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

        # If fecha_limite_pago is not set, use dia_pago
        if fecha_limite_pago == 0:
            fecha_limite_pago = dia_pago

        if fecha_apartado == 0:
            fecha_apartado = dia_pago

        # Validate/calculate start date
        if not fecha_inicio or fecha_inicio == '':
            fecha_inicio = calcular_fecha_inicio_inteligente(dia_pago, fecha_limite_pago)
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

        # Insert into database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO creditos_programados
                    (nombre, monto_mensual, dia_pago, fecha_inicio, fecha_fin,
                     fecha_corte, fecha_limite_pago, fecha_apartado, dias_alerta, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (nombre, monto, dia_pago, fecha_inicio, fecha_fin,
                  fecha_corte, fecha_limite_pago, fecha_apartado, dias_alerta, notas))
        conn.commit()
        conn.close()

        flash(f'Credit added: {nombre} - ${monto:.2f}/month', 'success')
        print(f"[CREDIT] {nombre} - ${monto:.2f}/month (day {dia_pago})")

    except Exception as e:
        flash(f'Error adding credit: {str(e)}', 'error')
        print(f"[ERROR] Error adding credit: {str(e)}")

    return redirect('/')


@creditos_bp.route('/desactivar_credito/<int:id>')
def desactivar_credito(id):
    """Deactivate (soft delete) credit"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE creditos_programados SET activo=0 WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('Credit deactivated', 'success')
        print(f"[DEACTIVATE] Credit {id} deactivated")

    except Exception as e:
        flash(f'Error deactivating credit: {str(e)}', 'error')
        print(f"[ERROR] Error deactivating credit: {str(e)}")

    return redirect('/')


@creditos_bp.route('/borrar_credito/<int:id>')
def borrar_credito(id):
    """Completely delete credit"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM creditos_programados WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('Credit deleted', 'success')
        print(f"[DELETE] Credit {id} deleted")

    except Exception as e:
        flash(f'Error deleting credit: {str(e)}', 'error')
        print(f"[ERROR] Error deleting credit: {str(e)}")

    return redirect('/')
