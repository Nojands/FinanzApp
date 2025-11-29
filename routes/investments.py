# -*- coding: utf-8 -*-
# routes/investments.py - Investment management routes
from flask import request, redirect, flash, jsonify
from routes import investments_bp
from database import get_db_connection
from utils import validar_fecha, validar_monto, validar_texto
from config import Config
from datetime import datetime

@investments_bp.route('/add_investment', methods=['POST'])
def add_investment():
    """Add new investment"""
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        investment_type = request.form.get('investment_type', '').strip()
        initial_amount_str = request.form.get('initial_amount', '0')
        current_value_str = request.form.get('current_value', '0')
        start_date = request.form.get('start_date', '').strip()
        expected_return_rate_str = request.form.get('expected_return_rate', '0')
        maturity_date = request.form.get('maturity_date', '').strip()
        platform = request.form.get('platform', '').strip()
        notes = request.form.get('notes', '').strip()

        # Validate name
        valid_name, name, error_name = validar_texto(name, "Name", min_length=1, max_length=200)
        if not valid_name:
            flash(f'Error: {error_name}', 'error')
            return redirect('/')

        # Validate investment type
        valid_type, investment_type, error_type = validar_texto(investment_type, "Investment Type", min_length=1, max_length=100)
        if not valid_type:
            flash(f'Error: {error_type}', 'error')
            return redirect('/')

        # Validate initial amount
        valid_initial, initial_amount, error_initial = validar_monto(initial_amount_str, "Initial Amount", minimo=0.01)
        if not valid_initial:
            flash(f'Error: {error_initial}', 'error')
            return redirect('/')

        # Validate current value (optional, defaults to initial amount)
        if current_value_str:
            valid_current, current_value, error_current = validar_monto(current_value_str, "Current Value", minimo=0.0)
            if not valid_current:
                flash(f'Error: {error_current}', 'error')
                return redirect('/')
        else:
            current_value = initial_amount

        # Validate start date
        valid_start, start_date, error_start = validar_fecha(start_date, "Start Date", requerido=True)
        if not valid_start:
            flash(f'Error: {error_start}', 'error')
            return redirect('/')

        # Validate expected return rate (percentage)
        try:
            expected_return_rate = float(expected_return_rate_str) if expected_return_rate_str else 0.0
            if expected_return_rate < 0 or expected_return_rate > 100:
                flash('Error: Expected return rate must be between 0 and 100', 'error')
                return redirect('/')
        except ValueError:
            flash('Error: Invalid expected return rate', 'error')
            return redirect('/')

        # Validate maturity date (optional)
        if maturity_date:
            valid_maturity, maturity_date, error_maturity = validar_fecha(maturity_date, "Maturity Date", requerido=False)
            if not valid_maturity:
                flash(f'Error: {error_maturity}', 'error')
                return redirect('/')
        else:
            maturity_date = None

        # Insert into database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO investments
                     (name, investment_type, initial_amount, current_value, start_date,
                      expected_return_rate, maturity_date, platform, notes, status, active)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 1)''',
                  (name, investment_type, initial_amount, current_value, start_date,
                   expected_return_rate, maturity_date, platform, notes))

        investment_id = c.lastrowid

        # Record initial transaction
        c.execute('''INSERT INTO investment_transactions
                     (investment_id, transaction_type, amount, transaction_date, notes)
                     VALUES (?, 'deposit', ?, ?, ?)''',
                  (investment_id, initial_amount, start_date, 'Initial investment'))

        conn.commit()
        conn.close()

        flash(f'Investment added successfully: {name} - ${initial_amount:.2f}', 'success')
        print(f"[INVESTMENT] {name} - ${initial_amount:.2f} ({investment_type})")

    except Exception as e:
        flash(f'Error adding investment: {str(e)}', 'error')
        print(f"[ERROR] Error adding investment: {str(e)}")

    return redirect('/')


@investments_bp.route('/add_investment_transaction/<int:id>', methods=['POST'])
def add_investment_transaction(id):
    """Add transaction to existing investment (deposit, withdrawal, or return)"""
    try:
        # Get form data
        transaction_type = request.form.get('transaction_type', 'return')
        amount_str = request.form.get('amount', '0')
        transaction_date = request.form.get('transaction_date', '').strip()
        notes = request.form.get('notes', '').strip()

        # Validate amount
        valid_amount, amount, error_amount = validar_monto(amount_str, "Amount", minimo=0.01)
        if not valid_amount:
            flash(f'Error: {error_amount}', 'error')
            return redirect('/')

        # Validate date
        valid_date, transaction_date, error_date = validar_fecha(transaction_date, "Transaction Date", requerido=True)
        if not valid_date:
            flash(f'Error: {error_date}', 'error')
            return redirect('/')

        conn = get_db_connection()
        c = conn.cursor()

        # Get current investment value
        c.execute('SELECT current_value FROM investments WHERE id = ?', (id,))
        result = c.fetchone()
        if not result:
            flash('Error: Investment not found', 'error')
            return redirect('/')

        current_value = result[0]

        # Update investment value based on transaction type
        if transaction_type == 'deposit':
            new_value = current_value + amount
        elif transaction_type == 'withdrawal':
            new_value = current_value - amount
        else:  # return/profit
            new_value = current_value + amount

        # Record transaction
        c.execute('''INSERT INTO investment_transactions
                     (investment_id, transaction_type, amount, transaction_date, notes)
                     VALUES (?, ?, ?, ?, ?)''',
                  (id, transaction_type, amount, transaction_date, notes))

        # Update investment current value
        c.execute('UPDATE investments SET current_value = ? WHERE id = ?', (new_value, id))

        conn.commit()
        conn.close()

        flash(f'Transaction recorded successfully: {transaction_type} ${amount:.2f}', 'success')
        print(f"[INVESTMENT TRANSACTION] ID {id}: {transaction_type} ${amount:.2f}")

    except Exception as e:
        flash(f'Error adding transaction: {str(e)}', 'error')
        print(f"[ERROR] Error adding investment transaction: {str(e)}")

    return redirect('/')


@investments_bp.route('/update_investment/<int:id>', methods=['POST'])
def update_investment(id):
    """Update investment details"""
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        investment_type = request.form.get('investment_type', '').strip()
        current_value_str = request.form.get('current_value', '0')
        expected_return_rate_str = request.form.get('expected_return_rate', '0')
        maturity_date = request.form.get('maturity_date', '').strip()
        status = request.form.get('status', 'active')
        platform = request.form.get('platform', '').strip()
        notes = request.form.get('notes', '').strip()

        # Validate name
        valid_name, name, error_name = validar_texto(name, "Name", min_length=1, max_length=200)
        if not valid_name:
            flash(f'Error: {error_name}', 'error')
            return redirect('/')

        # Validate current value
        valid_value, current_value, error_value = validar_monto(current_value_str, "Current Value", minimo=0.0)
        if not valid_value:
            flash(f'Error: {error_value}', 'error')
            return redirect('/')

        # Validate expected return rate
        try:
            expected_return_rate = float(expected_return_rate_str) if expected_return_rate_str else 0.0
            if expected_return_rate < 0 or expected_return_rate > 100:
                flash('Error: Expected return rate must be between 0 and 100', 'error')
                return redirect('/')
        except ValueError:
            flash('Error: Invalid expected return rate', 'error')
            return redirect('/')

        # Validate maturity date (optional)
        if maturity_date:
            valid_maturity, maturity_date, error_maturity = validar_fecha(maturity_date, "Maturity Date", requerido=False)
            if not valid_maturity:
                flash(f'Error: {error_maturity}', 'error')
                return redirect('/')
        else:
            maturity_date = None

        # Update database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''UPDATE investments
                     SET name = ?, investment_type = ?, current_value = ?,
                         expected_return_rate = ?, maturity_date = ?, status = ?,
                         platform = ?, notes = ?
                     WHERE id = ?''',
                  (name, investment_type, current_value, expected_return_rate,
                   maturity_date, status, platform, notes, id))
        conn.commit()
        conn.close()

        flash(f'Investment updated successfully', 'success')
        print(f"[INVESTMENT] ID {id} updated")

    except Exception as e:
        flash(f'Error updating investment: {str(e)}', 'error')
        print(f"[ERROR] Error updating investment: {str(e)}")

    return redirect('/')


@investments_bp.route('/delete_investment/<int:id>')
def delete_investment(id):
    """Delete investment and all its transactions"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Delete transactions first (foreign key constraint)
        c.execute('DELETE FROM investment_transactions WHERE investment_id=?', (id,))

        # Delete investment
        c.execute('DELETE FROM investments WHERE id=?', (id,))

        conn.commit()
        conn.close()

        flash(f'Investment deleted successfully', 'success')
        print(f"[DELETE] Investment {id} and its transactions deleted")

    except Exception as e:
        flash(f'Error deleting investment: {str(e)}', 'error')
        print(f"[ERROR] Error deleting investment: {str(e)}")

    return redirect('/')


@investments_bp.route('/deactivate_investment/<int:id>')
def deactivate_investment(id):
    """Deactivate investment (soft delete / mark as completed)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE investments SET active=0, status='completed' WHERE id=?", (id,))
        conn.commit()
        conn.close()

        flash(f'Investment deactivated successfully', 'success')
        print(f"[DEACTIVATE] Investment {id} deactivated")

    except Exception as e:
        flash(f'Error deactivating investment: {str(e)}', 'error')
        print(f"[ERROR] Error deactivating investment: {str(e)}")

    return redirect('/')


@investments_bp.route('/api/investments/summary')
def get_investments_summary():
    """Get investments summary (total invested, current value, total returns)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Total initial investment
        c.execute('''SELECT COALESCE(SUM(initial_amount), 0)
                     FROM investments
                     WHERE active = 1''')
        total_invested = c.fetchone()[0]

        # Total current value
        c.execute('''SELECT COALESCE(SUM(current_value), 0)
                     FROM investments
                     WHERE active = 1''')
        current_value = c.fetchone()[0]

        # Total returns (profit/loss)
        total_returns = current_value - total_invested

        # Return rate percentage
        return_rate = (total_returns / total_invested * 100) if total_invested > 0 else 0

        # Investments by type
        c.execute('''SELECT investment_type, COUNT(*) as count,
                            COALESCE(SUM(initial_amount), 0) as invested,
                            COALESCE(SUM(current_value), 0) as current
                     FROM investments
                     WHERE active = 1
                     GROUP BY investment_type
                     ORDER BY current DESC''')
        by_type = [{
            'type': row[0],
            'count': row[1],
            'invested': row[2],
            'current': row[3],
            'return': row[3] - row[2]
        } for row in c.fetchall()]

        conn.close()

        return jsonify({
            'total_invested': total_invested,
            'current_value': current_value,
            'total_returns': total_returns,
            'return_rate': return_rate,
            'by_type': by_type
        })

    except Exception as e:
        print(f"[ERROR] Error getting investments summary: {str(e)}")
        return jsonify({'error': str(e)}), 500


@investments_bp.route('/api/investments/<int:id>/transactions')
def get_investment_transactions(id):
    """Get all transactions for a specific investment"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''SELECT id, transaction_type, amount, transaction_date, notes
                     FROM investment_transactions
                     WHERE investment_id = ?
                     ORDER BY transaction_date DESC''', (id,))

        transactions = [{
            'id': row[0],
            'type': row[1],
            'amount': row[2],
            'date': row[3],
            'notes': row[4]
        } for row in c.fetchall()]

        conn.close()

        return jsonify({'transactions': transactions})

    except Exception as e:
        print(f"[ERROR] Error getting investment transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500
