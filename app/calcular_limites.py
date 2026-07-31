"""
calcular_limites.py
Muestra el Km_con_bono de cada auditor dado un precio de bencina y mes.

Uso:
    python app\calcular_limites.py <precio_bencina> <mes> <anio>

Ejemplo mayo 2026:
    python app\calcular_limites.py 1583 5 2026
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from motor import calcular_km_con_bono

def main():
    if len(sys.argv) < 4:
        print("Uso: python app\\calcular_limites.py <precio_bencina> <mes> <anio>")
        print("Ejemplo: python app\\calcular_limites.py 1583 5 2026")
        sys.exit(1)

    precio = float(sys.argv[1])
    mes    = int(sys.argv[2])
    anio   = int(sys.argv[3])

    MESES = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
             7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}

    print(f"\n{'='*60}")
    print(f"  Límites km — {MESES.get(mes, mes)} {anio} | Bencina: ${precio:,.0f}/litro")
    print(f"{'='*60}")
    print(f"\n  {'Auditor':<22} {'Km estimado':>12} {'Km con bono':>12} {'Bono':>12}")
    print(f"  {'-'*62}")

    resultados, M21, M15, M14_act = calcular_km_con_bono(anio, mes, precio)

    total_km_bono = 0
    for id_a, v in resultados.items():
        if not v:
            continue
        estado = "" if v["activo"] else " (inactivo)"
        print(f"  {v['nombre']:<22}{estado:<12} {v['G14_act']:>12,.0f} {v['km_con_bono']:>12,.0f} {v['bono']:>12,.0f}")
        if v["activo"]:
            total_km_bono += v["km_con_bono"]

    print(f"\n  Total km con bono (activos): {total_km_bono:,.0f} km")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()