# -*- coding: utf-8 -*-
# routes/msi.py - MSI (interest-free installments) purchase routes
from flask import request, redirect, flash, jsonify
from routes import msi_bp
from database import get_db_connection
from utils import validar_monto, validar_texto
from datetime import datetime

@msi_bp.route('/agregar_compra_msi', methods=['POST'])
def agregar_compra_msi():
    """Add confirmed MSI purchase"""
    try:
        producto = request.form.get('producto', '').strip()
        precio_str = request.form.get('precio', '0')
        meses = int(request.form.get('meses', 3))
        fecha_primera = request.form.get('fecha_primera', '').strip()

        # Validate product
        valido_producto, producto, error_producto = validar_texto(producto, "Producto")
        if not valido_producto:
            flash(f'Error: {error_producto}', 'error')
            return redirect('/')

        # Validate price
        valido_precio, precio, error_precio = validar_monto(precio_str, "Precio", minimo=0.01)
        if not valido_precio:
            flash(f'Error: {error_precio}', 'error')
            return redirect('/')

        # If fecha_primera is empty, use current date
        if not fecha_primera or fecha_primera == '':
            fecha_primera = datetime.now().strftime('%Y-%m-%d')

        mensualidad = precio / meses

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO compras_msi
                    (producto, precio_total, meses, mensualidad, fecha_primera_mensualidad, meses_restantes)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (producto, precio, meses, mensualidad, fecha_primera, meses))
        conn.commit()
        conn.close()

        flash(f'MSI purchase added: {producto} - {meses} months of ${mensualidad:.2f}', 'success')
        print(f"[OK] MSI purchase added: {producto} - ${precio:.2f} in {meses} months")

    except Exception as e:
        flash(f'Error adding MSI purchase: {str(e)}', 'error')
        print(f"[ERROR] Error adding MSI purchase: {str(e)}")

    return redirect('/')


@msi_bp.route('/simular_compra', methods=['POST'])
def simular_compra():
    """Simulate MSI purchase and see its impact"""
    try:
        from services import simular_compra as simular_compra_servicio

        precio = float(request.json.get('precio', 0))
        meses = int(request.json.get('meses', 3))
        producto = request.json.get('producto', 'Unnamed').strip()

        # Simulate purchase
        resultado = simular_compra_servicio(precio, meses)

        # Save to history
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''INSERT INTO simulaciones_historial
                    (fecha_simulacion, producto, precio_total, meses, mensualidad,
                     veredicto, saldo_inicial, saldo_final_proyectado, mes_critico, saldo_minimo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  producto,
                  precio,
                  meses,
                  resultado['mensualidad'],
                  resultado['veredicto'],
                  resultado['saldo_inicial'],
                  resultado['saldo_final'],
                  resultado['mes_critico'],
                  resultado['saldo_minimo']))

        conn.commit()
        conn.close()

        print(f"[OK] Simulation saved: {producto} - ${precio:.2f} in {meses} MSI - Verdict: {resultado['veredicto']}")

        return jsonify(resultado)

    except Exception as e:
        print(f"[ERROR] Simulator error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'veredicto': 'ERROR',
            'problema_mes': None
        }), 500


@msi_bp.route('/pago_anticipado_msi/<int:id>', methods=['POST'])
def pago_anticipado_msi(id):
    """Register early MSI payment (reduce remaining months)"""
    try:
        meses_pagados = int(request.form.get('meses_pagados', 1))

        conn = get_db_connection()
        c = conn.cursor()

        # Get current remaining months
        c.execute('SELECT meses_restantes FROM compras_msi WHERE id=?', (id,))
        result = c.fetchone()

        if not result:
            flash('MSI purchase not found', 'error')
            return redirect('/')

        meses_restantes = result[0]
        nuevos_meses = max(0, meses_restantes - meses_pagados)

        # Update
        c.execute('UPDATE compras_msi SET meses_restantes=? WHERE id=?', (nuevos_meses, id))

        # If it reaches 0, deactivate
        if nuevos_meses == 0:
            c.execute('UPDATE compras_msi SET activo=0 WHERE id=?', (id,))

        conn.commit()
        conn.close()

        flash(f'Early payment registered: {meses_pagados} months', 'success')
        print(f"[OK] Early payment registered: {meses_pagados} months")

    except Exception as e:
        flash(f'Error registering early payment: {str(e)}', 'error')
        print(f"[ERROR] Error registering early payment: {str(e)}")

    return redirect('/')


@msi_bp.route('/desactivar_msi/<int:id>')
def desactivar_msi(id):
    """Deactivate MSI purchase"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE compras_msi SET activo=0 WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('MSI purchase deactivated', 'success')
        print(f"[OK] MSI purchase {id} deactivated")

    except Exception as e:
        flash(f'Error deactivating MSI purchase: {str(e)}', 'error')
        print(f"[ERROR] Error deactivating MSI purchase: {str(e)}")

    return redirect('/')


@msi_bp.route('/borrar_msi/<int:id>')
def borrar_msi(id):
    """Completely delete MSI purchase"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM compras_msi WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash('MSI purchase deleted', 'success')
        print(f"[OK] MSI purchase {id} deleted")

    except Exception as e:
        flash(f'Error deleting MSI purchase: {str(e)}', 'error')
        print(f"[ERROR] Error deleting MSI purchase: {str(e)}")

    return redirect('/')
