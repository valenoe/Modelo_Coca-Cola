"""
probar_semestre.py
Planifica junio a septiembre 2026 con horizonte completo.
Saldo inicial = 0, saldo final = 0.

Uso:
    python app\probar_semestre.py <precio_bencina>
    python app\probar_semestre.py <precio_bencina> > resultado.txt
"""

import sys
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.stdout.reconfigure(encoding='utf-8')

from motor import (calcular_km_con_bono, planificar_horizonte,
                   guardar_programacion, inicializar_tabla_saldo)

DB_PATH = os.path.join(BASE_DIR, "roble.db")

MESES_CONFIG = [
    (8, 21),   # (mes, dias_habiles) — Agosto 2026 (feriado 15-ago cae sábado)
]

MESES_NOMBRE = {6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre"}
ANIO = 2026
SEP  = "=" * 75
SEP2 = "-" * 75


def limpiar_programacion():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for mes, _ in MESES_CONFIG:
        c.execute("DELETE FROM programacion_mensual WHERE anio=? AND mes=?", (ANIO, mes))
        c.execute("DELETE FROM saldo_inventario WHERE anio=? AND mes=?", (ANIO, mes))
        c.execute("DELETE FROM registro_pago WHERE anio=? AND mes=?", (ANIO, mes))
        c.execute("DELETE FROM parametro_mes WHERE anio=? AND mes=?", (ANIO, mes))
    conn.commit()
    conn.close()


def main():
    if len(sys.argv) < 2:
        print(r"Uso: python app\probar_semestre.py <precio_bencina>")
        sys.exit(1)

    precio = float(sys.argv[1])
    inicializar_tabla_saldo()
    limpiar_programacion()

    print(SEP)
    print(f"  Planificacion Junio-Septiembre {ANIO} | Bencina: ${precio:,.0f}/litro")
    print(f"  Saldo inicial = 0 | Saldo final = 0")
    print(SEP)

    # Obtener auditores activos
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    auditores = [dict(r) for r in conn.execute("SELECT * FROM auditor WHERE activo=1")]
    conn.close()

    resumen = {}

    for aud in auditores:
        id_a   = aud["id"]
        nombre = aud["nombre"]

        # Calcular km_con_bono para cada mes del horizonte
        meses_con_km = []
        for mes, dias in MESES_CONFIG:
            resultados, *_ = calcular_km_con_bono(ANIO, mes, precio)
            v = resultados.get(id_a)
            if not v:
                continue
            meses_con_km.append((mes, dias, v["km_con_bono"]))

        # Planificar horizonte completo
        plan, saldos, error = planificar_horizonte(id_a, ANIO, meses_con_km, precio)

        print(f"\n{SEP2}")
        print(f"  {nombre}")
        print(SEP2)

        if error:
            print(f"  ERROR: {error}")
            continue

        resumen[nombre] = []

        for mes, dias, km_con_bono in meses_con_km:
            rutas    = plan[mes]
            km_rutas = saldos[mes]["km_rutas"]
            saldo    = saldos[mes]["saldo"]

            resumen[nombre].append(saldo)

            # Obtener bono y pago_km del mes
            resultados, *_ = calcular_km_con_bono(ANIO, mes, precio)
            v = resultados[id_a]

            # Guardar en BD
            guardar_programacion(
                id_a, ANIO, mes, rutas,
                v["bono"], v["pago_km"], km_con_bono, saldo,
                precio, dias
            )

            print(f"\n  {MESES_NOMBRE[mes]} -- {dias} dias | Km bono: {km_con_bono:,.0f} | Km rutas: {km_rutas:,.0f} | Saldo: {saldo:+,.0f}")
            for r in sorted(rutas, key=lambda r: r["distancia_km"]):
                print(f"    {r['nombre']:<40} {r['distancia_km']:>5} km")

    # Tabla resumen
    print(f"\n\n{SEP}")
    print(f"  RESUMEN DE SALDOS")
    print(SEP)
    print(f"  {'Auditor':<22} {'Junio':>10} {'Julio':>10} {'Agosto':>10} {'Sept.':>12}")
    print(f"  {SEP2}")
    for nombre, saldos_lista in resumen.items():
        vals = [f"{s:+,.0f}" for s in saldos_lista]
        while len(vals) < 4:
            vals.append("-")
        print(f"  {nombre:<22} {vals[0]:>10} {vals[1]:>10} {vals[2]:>10} {vals[3]:>12}")
    print(SEP)


if __name__ == "__main__":
    main()