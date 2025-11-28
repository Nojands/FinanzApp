# services/simulador.py - Purchase simulator logic
from database import get_db_connection
from datetime import datetime
from dateutil.relativedelta import relativedelta

def simular_compra(precio, meses):
    """
    Simulate impact of an MSI purchase on projection

    Args:
        precio: Total purchase price
        meses: Interest-free months

    Returns:
        dict: Simulation result with month-by-month projection
    """
    conn = get_db_connection()
    c = conn.cursor()

    # Get initial balance
    c.execute("SELECT balance_inicial FROM configuracion WHERE id=1")
    result = c.fetchone()
    balance_inicial = float(result[0]) if result else 0.0

    # Get income and expense totals
    c.execute('SELECT SUM(monto) as total FROM ingresos')
    total_ingresos_row = c.fetchone()
    total_ingresos = total_ingresos_row['total'] if total_ingresos_row['total'] else 0.0

    c.execute('SELECT SUM(monto) as total FROM gastos')
    total_gastos_row = c.fetchone()
    total_gastos = total_gastos_row['total'] if total_gastos_row['total'] else 0.0

    # Calculate current balance
    saldo_actual = balance_inicial + total_ingresos - total_gastos

    # Get recurring income
    c.execute('SELECT * FROM ingresos_recurrentes WHERE activo=1')
    ingresos_rec = c.fetchall()

    # Get scheduled credits
    c.execute('SELECT * FROM creditos_programados WHERE activo=1')
    creditos = c.fetchall()

    # Get active MSI purchases
    c.execute('SELECT * FROM compras_msi WHERE activo=1')
    msis = c.fetchall()

    conn.close()

    # Calculate monthly payment
    mensualidad = precio / meses

    # Project month by month (up to number of months or 12, whichever is greater)
    meses_proyectar = max(meses, 12)
    proyeccion = []

    fecha_actual = datetime.now()
    saldo_sin_compra = saldo_actual
    saldo_con_compra = saldo_actual

    for i in range(meses_proyectar):
        mes_fecha = fecha_actual + relativedelta(months=i)
        mes_nombre = mes_fecha.strftime('%Y-%m')

        # Calculate month income
        ingresos_mes = 0.0
        for ing in ingresos_rec:
            # Verify if active in this month
            fecha_inicio = datetime.strptime(ing['fecha_inicio'], '%Y-%m-%d')
            if ing['fecha_fin'] and ing['fecha_fin'] != '2099-12-31':
                fecha_fin = datetime.strptime(ing['fecha_fin'], '%Y-%m-%d')
                if mes_fecha < fecha_inicio or mes_fecha > fecha_fin:
                    continue
            elif mes_fecha < fecha_inicio:
                continue

            ingresos_mes += ing['monto']

        # Calculate month expenses (credits)
        gastos_mes = 0.0
        for credito in creditos:
            fecha_inicio = datetime.strptime(credito['fecha_inicio'], '%Y-%m-%d')
            if credito['fecha_fin'] and credito['fecha_fin'] != '2099-12-31':
                fecha_fin = datetime.strptime(credito['fecha_fin'], '%Y-%m-%d')
                if mes_fecha < fecha_inicio or mes_fecha > fecha_fin:
                    continue
            elif mes_fecha < fecha_inicio:
                continue

            gastos_mes += credito['monto_mensual']

        # Calculate existing MSI
        for msi in msis:
            if msi['meses_restantes'] > 0:
                fecha_primera = datetime.strptime(msi['fecha_primera_mensualidad'], '%Y-%m-%d')
                meses_transcurridos = (mes_fecha.year - fecha_primera.year) * 12 + (mes_fecha.month - fecha_primera.month)

                if 0 <= meses_transcurridos < msi['meses']:
                    gastos_mes += msi['mensualidad']

        # Calculate balance WITHOUT the new purchase
        saldo_sin_compra = saldo_sin_compra + ingresos_mes - gastos_mes

        # Calculate balance WITH the new purchase (subtract monthly payment only during MSI months)
        if i < meses:
            saldo_con_compra = saldo_con_compra + ingresos_mes - gastos_mes - mensualidad
        else:
            saldo_con_compra = saldo_con_compra + ingresos_mes - gastos_mes

        # Determine statuses
        if saldo_sin_compra > 10000:
            estado_sin = "verde"
        elif saldo_sin_compra > 0:
            estado_sin = "amarillo"
        else:
            estado_sin = "rojo"

        if saldo_con_compra > 10000:
            estado_con = "verde"
        elif saldo_con_compra > 0:
            estado_con = "amarillo"
        else:
            estado_con = "rojo"

        proyeccion.append({
            'mes': mes_nombre,
            'numero_mes': i + 1,
            'ingresos': ingresos_mes,
            'gastos': gastos_mes,
            'mensualidad_msi': mensualidad if i < meses else 0,
            'saldo_sin_compra': round(saldo_sin_compra, 2),
            'saldo_con_compra': round(saldo_con_compra, 2),
            'diferencia': round(saldo_sin_compra - saldo_con_compra, 2),
            'estado_sin': estado_sin,
            'estado_con': estado_con
        })

    # Determine verdict
    veredicto = "SI"
    problema_en_mes = None
    mes_critico = None
    saldo_minimo = min(proyeccion, key=lambda x: x['saldo_con_compra'])

    for mes in proyeccion:
        if mes['estado_con'] == "rojo":
            if mes['numero_mes'] <= 3:
                veredicto = "NO"
                problema_en_mes = mes['numero_mes']
                mes_critico = mes['mes']
                break
            else:
                veredicto = "CUIDADO"
                problema_en_mes = mes['numero_mes']
                mes_critico = mes['mes']
                break

    return {
        'precio': precio,
        'meses': meses,
        'mensualidad': round(mensualidad, 2),
        'saldo_inicial': round(saldo_actual, 2),
        'proyeccion': proyeccion,
        'veredicto': veredicto,
        'problema_mes': problema_en_mes,
        'mes_critico': mes_critico,
        'saldo_minimo': round(saldo_minimo['saldo_con_compra'], 2),
        'saldo_final': round(proyeccion[-1]['saldo_con_compra'], 2)
    }
