# -*- coding: utf-8 -*-
# routes/configuracion.py - Configuration and recurring income management routes
from flask import request, redirect, flash
from routes import config_bp
from database import get_db_connection
from utils import validar_fecha, validar_monto, validar_dia_mes, validar_texto, calcular_fecha_inicio_inteligente
from config import Config

@config_bp.route('/configurar_balance_inicial', methods=['POST'])
def configurar_balance_inicial():
    """Configure initial balance (first time)"""
    try:
        balance_str = request.form.get('balance', '0')

        # Validate balance
        valido, balance, error = validar_monto(balance_str, "Balance inicial", minimo=None)
        if not valido:
            flash(f'Error: {error}', 'error')
            return redirect('/')

        conn = get_db_connection()
        c = conn.cursor()

        # Update initial balance and mark that it's no longer first time
        c.execute('UPDATE configuracion SET balance_inicial=?, primera_vez=0 WHERE id=1', (balance,))
        conn.commit()
        conn.close()

        flash(f'Balance inicial configurado: ${balance:.2f}', 'success')
        print(f"[OK] Balance inicial configurado: ${balance:.2f}")

    except Exception as e:
        flash(f'Error al configurar balance: {str(e)}', 'error')
        print(f"[ERROR] Error al configurar balance: {str(e)}")

    return redirect('/')


@config_bp.route('/editar_balance_inicial', methods=['POST'])
def editar_balance_inicial():
    """Edit initial balance"""
    try:
        balance_str = request.form.get('balance', '0')

        # Validate balance
        valido, balance, error = validar_monto(balance_str, "Balance inicial", minimo=None)
        if not valido:
            flash(f'Error: {error}', 'error')
            return redirect('/')

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE configuracion SET balance_inicial=? WHERE id=1', (balance,))
        conn.commit()
        conn.close()

        flash(f'Balance inicial actualizado: ${balance:.2f}', 'success')
        print(f"[OK] Balance inicial actualizado: ${balance:.2f}")

    except Exception as e:
        flash(f'Error al actualizar balance: {str(e)}', 'error')
        print(f"[ERROR] Error al actualizar balance: {str(e)}")

    return redirect('/')


@config_bp.route('/agregar_ingreso_recurrente', methods=['POST'])
def agregar_ingreso_recurrente():
    """Agregar ingreso recurrente (quincenal/mensual)"""
    try:
        nombre = request.form.get('nombre', '').strip()
        monto_str = request.form.get('monto', '0')
        dia_pago_str = request.form.get('dia_pago', '1')
        fecha_inicio = request.form.get('fecha_inicio', '').strip()
        fecha_fin = request.form.get('fecha_fin', '').strip()
        frecuencia = request.form.get('frecuencia', 'mensual').strip()
        mes_especifico_str = request.form.get('mes_especifico', '')

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
        valido_dia, dia_pago, error_dia = validar_dia_mes(dia_pago_str, "D�a de pago")
        if not valido_dia:
            flash(f'Error: {error_dia}', 'error')
            return redirect('/')

        # Validate/calculate start date
        if not fecha_inicio or fecha_inicio == '':
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

        # Process mes_especifico (only for annual frequency)
        mes_especifico = None
        if frecuencia == 'anual' and mes_especifico_str:
            try:
                mes_especifico = int(mes_especifico_str)
                if mes_especifico < 1 or mes_especifico > 12:
                    mes_especifico = None
            except:
                mes_especifico = None

        # Insert into database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO ingresos_recurrentes
                    (nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, mes_especifico)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, mes_especifico))
        conn.commit()
        conn.close()

        flash(f'Ingreso recurrente agregado: {nombre} - ${monto:.2f}/mes', 'success')
        print(f"[OK] Ingreso recurrente agregado: {nombre} - ${monto:.2f} cada d�a {dia_pago}")

    except Exception as e:
        flash(f'Error al agregar ingreso recurrente: {str(e)}', 'error')
        print(f"[ERROR] Error al agregar ingreso recurrente: {str(e)}")

    return redirect('/')


@config_bp.route('/desactivar_ingreso_recurrente/<int:id>')
def desactivar_ingreso_recurrente(id):
    """Desactivar (soft delete) un ingreso recurrente"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE ingresos_recurrentes SET activo=0 WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('Ingreso recurrente desactivado', 'success')
        print(f"[OK] Ingreso recurrente {id} desactivado")

    except Exception as e:
        flash(f'Error al desactivar ingreso recurrente: {str(e)}', 'error')
        print(f"[ERROR] Error al desactivar ingreso recurrente: {str(e)}")

    return redirect('/')


@config_bp.route('/borrar_ingreso_recurrente/<int:id>')
def borrar_ingreso_recurrente(id):
    """Borrar completamente un ingreso recurrente"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM ingresos_recurrentes WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('Ingreso recurrente eliminado', 'success')
        print(f"[OK] Ingreso recurrente {id} eliminado")

    except Exception as e:
        flash(f'Error al eliminar ingreso recurrente: {str(e)}', 'error')
        print(f"[ERROR] Error al eliminar ingreso recurrente: {str(e)}")

    return redirect('/')


@config_bp.route('/actualizar_vista_quincenal', methods=['POST'])
def actualizar_vista_quincenal():
    """Update biweekly view configuration"""
    try:
        from flask import session

        # Get form values
        vista_quincenal = 1 if request.form.get('vista_quincenal') == '1' else 0
        fecha_pago_1_str = request.form.get('fecha_pago_1', '15')
        fecha_pago_2_str = request.form.get('fecha_pago_2', '30')

        # Validate payment dates
        valido_1, fecha_pago_1, error_1 = validar_dia_mes(fecha_pago_1_str, "Primera fecha de pago")
        if not valido_1:
            flash(f'Error: {error_1}', 'error')
            return redirect('/')

        valido_2, fecha_pago_2, error_2 = validar_dia_mes(fecha_pago_2_str, "Segunda fecha de pago")
        if not valido_2:
            flash(f'Error: {error_2}', 'error')
            return redirect('/')

        # Validate that dates are different
        if fecha_pago_1 == fecha_pago_2:
            flash('Error: Las fechas de pago deben ser diferentes', 'error')
            return redirect('/')

        # Get usuario_id
        usuario_id = Config.DEFAULT_USER_ID if Config.SKIP_LOGIN else session.get('usuario_id', 1)

        # Update in database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''UPDATE configuracion
                     SET vista_quincenal=?, fecha_pago_1=?, fecha_pago_2=?
                     WHERE id=1 AND usuario_id=?''',
                  (vista_quincenal, fecha_pago_1, fecha_pago_2, usuario_id))
        conn.commit()
        conn.close()

        modo = "activada" if vista_quincenal else "desactivada"
        flash(f'Configuración actualizada: Vista quincenal {modo} (Pagos: día {fecha_pago_1} y {fecha_pago_2})', 'success')
        print(f"[OK] Vista quincenal {modo} - Fechas de pago: {fecha_pago_1} y {fecha_pago_2}")

    except Exception as e:
        flash(f'Error al actualizar configuración: {str(e)}', 'error')
        print(f"[ERROR] Error al actualizar vista quincenal: {str(e)}")

    return redirect('/')
