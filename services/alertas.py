# services/alertas.py - Payment alerts logic
import sqlite3
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from config import Config

def obtener_proximas_alertas(dias_adelante=15):
    """
    Get upcoming payment alerts

    Args:
        dias_adelante: Days ahead to search for alerts

    Returns:
        list: List of dictionaries with alerts
    """
    conn = sqlite3.connect(Config.DATABASE_PATH)
    c = conn.cursor()

    # Get active credits with alerts
    c.execute('''SELECT id, nombre, monto_mensual, fecha_limite_pago, dias_alerta, notas, fecha_inicio, fecha_fin
                 FROM creditos_programados WHERE activo=1''')
    creditos = c.fetchall()

    # Get active MSI purchases
    c.execute('''SELECT id, producto, mensualidad, dia_pago, dias_alerta
                 FROM compras_msi WHERE activo=1 AND meses_restantes > 0''')
    msis = c.fetchall()

    conn.close()

    alertas = []
    hoy = datetime.now()

    # Process credits
    for cred in creditos:
        dia_limite = cred[3]
        dias_alerta = cred[4] or 10
        fecha_inicio_str = cred[6]
        fecha_fin_str = cred[7]

        # Verify if credit has already started
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            if hoy < fecha_inicio:
                # Credit hasn't started yet, don't show alerts
                continue

        # Verify if credit has already ended
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
            if hoy > fecha_fin:
                # Credit has already ended, don't show alerts
                continue

        # Calculate next payment date (this month or next)
        for mes_offset in range(3):  # Check next 3 months
            fecha_pago = hoy + relativedelta(months=mes_offset)
            try:
                fecha_pago = datetime(fecha_pago.year, fecha_pago.month, dia_limite)
            except ValueError:
                # If day doesn't exist in that month (e.g., Feb 31), use last day
                fecha_pago = datetime(fecha_pago.year, fecha_pago.month, 1) + relativedelta(months=1, days=-1)

            dias_para_pago = (fecha_pago - hoy).days

            # Use dias_alerta from specific credit instead of global dias_adelante
            if 0 <= dias_para_pago <= dias_alerta:
                urgencia = "urgente" if dias_para_pago <= 2 else "proximo" if dias_para_pago <= 5 else "programado"

                alertas.append({
                    'tipo': 'credito',
                    'nombre': cred[1],
                    'monto': cred[2],
                    'fecha_pago': fecha_pago,
                    'dias_restantes': dias_para_pago,
                    'urgencia': urgencia,
                    'notas': cred[5] or ''
                })
                break

    # Process MSI purchases
    for msi in msis:
        dia_pago = msi[3] if msi[3] else 15
        dias_alerta = msi[4] or 10

        for mes_offset in range(3):
            fecha_pago = hoy + relativedelta(months=mes_offset)
            try:
                fecha_pago = datetime(fecha_pago.year, fecha_pago.month, dia_pago)
            except ValueError:
                fecha_pago = datetime(fecha_pago.year, fecha_pago.month, 1) + relativedelta(months=1, days=-1)

            dias_para_pago = (fecha_pago - hoy).days

            # Use dias_alerta from specific MSI instead of global dias_adelante
            if 0 <= dias_para_pago <= dias_alerta:
                urgencia = "urgente" if dias_para_pago <= 2 else "proximo" if dias_para_pago <= 5 else "programado"

                alertas.append({
                    'tipo': 'msi',
                    'nombre': msi[1],
                    'monto': msi[2],
                    'fecha_pago': fecha_pago,
                    'dias_restantes': dias_para_pago,
                    'urgencia': urgencia,
                    'notas': ''
                })
                break

    # Sort by nearest date
    alertas.sort(key=lambda x: x['dias_restantes'])

    return alertas
