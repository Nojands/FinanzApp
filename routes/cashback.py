# -*- coding: utf-8 -*-
# routes/cashback.py - Cashback management routes
from flask import request, redirect, flash, jsonify
from routes import cashback_bp
from database import get_db_connection
from utils import validar_fecha, validar_monto, validar_texto
from config import Config

@cashback_bp.route('/add_cashback', methods=['POST'])
def add_cashback():
    """Add new cashback entry"""
    try:
        # Get form data
        source = request.form.get('source', '').strip()
        amount_str = request.form.get('amount', '0')
        date_earned = request.form.get('date_earned', '').strip()
        date_received = request.form.get('date_received', '').strip()
        status = request.form.get('status', 'pending')
        card_id = request.form.get('card_id', None)
        category_id = request.form.get('category_id', None)
        notes = request.form.get('notes', '').strip()

        # Validate source
        valid_source, source, error_source = validar_texto(source, "Source", min_length=1, max_length=200)
        if not valid_source:
            flash(f'Error: {error_source}', 'error')
            return redirect('/')

        # Validate amount
        valid_amount, amount, error_amount = validar_monto(amount_str, "Amount", minimo=0.01)
        if not valid_amount:
            flash(f'Error: {error_amount}', 'error')
            return redirect('/')

        # Validate date earned
        valid_date_earned, date_earned, error_date_earned = validar_fecha(date_earned, "Date Earned", requerido=True)
        if not valid_date_earned:
            flash(f'Error: {error_date_earned}', 'error')
            return redirect('/')

        # Validate date received (optional)
        if date_received:
            valid_date_received, date_received, error_date_received = validar_fecha(date_received, "Date Received", requerido=False)
            if not valid_date_received:
                flash(f'Error: {error_date_received}', 'error')
                return redirect('/')
        else:
            date_received = None

        # Insert into database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO cashback
                     (source, amount, date_earned, date_received, status, card_id, category_id, notes, active)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
                  (source, amount, date_earned, date_received, status,
                   card_id if card_id else None,
                   category_id if category_id else None,
                   notes))
        conn.commit()
        conn.close()

        flash(f'Cashback added successfully: {source} - ${amount:.2f}', 'success')
        print(f"[CASHBACK] {source} - ${amount:.2f} ({status})")

    except Exception as e:
        flash(f'Error adding cashback: {str(e)}', 'error')
        print(f"[ERROR] Error adding cashback: {str(e)}")

    return redirect('/')


@cashback_bp.route('/update_cashback_status/<int:id>', methods=['POST'])
def update_cashback_status(id):
    """Update cashback status (pending -> received)"""
    try:
        status = request.form.get('status', 'received')
        date_received = request.form.get('date_received', '').strip()

        # Validate date received
        valid_date, date_received, error_date = validar_fecha(date_received, "Date Received", requerido=True)
        if not valid_date:
            flash(f'Error: {error_date}', 'error')
            return redirect('/')

        # Update database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''UPDATE cashback
                     SET status = ?, date_received = ?
                     WHERE id = ?''',
                  (status, date_received, id))
        conn.commit()
        conn.close()

        flash(f'Cashback status updated successfully', 'success')
        print(f"[CASHBACK] Status updated for ID {id}: {status}")

    except Exception as e:
        flash(f'Error updating cashback status: {str(e)}', 'error')
        print(f"[ERROR] Error updating cashback status: {str(e)}")

    return redirect('/')


@cashback_bp.route('/delete_cashback/<int:id>')
def delete_cashback(id):
    """Delete cashback entry"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM cashback WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash(f'Cashback deleted successfully', 'success')
        print(f"[DELETE] Cashback {id} deleted")

    except Exception as e:
        flash(f'Error deleting cashback: {str(e)}', 'error')
        print(f"[ERROR] Error deleting cashback: {str(e)}")

    return redirect('/')


@cashback_bp.route('/deactivate_cashback/<int:id>')
def deactivate_cashback(id):
    """Deactivate cashback entry (soft delete)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE cashback SET active=0 WHERE id=?', (id,))
        conn.commit()
        conn.close()

        flash(f'Cashback deactivated successfully', 'success')
        print(f"[DEACTIVATE] Cashback {id} deactivated")

    except Exception as e:
        flash(f'Error deactivating cashback: {str(e)}', 'error')
        print(f"[ERROR] Error deactivating cashback: {str(e)}")

    return redirect('/')


@cashback_bp.route('/api/cashback/summary')
def get_cashback_summary():
    """Get cashback summary (total pending, total received, total by card)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Total pending cashback
        c.execute('''SELECT COALESCE(SUM(amount), 0)
                     FROM cashback
                     WHERE status = 'pending' AND active = 1''')
        total_pending = c.fetchone()[0]

        # Total received cashback
        c.execute('''SELECT COALESCE(SUM(amount), 0)
                     FROM cashback
                     WHERE status = 'received' AND active = 1''')
        total_received = c.fetchone()[0]

        # Cashback by card
        c.execute('''SELECT t.nombre, COALESCE(SUM(cb.amount), 0) as total
                     FROM cashback cb
                     JOIN tarjetas_credito t ON cb.card_id = t.id
                     WHERE cb.active = 1
                     GROUP BY t.nombre
                     ORDER BY total DESC''')
        by_card = [{'card': row[0], 'total': row[1]} for row in c.fetchall()]

        conn.close()

        return jsonify({
            'total_pending': total_pending,
            'total_received': total_received,
            'by_card': by_card
        })

    except Exception as e:
        print(f"[ERROR] Error getting cashback summary: {str(e)}")
        return jsonify({'error': str(e)}), 500
