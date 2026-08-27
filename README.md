# Modelo Coca-Cola — Planificación de Rutas de Auditores

Modelo de optimización que genera la planificación mensual de rutas de auditores para Prieto Correa / Coca-Cola. Dado un conjunto de auditores, un catálogo de rutas y un precio de bencina, calcula cuántos kilómetros puede recorrer cada auditor ese mes (`Km_con_bono`) y resuelve un MILP (PuLP/CBC) que asigna exactamente una ruta por día hábil, respetando tope de kilómetros, frecuencia mínima anual por ruta y prioridad por antigüedad.

El estado vive en una base SQLite (`app/roble.db`) y los insumos/salidas son archivos Excel. **Hoy el proyecto es 100% CLI** — no hay interfaz web ni ejecutable empaquetado.

## Estado actual

El plan original (`informe_implementacion_3.md`) contemplaba una interfaz Flask + empaquetado con PyInstaller para distribuir un `.exe`. Eso nunca se construyó: `static/` y `templates/` están vacías y Flask no está instalado. Todo se opera hoy corriendo scripts de Python a mano desde la terminal, editando parámetros directamente en el código (ver `MESES_CONFIG` más abajo). Ese es justamente el siguiente paso pendiente del proyecto.

## Estructura

| Carpeta | Contenido |
|---|---|
| `app/` | Código Python, base de datos SQLite (`roble.db`) y Excel de insumo (catálogo de rutas, histórico, planificación de mayo) |
| `planning/` | Planificaciones reales enviadas al cliente (Excel) y sus comparativos contra el catálogo de rutas |
| `results/` | Salidas de las corridas: `.txt` con el reporte de cada mes y `.xlsx` generados a partir de ellos |
| `static/`, `templates/` | Vacías — placeholder de la interfaz web nunca implementada |

## Setup

- Python 3.12
- No hay `requirements.txt`. Dependencias:
  ```powershell
  pip install pulp openpyxl
  ```
- `app/roble.db` es la base de datos SQLite que contiene el estado (auditores, rutas, programación, saldos). Está ignorada por git (`*.db` en `.gitignore`) y se comparte por Google Drive — no se reconstruye desde cero salvo que sea necesario.
- Si se necesita reinicializar la base desde cero, `app/inicializar_bd.py` espera el archivo `app/_ABR26_Roble_Ajuste_KM_macros.xlsm` (histórico de km 2025), que **no está incluido en el repo**.

## Cómo correr el modelo

Todos los comandos se ejecutan desde la raíz del repo, en PowerShell, con el entorno virtual activado.

**Setup inicial (una sola vez, si no existe `roble.db`):**
```powershell
python app\inicializar_bd.py
python app\cargar_mayo.py
```

**Cargar planificación real (después de `cargar_mayo`, para dejar la BD al día):**

Esto es lo que se corre cada vez que se quiere poblar/actualizar la base con los meses ya planificados (junio, julio, agosto...) a partir de los Excel en `planning/`, en vez de dejar que el modelo los genere. Es el paso obligado justo después de `cargar_mayo` cuando la BD se inicializa de nuevo.
```powershell
python app\comparar_planificaciones.py [carpeta] [salida.xlsx]
python app\cargar_planificacion_real.py                                # simulación, no escribe
python app\cargar_planificacion_real.py --aplicar                      # escribe en la BD
python app\cargar_planificacion_real.py --aplicar --incluir-todos
python app\cargar_planificacion_real.py --aplicar --sin-extras
```

**Corrida principal del modelo:**
```powershell
python app\probar_semestre.py <precio_bencina> > results\<mes>.txt
```
El mes y los días hábiles a planificar se editan a mano en `MESES_CONFIG` dentro de `app/probar_semestre.py` (no son argumentos de línea de comando).

**Generar el Excel calendario a partir del reporte:**
```powershell
python app\generar_informe.py results\<mes>.txt results\Planificacion_<Mes>_2026.xlsx
```

**Utilidades de consulta (cálculo de `Km_con_bono`, Sección 7):**
```powershell
python app\calcular_limites.py <precio_bencina> <mes> <anio>
python app\generar_limites_excel.py <precio_bencina> <mes> <anio> [salida.xlsx]
python app\generar_paso_a_paso.py <precio_bencina> <mes> <anio> [salida.xlsx]
```

**No usar:** `app/probar_greedy.py` está roto (importa una función que ya no existe en `motor.py`).

## Módulos principales (`app/`)

- `motor.py` — núcleo: cálculo de `Km_con_bono` y el MILP de asignación de rutas (PuLP/CBC).
- `probar_semestre.py` — orquestador de la corrida principal por consola.
- `inicializar_bd.py` — crea el esquema de la BD y carga auditores, rutas, histórico, presupuesto y config.
- `cargar_mayo.py` — carga la planificación de mayo 2026 como estado inicial de antigüedad.
- `lector_planificacion.py` — parser común de los Excel de `planning/`.
- `cargar_planificacion_real.py` — reemplaza el plan modelado por el plan real en la BD y recalcula saldos.
- `comparar_planificaciones.py` — cruza plan real vs catálogo de rutas.
- `generar_informe.py` — convierte el `.txt` de una corrida en el Excel calendario final.
- `calcular_limites.py`, `generar_limites_excel.py`, `generar_paso_a_paso.py` — distintas vistas del cálculo de `Km_con_bono`.

## Datos y salidas

- **Insumos:** `app/Rutas__Kilometros_Auditores.xlsx` (catálogo de rutas por auditor), `app/28052026_PDR_Mayo.xlsx` (planificación de mayo), archivos en `planning/` (planificaciones reales mensuales).
- **Salidas:** reportes de corrida en `results/*.txt`, Excel calendario y de límites en `results/*.xlsx`, comparativo en `planning/Comparacion_Rutas.xlsx`.

## Pendiente: empaquetar para instalar en otro computador

Hoy no existe `requirements.txt`, así que replicar el entorno en otra máquina es manual (instalar Python 3.12 y correr `pip install pulp openpyxl` a mano). Para dejarlo como "llegar e instalar":

- **Generar `requirements.txt`** desde el `.venv` actual: `pip freeze > requirements.txt` (o escribirlo a mano con `pulp==3.3.2` y `openpyxl==3.1.5`, que son las únicas dependencias reales). Así en la otra máquina alcanza con `pip install -r requirements.txt`.
- **Empaquetado real** (para que no dependa de tener Python instalado): esto es lo que ya proponía `informe_implementacion_3.md` con PyInstaller, pero nunca se hizo. Recomendación: evaluarlo recién cuando exista una interfaz (aunque sea mínima) sobre los scripts actuales, porque empaquetar puro CLI con `.venv` y BD en SQLite compartida por Drive no resuelve mucho por sí solo — el cuello de botella hoy es la falta de interfaz, no la instalación de Python.

No se implementa esto ahora, queda como nota para la siguiente etapa del proyecto.

## Documentación adicional

- [`modelo_inventario_rutas_v2.md`](modelo_inventario_rutas_v2.md) — formulación matemática completa del modelo (conjuntos, parámetros, restricciones, función objetivo, cálculo de `Km_con_bono`).
- [`informe_implementacion_3.md`](informe_implementacion_3.md) — plan de arquitectura original (stack, esquema de BD, presupuestos). La parte de interfaz/empaquetado no se implementó (ver "Estado actual").
- [`HANDOFF.md`](HANDOFF.md) — bitácora de traspaso de una sesión anterior. Contiene contexto útil sobre el modelo y los datos, pero algunas partes están desactualizadas (rutas de archivos de una versión anterior del repo, estado de `MESES_CONFIG`).
