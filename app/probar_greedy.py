"""
probar_greedy.py
Prueba la seleccion de rutas con modelo de inventario para un mes dado.

Uso:
    python app\probar_greedy.py <precio_bencina> <mes> <anio> <dias_habiles>

Ejemplo junio 2026:
    python app\probar_greedy.py 1583 6 2026 21
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from motor import calcular_km_con_bono, seleccionar_rutas, inicializar_tabla_saldo

MESES = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
         7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}

def main():
    if len(sys.argv) < 5:
        print(r"Uso: python app\probar_greedy.py <precio_bencina> <mes> <anio> <dias_habiles>")
        print(r"Ejemplo: python app\probar_greedy.py 1583 6 2026 21")
        sys.exit(1)

    precio       = float(sys.argv[1])
    mes          = int(sys.argv[2])
    anio         = int(sys.argv[3])
    dias_habiles = int(sys.argv[4])

    inicializar_tabla_saldo()

    print(f"\n{'='*65}")
    print(f"  Programacion {MESES.get(mes, mes)} {anio} | Bencina: ${precio:,.0f} | Dias habiles: {dias_habiles}")
    print(f"{'='*65}")

    resultados, M21, M15, M14_act = calcular_km_con_bono(anio, mes, precio)

    for id_a, v in resultados.items():
        if not v or not v["activo"]:
            continue

        km_con_bono = v["km_con_bono"]
        rutas, km_total, saldo_anterior, saldo = seleccionar_rutas(
            id_a, anio, mes, dias_habiles, km_con_bono
        )

        print(f"\n  {'─'*60}")
        print(f"  {v['nombre']}")
        print(f"  Km con bono: {km_con_bono:,.0f} | Saldo anterior: {saldo_anterior:,.0f}")
        print(f"  Rutas: {len(rutas)}/{dias_habiles} | Km rutas: {km_total:,.0f} | Saldo nuevo: {saldo:,.0f}")
        print(f"  {'─'*60}")
        for r in rutas:
            print(f"    {r['nombre']:<40} {r['distancia_km']:>5} km")

    print(f"\n{'='*65}\n")

if __name__ == "__main__":
    main()