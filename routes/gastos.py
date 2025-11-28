# -*- coding: utf-8 -*-
# routes/gastos.py - Expense routes
from flask import request, redirect, flash
from routes import gastos_bp
from database import get_db_connection
from utils import validar_fecha, validar_monto, validar_texto
from datetime import datetime

@gastos_bp.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    """Add new expense (cash, card, or MSI purchase)"""
    from config import Config

    try:
        fecha = request.form.get('fecha', '').strip()
        tipo = request.form.get('tipo', 'efectivo')
        nombre = request.form.get('nombre', '').strip()
        monto_str = request.form.get('monto', '0')
        es_msi = request.form.get('es_msi', '0')  # '1' if checked
        categoria_id = request.form.get('categoria_id', None)
        tarjeta_id = request.form.get('tarjeta_id', None)

        # Get usuario_id
        usuario_id = Config.DEFAULT_USER_ID if Config.SKIP_LOGIN else 1

        # Validate data
        valido_fecha, fecha, error_fecha = validar_fecha(fecha, "Fecha", requerido=True)
        if not valido_fecha:
            flash(f'Error: {error_fecha}', 'error')
            return redirect('/')

        valido_nombre, nombre, error_nombre = validar_texto(nombre, "Nombre", min_length=1, max_length=200)
        if not valido_nombre:
            flash(f'Error: {error_nombre}', 'error')
            return redirect('/')

        valido_monto, monto, error_monto = validar_monto(monto_str, "Monto", minimo=0.01)
        if not valido_monto:
            flash(f'Error: {error_monto}', 'error')
            return redirect('/')

        conn = get_db_connection()
        c = conn.cursor()

        # If it's an MSI purchase
        if es_msi == '1':
            meses = int(request.form.get('meses', 3))
            fecha_primera = request.form.get('fecha_primera_msi', fecha)

            if not fecha_primera or fecha_primera.strip() == '':
                fecha_primera = datetime.now().strftime('%Y-%m-%d')

            mensualidad = monto / meses

            c.execute('''INSERT INTO compras_msi
                        (producto, precio_total, meses, mensualidad, fecha_primera_mensualidad, meses_restantes, usuario_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (nombre, monto, meses, mensualidad, fecha_primera, meses, usuario_id))
            conn.commit()
            conn.close()

            flash(f'MSI purchase added: {nombre} - {meses} months of ${mensualidad:.2f}', 'success')
            print(f"[MSI] Purchase added: {nombre} - ${monto:.2f} in {meses} months")

        # If it's a card expense (without MSI)
        elif tipo == 'tarjeta' and tarjeta_id:
            c.execute('''INSERT INTO gastos_tdc
                        (tarjeta_id, fecha, concepto, monto, categoria_id, usuario_id)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (tarjeta_id, fecha, nombre, monto, categoria_id if categoria_id else None, usuario_id))
            conn.commit()
            conn.close()

            flash(f'Card expense added: {nombre} - ${monto:.2f}', 'success')
            print(f"[CARD] Expense added: {nombre} - ${monto:.2f} (Card ID: {tarjeta_id})")

        # Cash/transfer expense
        else:
            c.execute('INSERT INTO gastos (fecha, tipo, nombre, monto, categoria_id, usuario_id) VALUES (?, ?, ?, ?, ?, ?)',
                     (fecha, tipo, nombre, monto, categoria_id if categoria_id else None, usuario_id))
            conn.commit()
            conn.close()

            flash(f'Expense added: {nombre} - ${monto:.2f}', 'success')
            print(f"[EXPENSE] {nombre} - ${monto:.2f} ({tipo})")

    except Exception as e:
        flash(f'Error adding expense: {str(e)}', 'error')
        print(f"[ERROR] Error adding expense: {str(e)}")
        import traceback
        traceback.print_exc()

    return redirect('/')


@gastos_bp.route('/borrar_gasto/<int:id>')
def borrar_gasto(id):
    """Delete specific expense"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM gastos WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('Expense deleted successfully', 'success')
        print(f"[DELETE] Expense {id} deleted")

    except Exception as e:
        flash(f'Error deleting expense: {str(e)}', 'error')
        print(f"[ERROR] Error deleting expense: {str(e)}")

    return redirect('/')


@gastos_bp.route('/borrar_gasto_tdc/<int:id>')
def borrar_gasto_tdc(id):
    """Delete credit card expense"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM gastos_tdc WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('Card expense deleted successfully', 'success')
        print(f"[DELETE] Card expense {id} deleted")

    except Exception as e:
        flash(f'Error deleting card expense: {str(e)}', 'error')
        print(f"[ERROR] Error deleting card expense: {str(e)}")

    return redirect('/')
