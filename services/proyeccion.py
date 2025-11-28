# services/proyeccion.py - Financial projection logic
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.helpers import parse_fecha
from config import Config

# Dictionary of month names in Spanish
MESES_ES = {
    1: 'enero',
    2: 'febrero',
    3: 'marzo',
    4: 'abril',
    5: 'mayo',
    6: 'junio',
    7: 'julio',
    8: 'agosto',
    9: 'septiembre',
    10: 'octubre',
    11: 'noviembre',
    12: 'diciembre'
}

def calcular_proyeccion_meses(meses_adelante=6):
    """
    Calculate balance projection for the next X months

    Args:
        meses_adelante: Number of months to project

    Returns:
        list: List of dictionaries with projection by month
    """
    conn = sqlite3.connect(Config.DATABASE_PATH)
    c = conn.cursor()

    # Get initial balance
    try:
        c.execute("SELECT balance_inicial FROM configuracion WHERE id=1")
        result = c.fetchone()
        saldo_actual = float(result[0]) if result else 0.0
    except:
        saldo_actual = 0.0

    # Get already registered income and expenses
    c.execute('SELECT SUM(monto) FROM ingresos')
    total_ingresos = c.fetchone()[0] or 0

    c.execute('SELECT SUM(monto) FROM gastos')
    total_gastos = c.fetchone()[0] or 0

    # Apply historical income and expenses to balance
    saldo_actual = saldo_actual + total_ingresos - total_gastos

    # Save current balance to calculate percentages
    balance_actual = saldo_actual

    # Get active loans with dates
    c.execute('SELECT nombre, monto_mensual, dia_pago, fecha_inicio, fecha_fin FROM prestamos WHERE activo=1')
    prestamos = c.fetchall()

    # Get active recurring income with dates and frequency
    c.execute('SELECT nombre, monto, dia_pago, fecha_inicio, fecha_fin, frecuencia, mes_especifico FROM ingresos_recurrentes WHERE activo=1')
    ingresos_rec = c.fetchall()

    # Get ALL active cards with their totals (regular expenses + MSI)
    c.execute('''SELECT
                    tc.id,
                    tc.nombre,
                    tc.fecha_pago_estimada,
                    COALESCE(SUM(CASE WHEN gt.tipo = 'corriente' THEN gt.monto ELSE 0 END), 0) as total_gastos_corrientes,
                    COALESCE(SUM(CASE WHEN gt.tipo = 'msi' THEN gt.mensualidad_msi ELSE 0 END), 0) as total_msi
                 FROM tarjetas_credito tc
                 LEFT JOIN gastos_tdc gt ON tc.id = gt.tarjeta_id AND gt.activo = 1
                 WHERE tc.activo = 1
                 GROUP BY tc.id''')
    tarjetas = c.fetchall()

    conn.close()

    # Project upcoming months
    proyeccion = []
    fecha_actual = datetime.now()

    for i in range(meses_adelante):
        mes_futuro = fecha_actual + relativedelta(months=i)
        mes_nombre = f"{MESES_ES[mes_futuro.month].capitalize()} {mes_futuro.year}"

        # For comparison, use only year-month (ignore day)
        mes_futuro_comparacion = datetime(mes_futuro.year, mes_futuro.month, 1)

        # Calculate month INCOME (only if active in that month)
        ingresos_mes = 0
        for ing in ingresos_rec:
            fecha_inicio = parse_fecha(ing[3])
            fecha_inicio_mes = datetime(fecha_inicio.year, fecha_inicio.month, 1)

            fecha_fin = parse_fecha(ing[4])
            fecha_fin_mes = datetime(fecha_fin.year, fecha_fin.month, 1)

            # Verify if month is within range
            if not (fecha_inicio_mes <= mes_futuro_comparacion <= fecha_fin_mes):
                continue

            # Get frequency (default monthly if doesn't exist)
            frecuencia = ing[5] if len(ing) > 5 and ing[5] else 'mensual'
            mes_especifico = ing[6] if len(ing) > 6 else None

            # Determine if it applies according to frequency
            aplica = False
            meses_desde_inicio = (mes_futuro_comparacion.year - fecha_inicio_mes.year) * 12 + (mes_futuro_comparacion.month - fecha_inicio_mes.month)

            if frecuencia == 'semanal':
                # Para semanal, aplicar en todos los meses (simplificación)
                aplica = True
            elif frecuencia == 'quincenal':
                # Para quincenal, aplicar en todos los meses (simplificación)
                aplica = True
            elif frecuencia == 'mensual':
                aplica = True
            elif frecuencia == 'bimestral':
                aplica = (meses_desde_inicio % 2 == 0)
            elif frecuencia == 'trimestral':
                aplica = (meses_desde_inicio % 3 == 0)
            elif frecuencia == 'semestral':
                aplica = (meses_desde_inicio % 6 == 0)
            elif frecuencia == 'anual':
                # Para anual, verificar si es el mes específico o el mes de inicio
                if mes_especifico:
                    aplica = (mes_futuro.month == mes_especifico)
                else:
                    aplica = (mes_futuro.month == fecha_inicio.month)

            if aplica:
                ingresos_mes += ing[1]

        # Calculate month EXPENSES (only loans active in that month)
        pago_prestamos = 0
        for prestamo in prestamos:
            fecha_inicio = parse_fecha(prestamo[3])
            fecha_inicio_mes = datetime(fecha_inicio.year, fecha_inicio.month, 1)

            fecha_fin = parse_fecha(prestamo[4])
            fecha_fin_mes = datetime(fecha_fin.year, fecha_fin.month, 1)

            # Only apply if month is within range
            if fecha_inicio_mes <= mes_futuro_comparacion <= fecha_fin_mes:
                pago_prestamos += prestamo[1]

        # Calculate CARD payments (regular expenses + monthly MSI)
        # Each card pays MONTHLY its total (expenses + MSI)
        pago_tarjetas = 0
        for tarjeta in tarjetas:
            total_tarjeta = tarjeta[3] + tarjeta[4]  # regular_expenses + msi
            pago_tarjetas += total_tarjeta

        pago_total_mes = pago_prestamos + pago_tarjetas

        # Update balance: + income - expenses
        saldo_actual = saldo_actual + ingresos_mes - pago_total_mes

        # Determine status (traffic light) based on percentage of current balance
        if balance_actual > 0:
            porcentaje_saldo = (saldo_actual / balance_actual) * 100

            if porcentaje_saldo >= 30:
                estado = "verde"  # Greater than or equal to 30% of current balance
            elif porcentaje_saldo >= 5:
                estado = "amarillo"  # Between 5% and 29% of current balance
            else:
                estado = "rojo"  # Less than 5% of current balance
        else:
            # If current balance is 0 or negative, use absolute balance
            if saldo_actual > 1000:
                estado = "verde"
            elif saldo_actual > 0:
                estado = "amarillo"
            else:
                estado = "rojo"

        proyeccion.append({
            'mes': mes_nombre,
            'ingresos_mes': ingresos_mes,
            'pago_total': pago_total_mes,
            'saldo_estimado': saldo_actual,
            'estado': estado
        })

    return proyeccion


def calcular_proyeccion_quincenal(quincenas_adelante=12, fecha_pago_1=15, fecha_pago_2=30):
    """
    Calculate balance projection for the next X biweekly periods

    Args:
        quincenas_adelante: Number of biweekly periods to project (default 12 = 6 months)
        fecha_pago_1: Day of month for first payment (e.g., 10, 15)
        fecha_pago_2: Day of month for second payment (e.g., 25, 30)

    Returns:
        list: List of dictionaries with projection by biweekly period
    """
    conn = sqlite3.connect(Config.DATABASE_PATH)
    c = conn.cursor()

    # Obtener balance inicial
    try:
        c.execute("SELECT balance_inicial FROM configuracion WHERE id=1")
        result = c.fetchone()
        saldo_actual = float(result[0]) if result else 0.0
    except:
        saldo_actual = 0.0

    # Obtener ingresos y gastos ya registrados
    c.execute('SELECT SUM(monto) FROM ingresos')
    total_ingresos = c.fetchone()[0] or 0

    c.execute('SELECT SUM(monto) FROM gastos')
    total_gastos = c.fetchone()[0] or 0

    # Aplicar ingresos y gastos históricos al saldo
    saldo_actual = saldo_actual + total_ingresos - total_gastos

    # Guardar el balance actual para calcular porcentajes
    balance_actual = saldo_actual

    # Obtener préstamos activos
    c.execute('SELECT nombre, monto_mensual, dia_pago, fecha_inicio, fecha_fin FROM prestamos WHERE activo=1')
    prestamos = c.fetchall()

    # Obtener ingresos recurrentes activos
    c.execute('SELECT nombre, monto, dia_pago, fecha_inicio, fecha_fin FROM ingresos_recurrentes WHERE activo=1')
    ingresos_rec = c.fetchall()

    # Obtener tarjetas con gastos corrientes (solo para el primer corte)
    c.execute('''SELECT
                    tc.id,
                    tc.nombre,
                    tc.fecha_pago_estimada,
                    COALESCE(SUM(gt.monto), 0) as total_gastos_corrientes
                 FROM tarjetas_credito tc
                 LEFT JOIN gastos_tdc gt ON tc.id = gt.tarjeta_id AND gt.activo = 1 AND gt.tipo = 'corriente'
                 WHERE tc.activo = 1
                 GROUP BY tc.id''')
    tarjetas_corrientes = c.fetchall()

    # Obtener TODOS los MSI individuales para calcular si están activos en cada mes
    c.execute('''SELECT
                    gt.id,
                    gt.tarjeta_id,
                    tc.nombre as tarjeta_nombre,
                    tc.fecha_pago_estimada,
                    gt.fecha,
                    gt.concepto,
                    gt.meses_msi,
                    gt.mensualidad_msi,
                    gt.meses_restantes
                 FROM gastos_tdc gt
                 JOIN tarjetas_credito tc ON gt.tarjeta_id = tc.id
                 WHERE gt.activo = 1 AND gt.tipo = 'msi' AND tc.activo = 1''')
    msi_list = c.fetchall()

    conn.close()

    # Trackear qué tarjetas corrientes ya fueron pagadas (se pagan una sola vez)
    corrientes_ya_pagadas = set()

    # Determinar quincenas
    # Quincena 1: (fecha_pago_2 + 1) hasta fecha_pago_1
    # Quincena 2: (fecha_pago_1 + 1) hasta fecha_pago_2

    proyeccion = []
    fecha_actual = datetime.now()

    # Determinar en qué quincena estamos actualmente
    dia_actual = fecha_actual.day

    # Determinar la quincena ACTUAL según las fechas de nómina:
    # Quincena 1: del 25 al 9 (día fecha_pago_2 al fecha_pago_1 - 1)
    # Quincena 2: del 10 al 24 (día fecha_pago_1 al fecha_pago_2 - 1)
    # La quincena INICIA el día que recibes la nómina

    if fecha_pago_1 <= dia_actual <= fecha_pago_2 - 1:
        # Estamos en quincena 2 (ej: del 10 al 24)
        quincena_actual = 2
        fecha_inicio_quincena = datetime(fecha_actual.year, fecha_actual.month, fecha_pago_1)
    else:
        # Estamos en quincena 1 (ej: del 25 al 9 del siguiente mes)
        quincena_actual = 1
        if dia_actual >= fecha_pago_2:
            # Estamos entre el 25-30/31 del mes actual
            fecha_inicio_quincena = datetime(fecha_actual.year, fecha_actual.month, fecha_pago_2)
        else:
            # Estamos entre el 1-9 del mes (quincena 1 que cruzó del mes anterior)
            mes_anterior = fecha_actual - relativedelta(months=1)
            fecha_inicio_quincena = datetime(mes_anterior.year, mes_anterior.month, fecha_pago_2)

    for i in range(quincenas_adelante):
        # Determinar el número de quincena (alterna 1-2-1-2...)
        # Para i=0 usamos quincena_actual, luego alternamos
        if i == 0:
            num_quincena = quincena_actual
        else:
            # Alternar entre 1 y 2
            num_quincena = 1 if num_quincena == 2 else 2

        # Calcular fechas de inicio y fin de la quincena
        if num_quincena == 1:
            # Quincena 1: fecha_pago_2 hasta (fecha_pago_1 - 1)
            # Recibes nómina el día fecha_pago_2 (día 25)
            dia_inicio = fecha_pago_2
            dia_fin = fecha_pago_1 - 1  # Termina el día antes de recibir la siguiente nómina
            dia_ingreso = fecha_pago_2
        else:
            # Quincena 2: fecha_pago_1 hasta (fecha_pago_2 - 1)
            # Recibes nómina el día fecha_pago_1 (día 10)
            dia_inicio = fecha_pago_1
            dia_fin = fecha_pago_2 - 1  # Termina el día antes de recibir la siguiente nómina
            dia_ingreso = fecha_pago_1

        # Determinar el mes de la quincena
        # Si dia_inicio > dia_fin, la quincena cruza el mes
        if dia_inicio > dia_fin:
            # La quincena cruza al siguiente mes
            mes_inicio = fecha_inicio_quincena.month
            ano_inicio = fecha_inicio_quincena.year

            fecha_fin_quincena = datetime(ano_inicio, mes_inicio, dia_inicio) + relativedelta(months=1)
            try:
                fecha_fin_quincena = datetime(fecha_fin_quincena.year, fecha_fin_quincena.month, dia_fin)
            except ValueError:
                # Día no válido en ese mes, usar último día
                fecha_fin_quincena = datetime(fecha_fin_quincena.year, fecha_fin_quincena.month, 1) + relativedelta(months=1, days=-1)
        else:
            # La quincena está en el mismo mes
            mes_inicio = fecha_inicio_quincena.month
            ano_inicio = fecha_inicio_quincena.year
            try:
                fecha_fin_quincena = datetime(ano_inicio, mes_inicio, dia_fin)
            except ValueError:
                fecha_fin_quincena = datetime(ano_inicio, mes_inicio, 1) + relativedelta(months=1, days=-1)

        # Nombre de la quincena con rango de fechas para claridad
        mes_nombre = MESES_ES[fecha_inicio_quincena.month].capitalize()
        # Mostrar rango de fechas para evitar confusión
        nombre_quincena = f"{mes_nombre} {fecha_inicio_quincena.year} - Quincena {num_quincena} ({dia_inicio} {MESES_ES[fecha_inicio_quincena.month][:3]} - {dia_fin} {MESES_ES[fecha_fin_quincena.month][:3]})"

        # Calcular INGRESOS de la quincena
        ingresos_quincena = 0
        for ing in ingresos_rec:
            dia_pago_ing = ing[2]
            fecha_inicio_ing = parse_fecha(ing[3])
            fecha_fin_ing = parse_fecha(ing[4])

            # Verificar si el ingreso está activo en este período
            if not (fecha_inicio_ing <= fecha_fin_quincena and fecha_fin_ing >= fecha_inicio_quincena):
                continue

            # Construir la fecha EXACTA de pago del ingreso en esta quincena
            if dia_inicio > dia_fin:
                # Quincena cruza meses
                if dia_pago_ing >= dia_inicio:
                    try:
                        fecha_pago_ing = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, dia_pago_ing)
                    except ValueError:
                        fecha_pago_ing = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, 1) + relativedelta(months=1, days=-1)
                else:
                    try:
                        fecha_pago_ing = datetime(fecha_fin_quincena.year, fecha_fin_quincena.month, dia_pago_ing)
                    except ValueError:
                        fecha_pago_ing = datetime(fecha_fin_quincena.year, fecha_fin_quincena.month, 1) + relativedelta(months=1, days=-1)
            else:
                # Quincena NO cruza meses
                try:
                    fecha_pago_ing = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, dia_pago_ing)
                except ValueError:
                    fecha_pago_ing = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, 1) + relativedelta(months=1, days=-1)

            # Verificar si la fecha de pago cae dentro del rango de esta quincena
            if fecha_inicio_quincena <= fecha_pago_ing <= fecha_fin_quincena:
                # Si el día de pago NO coincide con las fechas de nómina (fecha_pago_1 o fecha_pago_2),
                # entonces es un ingreso especial (como aguinaldo)
                if dia_pago_ing != fecha_pago_1 and dia_pago_ing != fecha_pago_2:
                    # Es un ingreso anual/especial (aguinaldo)
                    # El aguinaldo NO se usa en la quincena que se recibe, sino en la SIGUIENTE
                    # Por lo tanto, NO lo sumamos aquí (se sumará cuando sea i+1)
                    pass
                else:
                    # Es una nómina regular (día 10 o 25) - aplicar siempre
                    ingresos_quincena += ing[1]

            # AGUINALDO: Si el aguinaldo se recibió en la quincena ANTERIOR, sumarlo AHORA
            # Verificar si fecha_pago_ing cae en la quincena anterior
            if dia_pago_ing != fecha_pago_1 and dia_pago_ing != fecha_pago_2:
                # Calcular la quincena anterior
                if i > 0:  # Solo si no es la primera quincena
                    # La quincena anterior terminó justo antes de esta
                    fecha_fin_anterior = fecha_inicio_quincena - relativedelta(days=1)
                    fecha_inicio_anterior = fecha_fin_anterior - relativedelta(days=14)  # Aproximadamente 15 días atrás

                    # Reconstruir fecha de pago en la quincena anterior
                    if dia_inicio > dia_fin:
                        if dia_pago_ing >= dia_inicio:
                            try:
                                fecha_pago_anterior = datetime(fecha_inicio_anterior.year, fecha_inicio_anterior.month, dia_pago_ing)
                            except ValueError:
                                fecha_pago_anterior = datetime(fecha_inicio_anterior.year, fecha_inicio_anterior.month, 1) + relativedelta(months=1, days=-1)
                        else:
                            try:
                                fecha_pago_anterior = datetime(fecha_fin_anterior.year, fecha_fin_anterior.month, dia_pago_ing)
                            except ValueError:
                                fecha_pago_anterior = datetime(fecha_fin_anterior.year, fecha_fin_anterior.month, 1) + relativedelta(months=1, days=-1)
                    else:
                        try:
                            fecha_pago_anterior = datetime(fecha_inicio_anterior.year, fecha_inicio_anterior.month, dia_pago_ing)
                        except ValueError:
                            fecha_pago_anterior = datetime(fecha_inicio_anterior.year, fecha_inicio_anterior.month, 1) + relativedelta(months=1, days=-1)

                    # Si el aguinaldo cayó en la quincena anterior, sumarlo ahora
                    mes_inicio_ingreso = fecha_inicio_ing.month
                    if fecha_inicio_anterior <= fecha_pago_anterior <= fecha_fin_anterior:
                        if fecha_pago_anterior.month == mes_inicio_ingreso:
                            ingresos_quincena += ing[1]

        # Calcular GASTOS de la quincena
        pago_prestamos = 0
        for prestamo in prestamos:
            dia_pago_prestamo = prestamo[2]
            fecha_inicio_prestamo = parse_fecha(prestamo[3])
            fecha_fin_prestamo = parse_fecha(prestamo[4])

            # Verificar si el préstamo está activo en esta quincena
            if not (fecha_inicio_prestamo <= fecha_fin_quincena and fecha_fin_prestamo >= fecha_inicio_quincena):
                continue

            # Construir la fecha EXACTA de pago para esta quincena
            if dia_inicio > dia_fin:
                # Quincena cruza meses
                if dia_pago_prestamo >= dia_inicio:
                    try:
                        fecha_pago_prestamo = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, dia_pago_prestamo)
                    except ValueError:
                        fecha_pago_prestamo = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, 1) + relativedelta(months=1, days=-1)
                else:
                    try:
                        fecha_pago_prestamo = datetime(fecha_fin_quincena.year, fecha_fin_quincena.month, dia_pago_prestamo)
                    except ValueError:
                        fecha_pago_prestamo = datetime(fecha_fin_quincena.year, fecha_fin_quincena.month, 1) + relativedelta(months=1, days=-1)
            else:
                # Quincena NO cruza meses
                try:
                    fecha_pago_prestamo = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, dia_pago_prestamo)
                except ValueError:
                    fecha_pago_prestamo = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, 1) + relativedelta(months=1, days=-1)

            # Verificar si la fecha de pago cae dentro del rango de esta quincena
            if fecha_inicio_quincena <= fecha_pago_prestamo <= fecha_fin_quincena:
                pago_prestamos += prestamo[1]

        # Calcular pagos de TARJETAS
        pago_tarjetas = 0

        # 1. Gastos corrientes (una sola vez, en la quincena que corresponde según fecha de pago)
        for tarjeta in tarjetas_corrientes:
            tarjeta_id = tarjeta[0]
            tarjeta_nombre = tarjeta[1]
            dia_pago_tarjeta = tarjeta[2]
            total_corriente = tarjeta[3]

            # Si ya pagamos esta tarjeta, skip
            if tarjeta_id in corrientes_ya_pagadas:
                continue

            # Verificar si esta tarjeta se paga en ESTA quincena
            # Para quincenas que cruzan meses (dia_inicio > dia_fin), el día debe ser >= dia_inicio O <= dia_fin
            # Para quincenas en el mismo mes (dia_inicio < dia_fin), el día debe estar entre dia_inicio y dia_fin
            pagar_en_esta_quincena = False
            if dia_inicio > dia_fin:
                # Quincena cruza el mes (ej: 25-9)
                if (dia_pago_tarjeta >= dia_inicio) or (dia_pago_tarjeta <= dia_fin):
                    pagar_en_esta_quincena = True
            else:
                # Quincena en el mismo mes (ej: 10-24)
                if dia_inicio <= dia_pago_tarjeta <= dia_fin:
                    pagar_en_esta_quincena = True

            if pagar_en_esta_quincena:
                pago_tarjetas += total_corriente
                corrientes_ya_pagadas.add(tarjeta_id)

        # 2. MSI (verificar si están activos en este mes específico)
        for msi in msi_list:
            tarjeta_id = msi[1]
            dia_pago_msi = msi[3]
            fecha_inicio_msi = parse_fecha(msi[4])
            meses_msi_total = msi[6]
            mensualidad = msi[7]
            meses_restantes = msi[8]

            # Primero construir la fecha EXACTA de pago en esta quincena
            if dia_inicio > dia_fin:
                if dia_pago_msi >= dia_inicio:
                    try:
                        fecha_pago_msi = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, dia_pago_msi)
                    except ValueError:
                        fecha_pago_msi = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, 1) + relativedelta(months=1, days=-1)
                else:
                    try:
                        fecha_pago_msi = datetime(fecha_fin_quincena.year, fecha_fin_quincena.month, dia_pago_msi)
                    except ValueError:
                        fecha_pago_msi = datetime(fecha_fin_quincena.year, fecha_fin_quincena.month, 1) + relativedelta(months=1, days=-1)
            else:
                try:
                    fecha_pago_msi = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, dia_pago_msi)
                except ValueError:
                    fecha_pago_msi = datetime(fecha_inicio_quincena.year, fecha_inicio_quincena.month, 1) + relativedelta(months=1, days=-1)

            # Verificar si el pago cae en esta quincena
            if fecha_inicio_quincena <= fecha_pago_msi <= fecha_fin_quincena:
                # Calcular cuántos meses han pasado desde que empezó el MSI hasta la fecha de pago
                meses_desde_inicio = (fecha_pago_msi.year - fecha_inicio_msi.year) * 12 + (fecha_pago_msi.month - fecha_inicio_msi.month)

                # Verificar si este MSI todavía está activo en este mes de pago
                if 0 <= meses_desde_inicio < meses_msi_total:
                    pago_tarjetas += mensualidad

        pago_total_quincena = pago_prestamos + pago_tarjetas

        # Actualizar saldo
        saldo_actual = saldo_actual + ingresos_quincena - pago_total_quincena

        # Determinar estado (semáforo)
        if balance_actual > 0:
            porcentaje_saldo = (saldo_actual / balance_actual) * 100
            if porcentaje_saldo >= 30:
                estado = "verde"
            elif porcentaje_saldo >= 5:
                estado = "amarillo"
            else:
                estado = "rojo"
        else:
            if saldo_actual > 1000:
                estado = "verde"
            elif saldo_actual > 0:
                estado = "amarillo"
            else:
                estado = "rojo"

        # Solo agregar quincenas FUTURAS (que aún no han empezado)
        if fecha_inicio_quincena > fecha_actual:
            proyeccion.append({
                'quincena': nombre_quincena,
                'fecha_inicio': fecha_inicio_quincena.strftime('%Y-%m-%d'),
                'fecha_fin': fecha_fin_quincena.strftime('%Y-%m-%d'),
                'ingresos': ingresos_quincena,
                'pagos': pago_total_quincena,
                'saldo_estimado': saldo_actual,
                'estado': estado
            })

        # Avanzar a la siguiente quincena
        # La siguiente quincena siempre empieza al día siguiente del fin de esta
        fecha_inicio_quincena = fecha_fin_quincena + relativedelta(days=1)

    return proyeccion


def calcular_quincenas_a_proyectar(min_quincenas=12):
    """
    Calculate how many biweekly periods to project based on last debt (MSI or loan)

    Args:
        min_quincenas: Minimum biweekly periods to project if no debts (default 12 = 6 months)

    Returns:
        int: Number of biweekly periods to project
    """
    conn = sqlite3.connect(Config.DATABASE_PATH)
    c = conn.cursor()

    fecha_actual = datetime.now()
    fecha_maxima = fecha_actual

    # Buscar última fecha de MSI
    c.execute('SELECT fecha_primera_mensualidad, meses_restantes FROM compras_msi WHERE activo=1 AND meses_restantes > 0')
    msis = c.fetchall()

    for msi in msis:
        fecha_primera = parse_fecha(msi[0])
        meses_restantes = msi[1]
        fecha_fin_msi = fecha_primera + relativedelta(months=meses_restantes)
        if fecha_fin_msi > fecha_maxima:
            fecha_maxima = fecha_fin_msi

    # Buscar última fecha de préstamos
    c.execute('SELECT fecha_fin FROM prestamos WHERE activo=1')
    prestamos = c.fetchall()

    for prestamo in prestamos:
        fecha_fin = parse_fecha(prestamo[0])
        if fecha_fin > fecha_maxima:
            fecha_maxima = fecha_fin

    conn.close()

    # Calcular diferencia en meses
    meses_diferencia = (fecha_maxima.year - fecha_actual.year) * 12 + (fecha_maxima.month - fecha_actual.month)

    # Convertir a quincenas (2 quincenas por mes) y agregar un buffer de 2 quincenas
    quincenas_necesarias = (meses_diferencia * 2) + 2

    # Retornar el máximo entre lo calculado y el mínimo
    return max(quincenas_necesarias, min_quincenas)
