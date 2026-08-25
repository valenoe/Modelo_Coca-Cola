"""
cargar_planificacion_real.py
Reemplaza en la BD la programacion MODELADA de junio, julio y agosto 2026 por
la programacion REAL que se envio (los Excel de la carpeta planning\).

Que toca:
  - programacion_mensual : borra y reinserta las rutas reales de cada mes.
    Es la tabla que alimenta la antiguedad (la cola circular del modelo).
  - saldo_inventario     : recalcula el saldo en cadena con los km reales,
    partiendo del saldo de mayo (mayo NO se toca).
  - registro_pago        : actualiza bono / pago_km / km_con_bono del mes.

Que NO toca:
  - mayo 2026 (estado inicial)
  - los auditores excluidos (por defecto Pablo Villarroel)
  - la tabla ruta, parametro_mes ni config

Nota: programacion_mensual tiene UNIQUE(id_auditor, anio, mes, id_ruta), asi que
una ruta repetida dentro del mismo mes (rutas partidas en dos dias) se guarda
una sola vez. No afecta el calculo: la antiguedad es la misma y los km se toman
del Excel, no de la tabla.

Uso:
    python app\cargar_planificacion_real.py                     # simulacion
    python app\cargar_planificacion_real.py --aplicar           # escribe en la BD
    python app\cargar_planificacion_real.py --aplicar --incluir-todos
"""

import sys
import os
import glob
import shutil
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ     = os.path.dirname(BASE_DIR)
DB_PATH  = os.path.join(BASE_DIR, "roble.db")
CARPETA  = os.path.join(RAIZ, "planning")

ANIO = 2026

# Auditores que se dejan como estan (se planifican a mano)
EXCLUIR_POR_DEFECTO = {"Pablo Villarroel"}

# Los km "extra" (filas sin dia asignado, tipo "Compra de Muestras") se suman
# al total del mes. Con --sin-extras se ignoran.
INCLUIR_EXTRAS = True

sys.path.insert(0, BASE_DIR)
from motor import calcular_km_con_bono
from lector_planificacion import MES_NOMBRE, norm, leer_planificacion


def asegurar_columna_dia(conn):
    """Agrega la columna 'dia' a programacion_mensual si no existe.

    La tabla original tenia UNIQUE(id_auditor, anio, mes, id_ruta), que impide
    guardar una ruta dos veces en el mismo mes. Como en las planificaciones
    reales hay rutas que se hacen en dos jornadas (partidas por ser muy largas),
    la restriccion pasa a ser UNIQUE(id_auditor, anio, mes, dia): una ruta por
    dia, y la misma ruta puede repetirse en dias distintos.

    SQLite no permite cambiar restricciones con ALTER TABLE, asi que se crea la
    tabla nueva, se copian las filas y se reemplaza.
    """
    cols = [r[1] for r in conn.execute("PRAGMA table_info(programacion_mensual)")]
    if "dia" in cols:
        return False

    conn.executescript("""
        CREATE TABLE programacion_mensual_nueva (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            id_auditor INTEGER NOT NULL,
            anio       INTEGER NOT NULL,
            mes        INTEGER NOT NULL,
            id_ruta    INTEGER NOT NULL,
            dia        INTEGER,
            UNIQUE(id_auditor, anio, mes, dia),
            FOREIGN KEY (id_auditor) REFERENCES auditor(id),
            FOREIGN KEY (id_ruta)    REFERENCES ruta(id)
        );

        INSERT INTO programacion_mensual_nueva (id_auditor, anio, mes, id_ruta, dia)
            SELECT id_auditor, anio, mes, id_ruta, NULL FROM programacion_mensual;

        DROP TABLE programacion_mensual;
        ALTER TABLE programacion_mensual_nueva RENAME TO programacion_mensual;
    """)
    conn.commit()
    return True


def main():
    aplicar  = "--aplicar" in sys.argv
    excluir  = set() if "--incluir-todos" in sys.argv else set(EXCLUIR_POR_DEFECTO)
    con_extras = INCLUIR_EXTRAS and "--sin-extras" not in sys.argv

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    auditores = {r["nombre"]: r["id"] for r in c.execute("SELECT id, nombre FROM auditor")}
    rutas = {}
    for r in c.execute("""SELECT r.id, r.nombre, a.nombre AS aud
                          FROM ruta r JOIN auditor a ON a.id = r.id_auditor"""):
        rutas.setdefault(r["aud"], {})[norm(r["nombre"])] = r["id"]

    # ── Leer las planificaciones ──────────────────────────────
    planes, extras_mes = {}, {}
    for p in sorted(glob.glob(os.path.join(CARPETA, "*.xlsx"))):
        base = os.path.basename(p)
        if base.startswith("~$") or "Comparacion" in base:
            continue   # ~$ = temporal que crea Excel al tener el archivo abierto
        mes, plan, extras = leer_planificacion(p)
        if mes and mes not in planes:
            planes[mes] = plan
            extras_mes[mes] = extras
            print(f"  {os.path.basename(p):<45} -> {MES_NOMBRE[mes]}")

    meses = sorted(planes)
    if not meses:
        print(f"No se encontraron planificaciones en {CARPETA}")
        sys.exit(1)

    print(f"\nMeses a reemplazar: {', '.join(MES_NOMBRE[m] for m in meses)}")
    print(f"Auditores excluidos: {', '.join(sorted(excluir)) or '(ninguno)'}")

    # ── Precio de bencina de cada mes ─────────────────────────
    precios = {}
    for m in meses:
        r = c.execute("SELECT precio_bencina FROM parametro_mes WHERE anio=? AND mes=?",
                      (ANIO, m)).fetchone()
        if not r or not r["precio_bencina"]:
            print(f"\nFalta el precio de bencina de {MES_NOMBRE[m]} en parametro_mes.")
            sys.exit(1)
        precios[m] = r["precio_bencina"]
    print("Precios: " + " | ".join(f"{MES_NOMBRE[m]} ${precios[m]:,.0f}" for m in meses))

    # ── Calcular ──────────────────────────────────────────────
    nombres = sorted(a for a in auditores if a in
                     {x for m in meses for x in planes[m]} and a not in excluir)

    cambios = []
    for nombre in nombres:
        id_a = auditores[nombre]

        # Saldo del ultimo mes anterior al horizonte (normalmente mayo)
        r = c.execute("""SELECT anio, mes, saldo FROM saldo_inventario
                         WHERE id_auditor=? AND (anio*100+mes) < ?
                         ORDER BY (anio*100+mes) DESC LIMIT 1""",
                      (id_a, ANIO * 100 + meses[0])).fetchone()
        saldo = r["saldo"] if r else 0.0
        origen = f"{MES_NOMBRE[r['mes']]} {r['anio']}" if r else "cero"

        filas = []
        for m in meses:
            asign = planes[m].get(nombre, [])
            if not asign:
                continue

            km_rutas  = sum(km for _dia, _n, km in asign)
            lista_ex  = extras_mes.get(m, {}).get(nombre, []) if con_extras else []
            km_extras = sum(km for _, km in lista_ex)
            km_reales = km_rutas + km_extras

            res, *_ = calcular_km_con_bono(ANIO, m, precios[m])
            v = res[id_a]
            km_con_bono = v["km_con_bono"]

            saldo_ant = saldo
            saldo = saldo + km_con_bono - km_reales

            # Rutas -> (dia, id_ruta). Las que no estan en el catalogo se descartan.
            # Se guarda una fila por dia, asi una ruta partida en dos jornadas
            # queda registrada las dos veces.
            cat = rutas.get(nombre, {})
            asignados, sin_id = [], []
            for dia, n, _km in asign:
                rid = cat.get(norm(n))
                (asignados.append((dia, rid)) if rid else sin_id.append(n))
            repetidas = len(asignados) - len({rid for _d, rid in asignados})

            # Saldo que hay hoy en la BD, para comparar
            r_old = c.execute("""SELECT km_rutas, saldo FROM saldo_inventario
                                 WHERE id_auditor=? AND anio=? AND mes=?""",
                              (id_a, ANIO, m)).fetchone()

            filas.append({
                "mes": m, "dias": len(asign), "km_reales": km_reales,
                "km_rutas": km_rutas, "extras": lista_ex, "km_extras": km_extras,
                "km_con_bono": km_con_bono, "saldo_ant": saldo_ant, "saldo": saldo,
                "asignados": asignados, "repetidas": repetidas,
                "sin_id": sin_id, "bono": v["bono"], "pago_km": v["pago_km"],
                "km_old": r_old["km_rutas"] if r_old else None,
                "saldo_old": r_old["saldo"] if r_old else None,
            })

        cambios.append({"nombre": nombre, "id": id_a, "origen": origen, "filas": filas})

    # ── Reporte ───────────────────────────────────────────────
    print("\n" + "=" * 92)
    print(f"  {'Auditor / mes':<26} {'Dias':>5} {'Km real':>9} {'Km BD':>9} "
          f"{'Tope':>9} {'Saldo nuevo':>13} {'Saldo BD':>11}")
    print("=" * 92)
    for ch in cambios:
        print(f"\n  {ch['nombre']}  (parte del saldo de {ch['origen']})")
        for f in ch["filas"]:
            km_old   = f"{f['km_old']:,.0f}"   if f["km_old"]   is not None else "—"
            saldo_old = f"{f['saldo_old']:+,.0f}" if f["saldo_old"] is not None else "—"
            print(f"  {'  ' + MES_NOMBRE[f['mes']]:<26} {f['dias']:>5} "
                  f"{f['km_reales']:>9,.0f} {km_old:>9} {f['km_con_bono']:>9,.0f} "
                  f"{f['saldo']:>+13,.0f} {saldo_old:>11}")
            for concepto, km in f["extras"]:
                print(f"      · extra: {concepto} — {km:,.0f} km "
                      f"({f['km_rutas']:,.0f} de rutas + {km:,.0f} = {f['km_reales']:,.0f})")
            if f["repetidas"]:
                print(f"      · {f['repetidas']} ruta(s) hecha(s) en dos jornadas — se guardan ambas, con su dia")
            if f["sin_id"]:
                print(f"      · {len(f['sin_id'])} ruta(s) sin equivalente en el catalogo, no se guardan:")
                for n in sorted(set(f["sin_id"])):
                    print(f"          - {n}")
    print("\n" + "=" * 92)

    if not aplicar:
        print("\nSIMULACION — no se escribio nada en la BD.")
        print("Para aplicarlo de verdad:  python app\\cargar_planificacion_real.py --aplicar")
        conn.close()
        return

    # ── Aplicar ───────────────────────────────────────────────
    respaldo = os.path.join(BASE_DIR, "roble_backup_pre_carga_real.db")
    shutil.copy2(DB_PATH, respaldo)
    print(f"\nRespaldo de la BD: {os.path.basename(respaldo)}")

    if asegurar_columna_dia(conn):
        print("Tabla programacion_mensual migrada: ahora guarda el dia de cada ruta.")

    for ch in cambios:
        id_a = ch["id"]
        for f in ch["filas"]:
            m = f["mes"]
            c.execute("DELETE FROM programacion_mensual WHERE id_auditor=? AND anio=? AND mes=?",
                      (id_a, ANIO, m))
            for dia, rid in f["asignados"]:
                c.execute("""INSERT OR REPLACE INTO programacion_mensual
                             (id_auditor, anio, mes, id_ruta, dia) VALUES (?,?,?,?,?)""",
                          (id_a, ANIO, m, rid, dia))
            c.execute("""INSERT OR REPLACE INTO saldo_inventario
                         (id_auditor, anio, mes, km_con_bono, km_rutas, saldo)
                         VALUES (?,?,?,?,?,?)""",
                      (id_a, ANIO, m, f["km_con_bono"], f["km_reales"], f["saldo"]))
            c.execute("""INSERT OR REPLACE INTO registro_pago
                         (id_auditor, anio, mes, bono, pago_km, km_con_bono)
                         VALUES (?,?,?,?,?,?)""",
                      (id_a, ANIO, m, f["bono"], f["pago_km"], f["km_con_bono"]))

    conn.commit()
    conn.close()
    print("Aplicado. La BD quedo con la programacion real.")


if __name__ == "__main__":
    main()
