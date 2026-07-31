# HANDOFF — Modelo Coca-Cola / Planificación de rutas de auditores

> Documento de traspaso. Última sesión de trabajo real: **29 de mayo de 2026**.
> Generado el 27 de junio de 2026 para no perder el contexto.

---

## 1. Qué es el proyecto

Sistema de **planificación mensual de rutas para auditores** (cliente Coca-Cola, gestionado vía Prieto Correa).
Cada mes hay que asignar a cada auditor una ruta por día hábil, respetando:

1. **Cantidad exacta** de rutas = días hábiles del mes.
2. **Tope de km mensual** (`Km_con_bono`), que depende del presupuesto y del precio de la bencina.
3. **Frecuencia mínima** de visita por ruta.
4. **Prioridad por antigüedad**: las rutas más tiempo sin visitar van primero (cola circular).

Es un problema de **optimización combinatoria entera** (variante del *Bounded Knapsack* con restricción de cardinalidad). Se resuelve con **PuLP** (solver CBC).

Documentación matemática completa:
- [modelo_inventario_rutas_v2.md](modelo_inventario_rutas_v2.md) — "Informe N°2", definición formal del modelo.
- [informe_implementacion_3.md](informe_implementacion_3.md) — informe de implementación.

---

## 2. Arquitectura / archivos

Todo el código vive en [app/](app/).

| Archivo | Rol |
|---|---|
| [app/inicializar_bd.py](app/inicializar_bd.py) | Crea `roble.db` (SQLite) y la carga desde los Excel. Ejecutar **una sola vez** o cuando cambien las rutas. Contiene datos fijos: auditores, presupuestos 2025/2026, config. |
| [app/cargar_mayo.py](app/cargar_mayo.py) | Carga la programación de **mayo 2026** como estado inicial (para que la antigüedad arranque bien). Ejecutar una sola vez. Lee `28052026_PDR_Mayo.xlsx`. |
| [app/motor.py](app/motor.py) | **El núcleo.** Sección 7 (`calcular_km_con_bono`) y Sección 9 (`planificar_horizonte` + `_resolver_mes` con PuLP). |
| [app/calcular_limites.py](app/calcular_limites.py) | Utilidad: muestra el `Km_con_bono` de cada auditor para un precio/mes dado. |
| [app/probar_semestre.py](app/probar_semestre.py) | **Script principal de uso.** Corre la planificación del horizonte y la imprime + la guarda en BD. Salida a stdout → se redirige a `.txt`. |
| [app/generar_informe.py](app/generar_informe.py) | Toma un `.txt` de salida y genera el Excel final (`Planificacion_Junio_2026_N.xlsx`), una hoja por auditor con formato calendario. |
| [app/probar_greedy.py](app/probar_greedy.py) | ⚠️ **OBSOLETO / ROTO.** Importa `seleccionar_rutas` de motor.py, función que ya no existe (fue reemplazada por `planificar_horizonte`). No usar sin arreglar. |
| `app/roble.db` | Base de datos SQLite con todo el estado. |

### Insumos Excel (en app/)
- `Rutas__Kilometros_Auditores.xlsx` — catálogo de rutas y km por auditor.
- `_ABR26_Roble_Ajuste_KM_macros.xlsm` — histórico de km realizados (hoja "Resumen mensual").
- `28052026_PDR_Mayo.xlsx` — planificación de mayo (estado inicial).
- `24052026_Proyección_Presupuesto.v2.xlsx` — proyección de presupuesto.

---

## 3. Esquema de la base de datos (roble.db)

- **auditor** (id, nombre, ciudad, km_por_litro, activo)
- **ruta** (id, numero, nombre, distancia_km, id_auditor)
- **historial_km** (id_auditor, anio, mes, km_realizados) — histórico 2025
- **presupuesto_anual** (anio, mes, presupuesto_total)
- **parametro_mes** (anio, mes, precio_bencina, dias_habiles)
- **programacion_mensual** (id_auditor, anio, mes, id_ruta) — rutas asignadas
- **registro_pago** (id_auditor, anio, mes, bono, pago_km, km_con_bono)
- **saldo_inventario** (id_auditor, anio, mes, km_con_bono, km_rutas, saldo)
- **config** (clave, valor)

### Datos fijos clave (en inicializar_bd.py)
- **Auditores activos (5):** Carlos Acevedo (Talca, rend. 11), Samuel Inostroza (Curicó, 17), Cristian Lizama (San Fernando, 17), Pablo Villarroel (Talca, 12), Mauricio Picart (Talca, 15).
- **Inactivo:** Marco Contreras (Parral, 15) — se mantiene solo por su histórico, necesario para los cálculos.
- **Config:** tarifa_actual=140, tarifa_anterior=120, precio_bencina_anterior=1188, delta_frecuencia=2.
- **Presupuesto 2026:** ene 1.829.760 … may 1.978.340, y **jun–dic fijos en 1.812.100**.

---

## 4. Flujo de trabajo (cómo se usa)

```powershell
# (solo una vez, ya hecho) inicializar y cargar mayo
python app\inicializar_bd.py
python app\cargar_mayo.py

# 1. Correr la planificación → guarda en .txt
python app\probar_semestre.py 1583 > junio.txt

# 2. Generar el Excel final desde el .txt
python app\generar_informe.py junio.txt Planificacion_Junio_2026.xlsx
```

`probar_semestre.py` recibe **el precio de la bencina** como argumento. El mes/días hábiles
se configuran dentro del script en `MESES_CONFIG`.

---

## 5. Dónde quedó exactamente (29-may-2026)

- Se estaba iterando **solo sobre Junio 2026** (21 días hábiles). En
  [app/probar_semestre.py:24-28](app/probar_semestre.py#L24-L28) `MESES_CONFIG`
  tiene **julio y agosto comentados** — solo `(6, 21)` activo.
- **Última corrida buena:** [junio11.txt](junio11.txt), con bencina a **$1.583/litro**.
- **Último Excel generado:** [Planificacion_Junio_2026_5.xlsx](Planificacion_Junio_2026_5.xlsx).
- Había muchos `.txt` (junio.txt … junio11.txt) y 5 `Planificacion_Junio_2026*.xlsx`:
  son **iteraciones** probando precios/ajustes, no versiones distintas del modelo.
- Feriado de junio configurado en generar_informe.py: **29-jun (San Pedro y San Pablo)**.

### Resultado de la última corrida (junio11.txt, bencina $1.583)
Todos los auditores quedaron con **saldo NEGATIVO** en junio:

| Auditor | Km bono | Km rutas | Saldo |
|---|---|---|---|
| Carlos Acevedo | 1.446 | 1.589 | **−143** |
| Samuel Inostroza | 2.209 | 2.429 | **−220** |
| Cristian Lizama | 1.990 | 2.188 | **−198** |
| Pablo Villarroel | 1.400 | 1.540 | **−140** |
| Mauricio Picart | 1.465 | 1.611 | **−146** |

---

## 6. ⚠️ Punto pendiente / a revisar

**Los saldos salen negativos** porque el modelo obliga a asignar exactamente
`días_hábiles` rutas (21) pero permite excederse hasta el **10%** del tope
([app/motor.py:165-169](app/motor.py#L165-L169)). Cuando las rutas disponibles
suman más que el tope, se genera "deuda" de km que se arrastraría a meses siguientes.

Probablemente las tantas iteraciones de bencina eran para intentar cuadrar esto.
**Decisión pendiente:** ¿es aceptable el saldo negativo (deuda que se arrastra)?
¿O hay que ajustar el tope / la restricción / el precio de bencina?

> Ojo: el docstring de `planificar_horizonte` menciona "saldo final = 0" y un cierre
> del último mes, pero el código actual **no** fuerza el cierre a 0 — solo arrastra el saldo.

---

## 7. ⚠️ Estado de git (IMPORTANTE)

**Nada del código está commiteado.** Todos los `app/*.py`, los `.txt` y los `.xlsx`
están como *untracked*. El trabajo de mayo solo existe en disco, sin respaldo.

Pendiente recomendado:
- Hacer commit del código (`app/*.py`) para respaldarlo.
- Considerar un `.gitignore` para `env/`, `__pycache__/`, los `.txt` de iteración y
  los `.xlsx` generados (son salidas, no fuente).
- Limpiar los duplicados `junio2.txt`…`junio11.txt` dejando solo el bueno.

---

## 8. Próximos pasos sugeridos

1. Decidir qué hacer con los **saldos negativos** (sección 6).
2. Si junio está OK → **activar julio/agosto/sept** en `MESES_CONFIG` y correr el horizonte completo.
3. **Commitear** el código para respaldarlo (sección 7).
4. Limpiar archivos de iteración duplicados.
