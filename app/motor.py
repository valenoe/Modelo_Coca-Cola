"""
motor.py
Motor de cálculo del sistema de rutas.
Implementa:
  - Sección 7: cálculo de Km_con_bono por auditor
  - Sección 9: modelo de inventario con cola circular por antigüedad
    * Resuelve mes a mes con PuLP
    * Actualiza antigüedad después de cada mes
    * Saldo inicial = 0, saldo final >= 0
"""

import sqlite3
import os
from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpBinary, LpStatus, PULP_CBC_CMD

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "roble.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_tabla_saldo():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saldo_inventario (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            id_auditor  INTEGER NOT NULL,
            anio        INTEGER NOT NULL,
            mes         INTEGER NOT NULL,
            km_con_bono REAL,
            km_rutas    REAL,
            saldo       REAL,
            UNIQUE(id_auditor, anio, mes),
            FOREIGN KEY (id_auditor) REFERENCES auditor(id)
        )
    """)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# SECCIÓN 7: Cálculo de Km_con_bono
# ─────────────────────────────────────────────────────────────

def calcular_km_con_bono(anio, mes, precio_bencina_actual):
    conn = get_db()
    c    = conn.cursor()

    cfg   = {r["clave"]: float(r["valor"]) for r in c.execute("SELECT clave, valor FROM config")}
    T     = cfg["tarifa_actual"]
    T_ant = cfg["tarifa_anterior"]
    P_ant = cfg["precio_bencina_anterior"]
    P_act = precio_bencina_actual

    def get_presupuesto(a, m):
        r = c.execute(
            "SELECT presupuesto_total FROM presupuesto_anual WHERE anio=? AND mes=?", (a, m)
        ).fetchone()
        if not r:
            raise ValueError(f"No hay presupuesto cargado para {a}/mes {m}")
        return r["presupuesto_total"]

    M20_ant = get_presupuesto(anio - 1, mes)
    M20_act = get_presupuesto(anio, mes)

    r = c.execute(
        "SELECT SUM(km_realizados) FROM historial_km WHERE anio=? AND mes=?", (anio - 1, mes)
    ).fetchone()
    M14_ant = r[0]
    M14_act = (M20_act / M20_ant) * M14_ant

    todos = c.execute("SELECT * FROM auditor").fetchall()

    parciales = {}
    for aud in todos:
        id_a = aud["id"]
        h = c.execute("""
            SELECT km_realizados FROM historial_km
            WHERE id_auditor=? AND anio=? AND mes=?
        """, (id_a, anio - 1, mes)).fetchone()
        if not h:
            parciales[id_a] = None
            continue

        G14_ant = h["km_realizados"]
        G14_act = (G14_ant / M14_ant) * M14_act
        G15     = (M20_act / (T * M14_act)) * G14_act
        G18     = G15 / aud["km_por_litro"]
        G19     = G18 * (P_act - P_ant)
        G20     = G14_act * T_ant
        G21     = G20 - G19
        G22     = G21 + G19

        parciales[id_a] = {
            "nombre":  aud["nombre"],
            "activo":  aud["activo"],
            "G14_ant": G14_ant,
            "G14_act": G14_act,
            "G15":     G15,
            "G18":     G18,
            "G19":     G19,
            "G20":     G20,
            "G21":     G21,
            "G22":     G22,
        }

    M21 = sum(v["G21"] for v in parciales.values() if v)
    M15 = sum(v["G15"] for v in parciales.values() if v)

    resultados = {}
    for id_a, v in parciales.items():
        if not v:
            continue
        km_con_bono   = (M21 / (T * M15)) * v["G15"]
        diferencia_km = v["G14_act"] - km_con_bono
        resultados[id_a] = {
            "nombre":        v["nombre"],
            "activo":        v["activo"],
            "G14_ant":       v["G14_ant"],
            "G14_act":       v["G14_act"],
            "G15":           v["G15"],
            "G18":           v["G18"],
            "G19":           v["G19"],
            "G20":           v["G20"],
            "G21":           v["G21"],
            "G22":           v["G22"],
            "km_con_bono":   km_con_bono,
            "diferencia_km": diferencia_km,
            "bono":          v["G19"],
            "pago_km":       v["G22"],
        }

    conn.close()
    return resultados, M21, M15, M14_act


# ─────────────────────────────────────────────────────────────
# SECCIÓN 9: Cola circular con PuLP mes a mes
# ─────────────────────────────────────────────────────────────

def _resolver_mes(rutas, dias_habiles, km_con_bono, saldo_anterior):
    """
    Resuelve la selección de rutas para un mes usando PuLP.

    Maximiza antigüedad (con desempate por km) respetando siempre el
    límite acumulado. El saldo se arrastra mes a mes y nunca es negativo.

    Si es el último mes: el saldo final queda entre 0 y 10% del km_con_bono
    para no acumular excedente hacia meses desconocidos.

    rutas: lista de dicts con id, nombre, distancia_km, antiguedad
    Retorna: (rutas_seleccionadas, km_total)

    El tope es un límite BLANDO:
      1) Primero se intenta respetar el tope (km <= saldo + km_con_bono*1.10).
      2) Si no hay solución factible dentro del tope (las rutas son demasiado
         largas para el presupuesto del mes), se relaja: se eligen las 22 rutas
         más vencidas minimizando el exceso de km. Ese exceso queda como saldo
         negativo (deuda) que se arrastra al mes siguiente.
    """
    def resolver(con_cap, km_signo):
        prob = LpProblem("mes", LpMaximize)
        x    = {r["id"]: LpVariable(f"x_{r['id']}", cat=LpBinary) for r in rutas}

        # Objetivo: maximizar antigüedad (domina por el factor 10000);
        # el km solo desempata. Con tope: rutas más largas primero (llena el
        # presupuesto). Sin tope: rutas más cortas (minimiza la deuda).
        prob += lpSum((r["antiguedad"] * 10000 + km_signo * r["distancia_km"]) * x[r["id"]] for r in rutas)

        # Restricción: exactamente dias_habiles rutas
        prob += lpSum(x[r["id"]] for r in rutas) == dias_habiles

        # Restricción de tope (solo en el intento 1)
        if con_cap:
            prob += lpSum(r["distancia_km"] * x[r["id"]] for r in rutas) <= saldo_anterior + km_con_bono * 1.10

        prob.solve(PULP_CBC_CMD(msg=0))
        return prob, x

    # 1) Dentro del tope (desempate: rutas más largas primero)
    prob, x = resolver(con_cap=True, km_signo=1)

    # 2) Si no entra, relajar el tope (desempate: rutas más cortas, menos deuda)
    if LpStatus[prob.status] != "Optimal":
        prob, x = resolver(con_cap=False, km_signo=-1)
        if LpStatus[prob.status] != "Optimal":
            return None, None

    seleccionadas = [r for r in rutas if x[r["id"]].value() and x[r["id"]].value() > 0.5]
    km_total      = sum(r["distancia_km"] for r in seleccionadas)
    return seleccionadas, km_total


def planificar_horizonte(id_auditor, anio, meses_config, precio_bencina):
    """
    Planifica rutas mes a mes con cola circular por antigüedad.

    meses_config: lista de (mes, dias_habiles, km_con_bono)
    
    Lógica:
    - Cada mes resuelve con PuLP maximizando antigüedad
    - Después de cada mes actualiza antigüedad (rutas usadas van al final)
    - El último mes cierra el saldo en 0

    Retorna:
      plan:   {mes: [rutas]}
      saldos: {mes: {km_con_bono, km_rutas, saldo}}
      error:  mensaje si falla, None si ok
    """
    conn = get_db()
    c    = conn.cursor()

    # Cargar rutas con antigüedad inicial
    rutas_bd = c.execute("""
        SELECT r.id, r.nombre, r.distancia_km,
               COALESCE(MAX(p.anio * 100 + p.mes), 0) AS ultimo_mes
        FROM ruta r
        LEFT JOIN programacion_mensual p
               ON p.id_ruta = r.id AND p.id_auditor = ?
        WHERE r.id_auditor = ?
        GROUP BY r.id
    """, (id_auditor, id_auditor)).fetchall()

    # Saldo acumulado del último mes guardado antes del horizonte.
    # Cada corrida continúa la deuda/excedente de meses previos en vez de partir de 0.
    primer_mes    = meses_config[0][0] if meses_config else 0
    saldo_inicial = 0.0
    if primer_mes:
        row_saldo = c.execute("""
            SELECT saldo FROM saldo_inventario
            WHERE id_auditor = ? AND (anio * 100 + mes) < ?
            ORDER BY (anio * 100 + mes) DESC
            LIMIT 1
        """, (id_auditor, anio * 100 + primer_mes)).fetchone()
        if row_saldo:
            saldo_inicial = row_saldo["saldo"]
    conn.close()

    # Estado de antigüedad: {id_ruta: ultimo_mes_asignado}
    # Menor valor = más antigua = mayor prioridad
    estado = {r["id"]: r["ultimo_mes"] for r in rutas_bd}
    rutas  = [dict(r) for r in rutas_bd]

    plan    = {}
    saldos  = {}
    saldo   = saldo_inicial

    for mes, dias_habiles, km_con_bono in meses_config:

        # Actualizar antigüedad en las rutas según estado actual
        mes_ref = anio * 100 + mes
        for r in rutas:
            r["antiguedad"] = mes_ref - estado[r["id"]]

        seleccionadas, km_total = _resolver_mes(
            rutas, dias_habiles, km_con_bono, saldo
        )

        if seleccionadas is None:
            return None, None, f"No hay solucion factible para {mes}/{anio}."

        # Actualizar estado de antigüedad — rutas usadas este mes
        # reciben como ultimo_mes el mes actual (van al final de la cola)
        for r in seleccionadas:
            estado[r["id"]] = mes_ref

        # Calcular saldo
        saldo = saldo + km_con_bono - km_total
        plan[mes]    = seleccionadas
        saldos[mes]  = {
            "km_con_bono": km_con_bono,
            "km_rutas":    km_total,
            "saldo":       saldo,
        }

    return plan, saldos, None


# ─────────────────────────────────────────────────────────────
# GUARDAR PROGRAMACIÓN EN LA BD
# ─────────────────────────────────────────────────────────────

def guardar_programacion(id_auditor, anio, mes, rutas_seleccionadas,
                         bono, pago_km, km_con_bono, saldo,
                         precio_bencina, dias_habiles):
    conn = get_db()
    c    = conn.cursor()

    c.execute("""
        INSERT OR IGNORE INTO parametro_mes (anio, mes, precio_bencina, dias_habiles)
        VALUES (?, ?, ?, ?)
    """, (anio, mes, precio_bencina, dias_habiles))

    for ruta in rutas_seleccionadas:
        c.execute("""
            INSERT OR REPLACE INTO programacion_mensual (id_auditor, anio, mes, id_ruta)
            VALUES (?, ?, ?, ?)
        """, (id_auditor, anio, mes, ruta["id"]))

    c.execute("""
        INSERT OR REPLACE INTO registro_pago (id_auditor, anio, mes, bono, pago_km, km_con_bono)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (id_auditor, anio, mes, bono, pago_km, km_con_bono))

    km_rutas = sum(r["distancia_km"] for r in rutas_seleccionadas)
    c.execute("""
        INSERT OR REPLACE INTO saldo_inventario
            (id_auditor, anio, mes, km_con_bono, km_rutas, saldo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (id_auditor, anio, mes, km_con_bono, km_rutas, saldo))

    conn.commit()
    conn.close()