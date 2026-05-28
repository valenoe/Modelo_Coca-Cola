# Sistema de Inventario de Rutas para Auditores

## Modelo de optimización combinatoria con variables binarias

---

# 1. Definición del problema

El sistema debe seleccionar rutas mensuales para cada auditor satisfaciendo simultáneamente cuatro criterios:

- cantidad exacta de rutas igual a los días hábiles del mes;
- suma de kilómetros dentro del límite mensual disponible (`Km_con_bono`);
- frecuencia mínima anual de visita por ruta;
- priorización por antigüedad (rutas más tiempo sin visitar tienen precedencia).

El problema pertenece a la clase de la **optimización combinatoria entera**, específicamente como una variante del _Bounded Knapsack Problem_ con restricción de cardinalidad y función objetivo de prioridad temporal.

---

# 2. Conjuntos

## Auditores

$$i \in A$$

Donde $A$ es el conjunto de todos los auditores activos del sistema.

---

## Rutas por auditor

$$j \in R_i$$

Donde $R_i$ es el conjunto de rutas asignadas al auditor $i$. Cada ruta pertenece a un único auditor.

---

## Meses del horizonte de planificación

$$m \in M = \{1, 2, \ldots, 12\}$$

El modelo opera mes a mes pero mantiene estado acumulado anual para la restricción de frecuencia mínima.

---

# 3. Parámetros

## Parámetros fijos por auditor

| Símbolo     | Descripción                                                               | Unidad   |
| ----------- | ------------------------------------------------------------------------- | -------- |
| $km_j$      | Distancia de la ruta $j$                                                  | km       |
| $r_i$       | Rendimiento del vehículo del auditor $i$                                  | km/litro |
| $SB_i$      | Sueldo base mensual del auditor $i$                                       | $        |
| $H_i^{m-1}$ | Kilómetros realizados por el auditor $i$ en el mismo mes del año anterior | km       |

---

## Parámetros variables mensuales

| Símbolo   | Descripción                                                    | Unidad  |
| --------- | -------------------------------------------------------------- | ------- |
| $P_m$     | Precio de la bencina en el mes $m$                             | $/litro |
| $D_{im}$  | Días hábiles efectivos del auditor $i$ en el mes $m$           | días    |
| $DT_{im}$ | Días efectivamente trabajados por el auditor $i$ en el mes $m$ | días    |

---

## Parámetros de estado (actualizados cada mes)

| Símbolo  | Descripción                                                                                                   |
| -------- | ------------------------------------------------------------------------------------------------------------- |
| $a_{jm}$ | Antigüedad de la ruta $j$ al inicio del mes $m$: cantidad de meses transcurridos desde su última programación |
| $v_{jm}$ | Visitas acumuladas a la ruta $j$ desde el inicio del año hasta el mes $m$                                     |
| $K_{im}$ | Límite mensual de kilómetros del auditor $i$ en el mes $m$ (`Km_con_bono`)                                    |

---

## Parámetro configurable

| Símbolo    | Descripción                                                                                         |
| ---------- | --------------------------------------------------------------------------------------------------- |
| $\delta_i$ | Ajuste a la baja aplicado al mínimo de rotaciones del auditor $i$ (configurable, típicamente 1 o 2) |

La frecuencia mínima anual **no es un parámetro fijo**: se calcula para cada auditor en función de su cantidad de rutas y los días hábiles del año:

$$f_{\min,i} = \left\lfloor \frac{D_{\text{año}}}{|R_i|} \right\rfloor - \delta_i$$

Donde:

- $D_{\text{año}}$ = total de días hábiles del año (aproximadamente 250);
- $|R_i|$ = cantidad de rutas asignadas al auditor $i$;
- $\delta_i$ = ajuste configurable que descuenta meses cortos por feriados, vacaciones u otros (típicamente 1 o 2).

**Ejemplo:** un auditor con 50 rutas y $\delta_i = 2$:

$$f_{\min,i} = \left\lfloor \frac{250}{50} \right\rfloor - 2 = 5 - 2 = 3 \text{ visitas mínimas al año por ruta}$$

Lo configurable es únicamente $\delta_i$; el resto se calcula automáticamente a partir de los datos del auditor.

---

# 4. Variable de decisión

La variable principal del modelo es **binaria**:

$$x_{ijm} = \begin{cases} 1 & \text{si la ruta } j \text{ es asignada al auditor } i \text{ en el mes } m \\ 0 & \text{en otro caso} \end{cases}$$

Para la planificación del mes actual $m^{\ast}$, se trabaja con la notación simplificada $x_{ij}$ entendiéndose que corresponde al mes en curso.

---

# 5. Restricciones del modelo

## 5.1 Restricción de cardinalidad (días hábiles)

Cada auditor debe realizar exactamente una ruta por día hábil del mes:

$$\sum_{j \in R_i} x_{ij} = D_{im^{\ast}} \quad \forall i \in A$$

Esta restricción es de igualdad estricta: ni más ni menos rutas que los días hábiles disponibles.

---

## 5.2 Restricción de capacidad (kilómetros)

La suma de kilómetros de las rutas seleccionadas no puede superar el límite mensual:

$$\sum_{j \in R_i} km_j \cdot x_{ij} \leq K_{im^{\ast}} \quad \forall i \in A$$

Donde $K_{im^{\ast}}$ corresponde al valor `Km_con_bono` calculado según el precio de bencina del mes.

---

## 5.3 Restricción de frecuencia mínima anual

Cada ruta debe alcanzar al menos $f_{\min}$ visitas durante el año:

$$\sum_{m=1}^{12} x_{ijm} \geq f_{\min} \quad \forall i \in A,\ \forall j \in R_i$$

Equivalentemente, usando el estado acumulado al mes $m^{\ast}$:

$$v_{jm^{\ast}} + \sum_{m=m^{\ast}}^{12} x_{ijm} \geq f_{\min} \quad \forall i \in A,\ \forall j \in R_i$$

Esta forma permite detectar anticipadamente si una ruta no alcanzará la frecuencia mínima en los meses restantes del año.

---

## 5.4 Restricción de integralidad

$$x_{ijm} \in \{0, 1\} \quad \forall i \in A,\ \forall j \in R_i,\ \forall m \in M$$

---

# 6. Función objetivo

## 6.1 Formulación base (prioridad por antigüedad)

El sistema maximiza la suma ponderada de antigüedad de las rutas seleccionadas:

$$\max \sum_{j \in R_i} a_{jm^{\ast}} \cdot x_{ij}$$

Esto asegura que las rutas que llevan más tiempo sin programarse sean seleccionadas primero.

---

## 6.2 Formulación extendida (antigüedad + urgencia de frecuencia)

Para incorporar también la urgencia de cumplimiento de frecuencia mínima, se define un término de incentivo por urgencia (o prioridad):

$$\max \sum_{j \in R_i} \left[ a_{jm^{\ast}} + \beta \cdot \max\left(0,\ f_{\min} - v_{jm^{\ast}} - (12 - m^{\ast} + 1)\right) \right] \cdot x_{ij}$$

Donde:

- $\beta > 0$ es un parámetro de peso que controla la importancia relativa de la urgencia de frecuencia frente a la antigüedad pura;
- el término $\max(0,\ f_{\min} - v_{jm^{\ast}} - (12 - m^{\ast} + 1))$ cuantifica el déficit de visitas que no puede recuperarse con los meses restantes del año.

Cuando $\beta = 0$, la función colapsa a la formulación base.

---

## 6.3 Interpretación combinada

| Componente                   | Efecto                                                               |
| ---------------------------- | -------------------------------------------------------------------- |
| $a_{jm^{\ast}}$              | Prioriza rutas con mayor tiempo sin visitar                          |
| $\beta \cdot \text{déficit}$ | Eleva la prioridad de rutas en riesgo de no cumplir frecuencia anual |
| Restricción 5.1              | Garantiza exactamente $D_{im^{\ast}}$ rutas seleccionadas            |
| Restricción 5.2              | Garantiza que no se supera el límite de km                           |
| Restricción 5.3              | Garantiza cumplimiento de frecuencia mínima a largo plazo            |

---

# 7. Cálculo del límite de kilómetros mensual (`Km_con_bono`)

El presupuesto de kilómetros parte del presupuesto total mensual definido para el año actual, distribuido entre auditores en proporción a lo que cada uno recorrió el mismo mes del año anterior. El objetivo es mantener el mismo gasto total anual: si la bencina sube, el auditor recorre menos kilómetros pero recibe un bono que compensa la diferencia.

## 7.1 Parámetros del cálculo

| Símbolo                 | Descripción                                                                               | Ejemplo (Enero) |
| ----------------------- | ----------------------------------------------------------------------------------------- | --------------- |
| $M_{20}^{m,2025}$       | Presupuesto total de todos los auditores en el mes $m$ del año anterior                   | $2.162.160      |
| $M_{20}^{m,2026}$       | Presupuesto total de todos los auditores en el mes $m$ del año actual (dato fijo por mes) | $1.829.760      |
| $M_{14}^{m,2025}$       | Km totales recorridos por todos los auditores en el mes $m$ del año anterior              | 18.018 km       |
| $M_{14}^{m,2026}$       | Km totales estimados para el mes $m$ del año actual (calculado)                           | 15.248 km       |
| $M_{15}^m$              | Km estimados totales mes $m$ año actual a tarifa $T$ (calculado)                          | 13.070 km       |
| $M_{21}^m$              | Presupuesto total mes $m$ año actual antes del bono (calculado)                           | $1.472.172      |
| $G_{14,i}^{2025}$       | Km recorridos por el auditor $i$ en el mes $m$ del año anterior                           | 2.183 km        |
| $G_{14,i}^{2026}$       | Km estimados para el auditor $i$ en el mes $m$ del año actual (calculado)                 | 2.183 km        |
| $r_i$                   | Rendimiento del vehículo del auditor $i$                                                  | 11 km/litro     |
| $T$                     | Tarifa interna vigente por km (año actual)                                                | $140            |
| $T_{\text{ant}}$        | Tarifa interna por km del año anterior                                                    | $120            |
| $P_{\text{actual}}^m$   | Precio de la bencina en el mes $m$ del año actual                                         | $1.583/litro    |
| $P_{\text{anterior}}^m$ | Precio de la bencina en el mes $m$ del año anterior                                       | $1.188/litro    |

---

## 7.2 Paso 0 — Km totales estimados año actual

A partir del nuevo presupuesto mensual total $M_{20}^{m,2026}$, se estiman los km totales del mes manteniendo la misma proporción que el año anterior:

$$M_{14}^{m,2026} = \frac{M_{20}^{m,2026}}{M_{20}^{m,2025}} \times M_{14}^{m,2025}$$

**Ejemplo enero:** $\frac{1.829.760}{2.162.160} \times 18.018 = 15.248$ km

---

## 7.3 Paso 1 — Km estimados por auditor año actual

Se distribuyen los km totales 2026 entre auditores en proporción a lo que cada uno recorrió el año anterior:

$$G_{14,i}^{2026} = \frac{G_{14,i}^{2025}}{M_{14}^{m,2025}} \times M_{14}^{m,2026}$$

**Ejemplo enero Carlos:** $\frac{2.580}{18.018} \times 15.248 = 2.183$ km

---

## 7.4 Paso 2 — Km estimados sin bono (a tarifa $T$)

$$G_{15,i} = \frac{M_{20}^{m,2026}}{T \cdot M_{14}^{m,2026}} \times G_{14,i}^{2026}$$

**Ejemplo enero Carlos:** $\frac{1.829.760}{140 \times 15.248} \times 2.183 = 1.871$ km

---

## 7.5 Paso 3 — Litros implícitos del auditor

Cantidad de litros que representan los km estimados según el rendimiento $r_i$ del vehículo:

$$G_{18,i} = \frac{G_{15,i}}{r_i}$$

**Ejemplo enero Carlos:** $\frac{1.871}{11} = 170$ litros

---

## 7.6 Paso 4 — Bono de estabilización

Compensación por el alza del precio de la bencina respecto al año anterior:

$$G_{19,i} = G_{18,i} \times \left( P_{\text{actual}}^m - P_{\text{anterior}}^m \right)$$

**Ejemplo enero Carlos:** $170 \times (1.583 - 1.188) = \$67.202$

---

## 7.7 Paso 5 — Pago del año actual base

$$G_{20,i} = G_{14,i}^{2026} \times T_{\text{ant}}$$

**Ejemplo enero Carlos:** $2.183 \times 120 = \$262.004$

---

## 7.8 Paso 6 — Pago año actual antes del bono

$$G_{21,i} = G_{20,i} - G_{19,i}$$

**Ejemplo enero Carlos:** $262.004 - 67.202 = \$194.801$

_Los valores $G_{21,i}$ de todos los auditores se suman para obtener $M_{21}^m$, y los $G_{15,i}$ para obtener $M_{15}^m$._

---

## 7.9 Paso 7 — Pago total año actual (con bono)

$$G_{22,i} = G_{21,i} + G_{19,i} = G_{20,i}$$

**Ejemplo enero Carlos:** $194.801 + 67.202 = \$262.004$

Propiedad clave del sistema: **el pago total por kilómetros se mantiene igual al año actual base**, independientemente del precio de la bencina. El bono no aumenta el gasto; solo redistribuye el presupuesto para absorber el alza.

---

## 7.10 Paso 8 — Km reales disponibles con bono (`Km_con_bono`)

Este es el límite efectivo $K_{im^{\ast}}$ que entra al modelo de optimización:

$$K_{im^{\ast}} = G_{16,i} = \frac{M_{21}^m}{T \cdot M_{15}^m} \times G_{15,i}$$

**Ejemplo enero Carlos:** $\frac{1.472.172}{140 \times 13.070} \times 1.871 = 1.506$ km

---

## 7.11 Paso 9 — Diferencia de km (registro histórico)

$$G_{17,i} = G_{14,i}^{2026} - G_{16,i}$$

**Ejemplo enero Carlos:** $2.183 - 1.506 = 678$ km

Este valor no afecta la optimización; se registra para seguimiento de la reducción de cobertura causada por el alza de bencina.

---

## 7.12 Ejemplo numérico completo — Enero 2026 (todos los auditores)

| Paso                           | Carlos    | Samuel    | Cristian  | Pablo     | Mauricio  |
| ------------------------------ | --------- | --------- | --------- | --------- | --------- |
| $G_{14}^{2026}$ (km est. 2026) | 2.183     | 2.678     | 3.071     | 1.907     | 3.157     |
| $G_{15}$ (valor 140)           | 1.871     | 2.295     | 2.632     | 1.635     | 2.706     |
| $G_{18}$ (litros)              | 170       | 135       | 155       | 136       | 180       |
| $G_{19}$ (bono)                | $67.202   | $53.327   | $61.164   | $53.818   | $71.267   |
| $G_{20}$ (pago base)           | $262.004  | $321.310  | $368.531  | $228.898  | $378.890  |
| $G_{21}$ (sin bono)            | $194.801  | $267.983  | $307.368  | $175.080  | $307.622  |
| $G_{22}$ (con bono)            | $262.004  | $321.310  | $368.531  | $228.898  | $378.890  |
| $K_{im^*}$ (**Km_con_bono**)   | **1.506** | **1.847** | **2.118** | **1.315** | **2.177** |
| $G_{17}$ (diferencia km)       | 678       | 831       | 953       | 592       | 980       |

**Totales globales enero 2026:**

- $M_{20}^{m,2026} = \$1.829.760$ (dato fijo de entrada)
- $M_{14}^{m,2026} = 15.248$ km
- $M_{15}^m = 13.070$ km
- $M_{21}^m = \$1.472.172$
- Bono total = $\$357.588$
- Km_con_bono total = **10.516 km**

> **Nota:** No se incluye Marco Contreras porque no está disponible, pero en los calculos internos si está presente.

---

# 8. Cálculo del pago mensual por auditor

El sistema calcula y entrega dos valores por auditor: el **pago por kilómetros (rutas)** y el **bono de estabilización**. El sueldo base y otros componentes son calculados externamente por el equipo administrativo.

---

## 8.1 Pago por kilómetros (rutas)

El pago por rutas resulta directamente del cálculo de la sección 7 y corresponde a $G_{22,i}$:

$$\text{Pago-km}_{im^{\ast}} = G_{22,i} = G_{20,i}$$

Esta igualdad es una propiedad garantizada del sistema: **el pago por rutas del año actual es siempre igual al pago base calculado sobre los km estimados 2026**, independientemente del precio de la bencina. El bono no aumenta el gasto; solo redistribuye el presupuesto internamente para absorber el alza.

**Ejemplo enero 2026 — Carlos Acevedo:**

$$\text{Pago-km} = G_{22} = \$262.004$$

---

## 8.2 Bono de estabilización

El bono corresponde a $G_{19,i}$, calculado en el Paso 4 de la sección 7. Se reporta por separado como componente informativo del pago:

$$\text{Bono}_{im^{\ast}} = G_{19,i} = G_{18,i} \times \left( P_{\text{actual}}^m - P_{\text{anterior}}^m \right)$$

**Ejemplo enero 2026 — Carlos Acevedo:**

$$\text{Bono} = 170 \times (1.583 - 1.188) = \$67.202$$

---

## 8.3 Resumen del informe mensual por auditor

El sistema entrega por cada auditor $i$ en el mes $m$:

| Concepto                      | Símbolo           | Ejemplo (Carlos, Enero 2026) |
| ----------------------------- | ----------------- | ---------------------------- |
| Km estimados 2026             | $G_{14,i}^{2026}$ | 2.183 km                     |
| Km con bono (límite efectivo) | $K_{im^{\ast}}$   | 1.506 km                     |
| Diferencia de km              | $G_{17,i}$        | 678 km                       |
| Bono de estabilización        | $G_{19,i}$        | $67.202                      |
| Pago por rutas                | $G_{22,i}$        | $262.004                     |
| Rutas asignadas del mes       | Lista de rutas    | Según algoritmo sección 9    |

---

# 9. Algoritmo de resolución

## 9.1 Estrategia greedy (implementación base)

El sistema opera como una **cola circular por antigüedad**: las rutas nunca se agotan. Cuando todas las rutas han sido visitadas al menos $f_{\min,i}$ veces, el ciclo se reinicia desde la más antigua, manteniendo siempre la antigüedad acumulada como criterio de orden.

El algoritmo de selección mensual es:

1. Ordenar todas las rutas $j \in R_i$ de mayor a menor antigüedad $a_{jm^{\ast}}$.
2. Recorrer la lista en ese orden e incluir la ruta si:
   - Aún no se han seleccionado suficientes rutas para cubrir los días hábiles del mes ($D_{im^{\ast}}$).
   - El km acumulado más $km_j$ no supera $K_{im^{\ast}}$.
3. Si una ruta no cabe en km, se omite sin perder su antigüedad (mantiene prioridad en meses siguientes).
4. Si todas las rutas ya alcanzaron $f_{\min,i}$ visitas, se continúa seleccionando por antigüedad igual: no se excluyen, solo tienen menor prioridad que las que aún no han cumplido el mínimo.
5. El único caso de alerta es cuando ninguna ruta cabe dentro del límite de km disponible (R5).

**Ventaja:** simple, eficiente, determinista y siempre tiene rutas disponibles.  
**Limitación:** puede no encontrar combinaciones factibles que un solver exacto sí encontraría cuando el límite de km es muy restrictivo.

> **Nota:** R5 refiere al requerimiento número 5 de la lista de requerimientos del sistema definidas en el informe número 1, sección 6.

---

## 9.2 Estrategia de optimización exacta (implementación avanzada)

Resuelve el modelo de programación lineal entera mixta (MILP) completo:

$$\max \sum_{j \in R_i} \left[ a_{jm^{\ast}} + \beta \cdot \delta_j \right] \cdot x_{ij}$$

sujeto a las restricciones 5.1, 5.2, 5.3 y 5.4.

**Ventaja:** garantiza la solución óptima global.  
**Complejidad:** NP-difícil en el caso general; manejable con solvers como OR-Tools o PuLP para el tamaño típico del problema (decenas de rutas por auditor).

---

## 9.3 Comparación de estrategias

| Criterio                 | Greedy         | Optimización exacta                 |
| ------------------------ | -------------- | ----------------------------------- |
| Optimalidad              | No garantizada | Garantizada                         |
| Velocidad                | Alta           | Media-alta (dependiente del tamaño) |
| Implementación           | Simple         | Requiere solver externo             |
| Escalabilidad            | Alta           | Alta (con solver eficiente)         |
| Riesgo de infactibilidad | Mayor          | Menor                               |

Para el tamaño del problema (decenas de rutas por auditor), la optimización exacta es computacionalmente viable y se recomienda como implementación objetivo.

---

# 10. Relación con el problema de la mochila

El modelo es una variante del _Bounded Knapsack Problem_ clásico con restricciones adicionales:

| Elemento del Knapsack     | Equivalente en el sistema                                     |
| ------------------------- | ------------------------------------------------------------- |
| Objetos                   | Rutas $j \in R_i$                                             |
| Peso del objeto           | Kilómetros $km_j$                                             |
| Capacidad de la mochila   | Límite mensual $K_{im^{\ast}}$                                |
| Valor del objeto          | Antigüedad $a_{jm^{\ast}}$ (+ urgencia)                       |
| Selección binaria         | $x_{ij} \in \{0,1\}$                                          |
| **Restricción adicional** | **Cardinalidad exacta** $\sum x_{ij} = D_{im^{\ast}}$         |
| **Restricción adicional** | **Frecuencia mínima anual** $\sum_m x_{ijm} \geq f_{\min}$    |
| **Restricción adicional** | **Estado dinámico** $a_{jm}$, $v_{jm}$ se actualizan cada mes |

La restricción de cardinalidad exacta (igualdad, no desigualdad) aumenta la dificultad combinatoria respecto al Knapsack estándar.

---

# 11. ¿Por qué Excel no es suficiente?

| Capacidad                                       | Excel    | Sistema requerido |
| ----------------------------------------------- | -------- | ----------------- |
| Ingreso de datos simples                        | ✅       | ✅                |
| Visualización de reportes                       | ✅       | ✅                |
| Resolución de problemas combinatorios           | ❌       | ✅                |
| Estado dinámico mes a mes (antigüedad, visitas) | ❌       | ✅                |
| Historial consultable                           | Limitado | ✅                |
| Alerta automática de infactibilidad             | ❌       | ✅                |
| Escalabilidad (nuevos auditores sin rediseño)   | ❌       | ✅                |
| Parámetros configurables sin tocar código       | ❌       | ✅                |

Excel puede funcionar como **interfaz auxiliar** (ingreso de precio de bencina, visualización de informes), pero no como motor de cálculo del sistema.

---

# 12. Comportamiento del sistema ante alzas sostenidas de bencina

Una subida del precio $P_m$ reduce $K_{im^{\ast}}$, lo que genera:

1. **Restricción de capacidad más estricta**: menos rutas km-pesadas pueden incluirse.
2. **Acumulación de antigüedad**: rutas que no caben quedan pendientes y aumentan $a_{jm}$.
3. **Riesgo de incumplimiento de frecuencia mínima**: si $K_{im^*}$ cae mucho, puede volverse imposible completar $D_{im^{\ast}}$ rutas válidas → el sistema emite alerta (R5).
4. **Comportamiento emergente**: el sistema tiende a seleccionar rutas cortas de forma sistemática, generando desequilibrio en la rotación de rutas largas.

Este es un ejemplo de **retroalimentación negativa**: el alza de bencina reduce la capacidad, que reduce las visitas posibles, que incrementa el déficit de frecuencia, que aumenta la urgencia en la función objetivo.

---

# 13. Modelo de datos

| Entidad                | Atributos principales                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------- |
| `Auditor`              | `id`, `nombre`, `sueldo_base`, `km_por_litro`                                               |
| `Ruta`                 | `id`, `nombre`, `distancia_km`, `id_auditor` (FK)                                           |
| `Historial_km`         | `id_auditor`, `mes`, `año`, `km_realizados`                                                 |
| `Parametro_mes`        | `año`, `mes`, `precio_bencina`, `dias_habiles`                                              |
| `Programacion_mensual` | `id_auditor`, `año`, `mes`, `id_ruta`, `ultima_vez_realizada`                               |
| `Registro_pago`        | `id_auditor`, `año`, `mes`, `dias_trabajados`, `pago_base`, `bono`, `pago_km`, `pago_total` |

La entidad `Programacion_mensual` es el núcleo del inventario: registra el estado de cada ruta (cuándo fue visitada por última vez) y permite calcular la antigüedad $a_{jm}$ y las visitas acumuladas $v_{jm}$.

---

# 14. Flujo de procesamiento mensual

```text
[Usuario ingresa precio bencina P_m y días hábiles D_im]
                    ↓
        Cálculo de K_im (Km_con_bono)
                    ↓
   Cálculo de antigüedad a_jm para cada ruta j
   Cálculo de visitas acumuladas v_jm para cada ruta j
                    ↓
     Resolución del modelo de optimización:
     max Σ [a_jm + β·δ_j] · x_ij
     s.a. Σ x_ij = D_im
          Σ km_j · x_ij ≤ K_im
          v_jm + futuros ≥ f_min
                    ↓
   ¿Solución factible? → NO → Emitir alerta (R5)
                    ↓ SÍ
     Generar programación mensual del auditor
                    ↓
     Calcular pago_base, bono, pago_km, pago_total
                    ↓
   Actualizar Programacion_mensual y Registro_pago
                    ↓
        Generar informe mensual (R9, R11)
```

---

# 15. Conclusión

El problema corresponde a un **sistema dinámico adaptativo** con las siguientes características formales:

- **Clase de problema**: optimización combinatoria entera (NP-difícil en el caso general, tratable en el tamaño real del problema).
- **Horizonte**: mensual con estado acumulado anual.
- **Tipo de lazo**: cerrado respecto a la frecuencia mínima anual (retroalimentación a través del estado $v_{jm}$) y abierto respecto al precio de bencina (parámetro exógeno).
- **Escalabilidad**: el modelo escala linealmente con el número de auditores; cada auditor es un subproblema independiente.

La formalización con variables binarias permite implementar el motor de selección en cualquier lenguaje con acceso a un solver MILP, manteniendo la interfaz de usuario simple y operable por personas no técnicas.
