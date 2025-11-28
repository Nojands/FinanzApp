# -*- coding: utf-8 -*-
# routes/tarjetas.py - Credit card management routes
from flask import request, redirect, url_for, jsonify
from database import get_db_connection
from . import tarjetas_bp

@tarjetas_bp.route('/agregar_tarjeta', methods=['POST'])
def agregar_tarjeta():
    """Add new credit card"""
    try:
        nombre = request.form['nombre']
        fecha_corte = int(request.form['fecha_corte'])
        fecha_pago_estimada = int(request.form['fecha_pago_estimada'])
        limite_credito = float(request.form.get('limite_credito', 0))

        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''INSERT INTO tarjetas_credito (nombre, fecha_corte, fecha_pago_estimada, limite_credito)
                     VALUES (?, ?, ?, ?)''',
                  (nombre, fecha_corte, fecha_pago_estimada, limite_credito))

        conn.commit()
        conn.close()

        print(f"[CARD] Card added: {nombre} (Cutoff: {fecha_corte}, Payment: {fecha_pago_estimada})")
        return redirect(url_for('home'))

    except Exception as e:
        print(f"[ERROR] Error adding card: {e}")
        return redirect(url_for('home'))


@tarjetas_bp.route('/desactivar_tarjeta/<int:id>')
def desactivar_tarjeta(id):
    """Deactivate credit card"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('UPDATE tarjetas_credito SET activo=0 WHERE id=?', (id,))

        conn.commit()
        conn.close()

        print(f"[CARD] Card deactivated: ID {id}")
        return redirect(url_for('home'))

    except Exception as e:
        print(f"[ERROR] Error deactivating card: {e}")
        return redirect(url_for('home'))


@tarjetas_bp.route('/borrar_tarjeta/<int:id>')
def borrar_tarjeta(id):
    """Delete credit card"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Also delete all associated expenses
        c.execute('DELETE FROM gastos_tdc WHERE tarjeta_id=?', (id,))
        c.execute('DELETE FROM tarjetas_credito WHERE id=?', (id,))

        conn.commit()
        conn.close()

        print(f"[DELETE] Card deleted: ID {id}")
        return redirect(url_for('home'))

    except Exception as e:
        print(f"[ERROR] Error deleting card: {e}")
        return redirect(url_for('home'))


@tarjetas_bp.route('/agregar_gasto_tdc', methods=['POST'])
def agregar_gasto_tdc():
    """Add expense to credit card"""
    try:
        tarjeta_id = int(request.form['tarjeta_id'])
        fecha = request.form['fecha']
        concepto = request.form['concepto']
        monto = float(request.form['monto'])
        tipo = request.form.get('tipo', 'corriente')
        categoria_id = request.form.get('categoria_id', None)

        conn = get_db_connection()
        c = conn.cursor()

        if tipo == 'msi':
            meses_msi = int(request.form['meses_msi'])
            mensualidad_msi = monto / meses_msi
            meses_restantes = meses_msi

            c.execute('''INSERT INTO gastos_tdc
                         (tarjeta_id, fecha, concepto, monto, tipo, meses_msi, mensualidad_msi, meses_restantes, categoria_id)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (tarjeta_id, fecha, concepto, monto, tipo, meses_msi, mensualidad_msi, meses_restantes, categoria_id))

            print(f"[CARD MSI] Expense added: {concepto} - ${monto:.2f} in {meses_msi} months (${mensualidad_msi:.2f}/month)")

        else:
            c.execute('''INSERT INTO gastos_tdc
                         (tarjeta_id, fecha, concepto, monto, tipo, categoria_id)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (tarjeta_id, fecha, concepto, monto, tipo, categoria_id))

            print(f"[CARD] Regular expense added: {concepto} - ${monto:.2f}")

        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    except Exception as e:
        print(f"[ERROR] Error adding card expense: {e}")
        return redirect(url_for('home'))


@tarjetas_bp.route('/pago_anticipado_tdc/<int:id>', methods=['POST'])
def pago_anticipado_tdc(id):
    """Reduce remaining months of an MSI expense"""
    try:
        meses_a_pagar = int(request.form.get('meses_a_pagar', 1))

        conn = get_db_connection()
        c = conn.cursor()

        c.execute('SELECT meses_restantes FROM gastos_tdc WHERE id=?', (id,))
        row = c.fetchone()

        if row:
            meses_restantes = row['meses_restantes']
            nuevos_meses = max(0, meses_restantes - meses_a_pagar)

            c.execute('UPDATE gastos_tdc SET meses_restantes=? WHERE id=?', (nuevos_meses, id))

            if nuevos_meses == 0:
                c.execute('UPDATE gastos_tdc SET activo=0 WHERE id=?', (id,))
                print(f"[CARD MSI] MSI expense paid off (ID {id})")
            else:
                print(f"[CARD MSI] Early payment: {nuevos_meses} months remaining (ID {id})")

        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    except Exception as e:
        print(f"[ERROR] Error processing early payment: {e}")
        return redirect(url_for('home'))


@tarjetas_bp.route('/api/tarjeta/<int:id>/gastos')
def obtener_gastos_tarjeta(id):
    """Get expenses for a specific card (JSON API)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''SELECT g.*, cat.nombre as categoria_nombre
                     FROM gastos_tdc g
                     LEFT JOIN categorias cat ON g.categoria_id = cat.id
                     WHERE g.tarjeta_id = ? AND g.activo = 1
                     ORDER BY g.fecha DESC''', (id,))

        gastos = []
        for row in c.fetchall():
            gastos.append({
                'id': row['id'],
                'fecha': row['fecha'],
                'concepto': row['concepto'],
                'monto': row['monto'],
                'tipo': row['tipo'],
                'meses_msi': row['meses_msi'],
                'mensualidad_msi': row['mensualidad_msi'],
                'meses_restantes': row['meses_restantes'],
                'categoria': row['categoria_nombre']
            })

        conn.close()
        return jsonify(gastos)

    except Exception as e:
        print(f"[ERROR] Error fetching expenses: {e}")
        return jsonify([])
