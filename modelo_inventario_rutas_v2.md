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

Para la planificación del mes actual $m^*$, se trabaja con la notación simplificada $x_{ij}$ entendiéndose que corresponde al mes en curso.

---

# 5. Restricciones del modelo

## 5.1 Restricción de cardinalidad (días hábiles)

Cada auditor debe realizar exactamente una ruta por día hábil del mes:

$$\sum_{j \in R_i} x_{ij} = D_{im^*} \quad \forall i \in A$$

Esta restricción es de igualdad estricta: ni más ni menos rutas que los días hábiles disponibles.

---

## 5.2 Restricción de capacidad (kilómetros)

La suma de kilómetros de las rutas seleccionadas no puede superar el límite mensual:

$$\sum_{j \in R_i} km_j \cdot x_{ij} \leq K_{im^*} \quad \forall i \in A$$

Donde $K_{im^*}$ corresponde al valor `Km_con_bono` calculado según el precio de bencina del mes.

---

## 5.3 Restricción de frecuencia mínima anual

Cada ruta debe alcanzar al menos $f_{\min}$ visitas durante el año:

$$\sum_{m=1}^{12} x_{ijm} \geq f_{\min} \quad \forall i \in A,\ \forall j \in R_i$$

Equivalentemente, usando el estado acumulado al mes $m^*$:

$$v_{jm^{\ast}} + \sum_{m=m^*}^{12} x_{ijm} \geq f_{\min} \quad \forall i \in A,\ \forall j \in R_i$$

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

Para incorporar también la urgencia de cumplimiento de frecuencia mínima, se define un término de penalización:

$$\max \sum_{j \in R_i} \left[ a_{jm^*} + \beta \cdot \max\left(0,\ f_{\min} - v_{jm^*} - (12 - m^* + 1)\right) \right] \cdot x_{ij}$$

Donde:

- $\beta > 0$ es un parámetro de peso que controla la importancia relativa de la urgencia de frecuencia frente a la antigüedad pura;
- el término $\max(0,\ f_{\min} - v_{jm^*} - (12 - m^* + 1))$ cuantifica el déficit de visitas que no puede recuperarse con los meses restantes del año.

Cuando $\beta = 0$, la función colapsa a la formulación base.

---

## 6.3 Interpretación combinada

| Componente                   | Efecto                                                               |
| ---------------------------- | -------------------------------------------------------------------- |
| $a_{jm^*}$                   | Prioriza rutas con mayor tiempo sin visitar                          |
| $\beta \cdot \text{déficit}$ | Eleva la prioridad de rutas en riesgo de no cumplir frecuencia anual |
| Restricción 5.1              | Garantiza exactamente $D_{im^*}$ rutas seleccionadas                 |
| Restricción 5.2              | Garantiza que no se supera el límite de km                           |
| Restricción 5.3              | Garantiza cumplimiento de frecuencia mínima a largo plazo            |

---

# 7. Cálculo del límite de kilómetros mensual (`Km_con_bono`)

El presupuesto de kilómetros parte de los kilómetros históricos del auditor en el mismo mes del año anterior, ajustado por la variación del precio de la bencina. El objetivo es mantener el mismo gasto total en combustible: si la bencina sube, el auditor recorre menos kilómetros pero recibe un bono que compensa la diferencia.

## 7.1 Parámetros adicionales del cálculo

| Símbolo                 | Descripción                                                                  | Ejemplo   |
| ----------------------- | ---------------------------------------------------------------------------- | --------- |
| $M_{20}^m$              | Presupuesto total de todos los auditores en el mes $m$ del año anterior      | 2.162.160 |
| $M_{14}^m$              | Km totales recorridos por todos los auditores en el mes $m$ del año anterior | 18.018    |
| $M_{21}^m$              | Presupuesto estimado total mes $m$ año actual antes del bono                 | 1.739.611 |
| $M_{15}^m$              | Km estimados totales mes $m$ año actual antes del bono                       | 15.444    |
| $G_{14,i}$              | Km recorridos por el auditor $i$ en el mes $m$ del año anterior              | 2.580     |
| $T$                     | Tarifa interna vigente por km (año actual)                                   | 140       |
| $T_{\text{ant}}$        | Tarifa interna por km del año anterior                                       | 120       |
| $P_{\text{actual}}^m$   | Precio de la bencina en el mes $m$ del año actual                            | 1.583     |
| $P_{\text{anterior}}^m$ | Precio de la bencina en el mes $m$ del año anterior                          | 1.188     |

---

## 7.2 Paso 1 — Km estimados sin bono

Proporción de los km históricos del auditor $i$ respecto al total del año anterior, aplicada al nuevo presupuesto:

$$G_{15,i} = \frac{M_{20}^m}{T \cdot M_{14}^m} \cdot G_{14,i}$$

---

## 7.3 Paso 2 — Litros implícitos del auditor (rendimiento)

Cantidad de litros que representan los km estimados según el rendimiento $r_i$ del vehículo:

$$G_{18,i} = \frac{G_{15,i}}{r_i}$$

---

## 7.4 Paso 3 — Bono de estabilización

Compensación por el alza del precio de la bencina respecto al año anterior:

$$G_{19,i} = G_{18,i} \times \left( P_{\text{actual}}^m - P_{\text{anterior}}^m \right)$$

El bono cubre exactamente el costo adicional de combustible generado por la diferencia de precio, calculado sobre los litros que consume el auditor.

---

## 7.5 Paso 4 — Pago del año anterior

$$G_{20,i} = G_{14,i} \times T_{\text{ant}}$$

---

## 7.6 Paso 5 — Pago año actual antes del bono

$$G_{21,i} = G_{20,i} - G_{19,i}$$

---

## 7.7 Paso 6 — Pago total año actual (con bono)

$$G_{22,i} = G_{21,i} + G_{19,i} = G_{20,i}$$

Esto confirma una propiedad clave del sistema: **el pago total por kilómetros se mantiene igual al año anterior**, independientemente del precio de la bencina. El bono no aumenta el gasto; solo redistribuye el presupuesto para absorber el alza.

---

## 7.8 Paso 7 — Km reales disponibles con bono (`Km_con_bono`)

Este es el límite efectivo $K_{im^*}$ que entra al modelo de optimización:

$$K_{im^*} = G_{16,i} = \frac{M_{21}^m}{T \cdot M_{15}^m} \cdot G_{15,i}$$

---

## 7.9 Paso 8 — Diferencia de km (registro histórico)

$$G_{17,i} = G_{14,i} - G_{16,i}$$

Este valor no afecta la optimización; se registra para seguimiento de la reducción de cobertura causada por el alza de bencina.

---

## 7.10 Ejemplo numérico (auditor A1, mes $m$)

| Paso                  | Fórmula                                                             | Resultado    |
| --------------------- | ------------------------------------------------------------------- | ------------ |
| Km estimados sin bono | $G_{15} = \frac{2{,}162{,}160}{140 \times 18{,}018} \times 2{,}580$ | 2.211 km     |
| Litros implícitos     | $G_{18} = \frac{2{,}211}{11}$                                       | 201 litros   |
| Bono                  | $G_{19} = 201 \times (1{,}583 - 1{,}188)$                           | \$79.395     |
| Pago año anterior     | $G_{20} = 2{,}580 \times 120$                                       | \$309.600    |
| Pago sin bono         | $G_{21} = 309{,}600 - 79{,}395$                                     | \$230.205    |
| Pago con bono         | $G_{22} = 230{,}205 + 79{,}395$                                     | \$309.600    |
| **Km con bono**       | $G_{16} = \frac{1{,}739{,}611}{140 \times 15{,}444} \times 2{,}211$ | **1.778 km** |
| Diferencia de km      | $G_{17} = 2{,}580 - 1{,}778$                                        | 802 km       |

---

# 8. Cálculo del pago mensual por auditor

## 8.1 Componente 1: Sueldo base

El auditor recibe un sueldo base mensual fijo $SB_i$, independiente de los kilómetros recorridos. Ejemplo: \$700.000.

---

## 8.2 Componente 2: Pago por kilómetros (rutas)

El pago por rutas se construye en tres pasos:

**Paso 1 — Calcular el pago que se hizo el año anterior:**

$$G_{20,i} = G_{14,i} \times T_{\text{ant}}$$

Ejemplo: $2.580 \times 120 = \$309.600$

**Paso 2 — Restar el bono** (que cubre el alza de bencina):

$$G_{21,i} = G_{20,i} - G_{19,i}$$

Ejemplo: $309.600 - 79.395 = \$230.205$

**Paso 3 — Sumar el bono de vuelta** para llegar al pago final:

$$G_{22,i} = G_{21,i} + G_{19,i}$$

Ejemplo: $230.205 + 79.395 = \$309.600$

El resultado es que $G_{22,i} = G_{20,i}$ siempre: **el pago por rutas del año actual es igual al del año anterior**. El bono no aumenta el gasto total; solo compensa internamente el alza de bencina para mantener el presupuesto estable.

$$\text{Pago\_km}_{im^*} = G_{22,i} = \$309.600$$

---

## 8.3 Pago total mensual

El pago total es la suma de ambos componentes:

$$\text{Pago\_total}_{im^*} = SB_i + \text{Pago\_km}_{im^*}$$

Ejemplo: $700.000 + 309.600 = \$1.009.600$

---

## 8.4 Descuento por inasistencia

Si el auditor no trabajó todos los días hábiles, se aplica un descuento proporcional sobre el pago total:

$$\text{Pago\_final}_{im^*} = \text{Pago\_total}_{im^*} \times \frac{DT_{im^*}}{D_{im^*}}$$

> ⚠️ **Por confirmar:** si el descuento aplica sobre el pago total (base + km) o solo sobre el sueldo base. La lógica reportada indica que es sobre el total, pero se debe validar con el equipo.

---

# 9. Algoritmo de resolución

## 9.1 Estrategia greedy (implementación base)

El sistema opera como una **cola circular por antigüedad**: las rutas nunca se agotan. Cuando todas las rutas han sido visitadas al menos $f_{\min,i}$ veces, el ciclo se reinicia desde la más antigua, manteniendo siempre la antigüedad acumulada como criterio de orden.

El algoritmo de selección mensual es:

1. Ordenar todas las rutas $j \in R_i$ de mayor a menor antigüedad $a_{jm^*}$.
2. Recorrer la lista en ese orden e incluir la ruta si:
   - Aún no se han seleccionado suficientes rutas para cubrir los días hábiles del mes ($D_{im^*}$).
   - El km acumulado más $km_j$ no supera $K_{im^*}$.
3. Si una ruta no cabe en km, se omite sin perder su antigüedad (mantiene prioridad en meses siguientes).
4. Si todas las rutas ya alcanzaron $f_{\min,i}$ visitas, se continúa seleccionando por antigüedad igual: no se excluyen, solo tienen menor prioridad que las que aún no han cumplido el mínimo.
5. El único caso de alerta es cuando ninguna ruta cabe dentro del límite de km disponible (R5).

**Ventaja:** simple, eficiente, determinista y siempre tiene rutas disponibles.  
**Limitación:** puede no encontrar combinaciones factibles que un solver exacto sí encontraría cuando el límite de km es muy restrictivo.

> **Nota:** R5 refiere al requerimiento número 5 de la lista de requerimientos del sistema definidas en el informe número 1, sección 6.

---

## 9.2 Estrategia de optimización exacta (implementación avanzada)

Resuelve el modelo de programación lineal entera mixta (MILP) completo:

$$\max \sum_{j \in R_i} \left[ a_{jm^*} + \beta \cdot \delta_j \right] \cdot x_{ij}$$

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
| Capacidad de la mochila   | Límite mensual $K_{im^*}$                                     |
| Valor del objeto          | Antigüedad $a_{jm^*}$ (+ urgencia)                            |
| Selección binaria         | $x_{ij} \in \{0,1\}$                                          |
| **Restricción adicional** | **Cardinalidad exacta** $\sum x_{ij} = D_{im^*}$              |
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

Una subida del precio $P_m$ reduce $K_{im^*}$, lo que genera:

1. **Restricción de capacidad más estricta**: menos rutas km-pesadas pueden incluirse.
2. **Acumulación de antigüedad**: rutas que no caben quedan pendientes y aumentan $a_{jm}$.
3. **Riesgo de incumplimiento de frecuencia mínima**: si $K_{im^*}$ cae mucho, puede volverse imposible completar $D_{im^*}$ rutas válidas → el sistema emite alerta (R5).
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

# 15. Tecnologías recomendadas

## Backend

- Python (recomendado por ecosistema de optimización)
- FastAPI o Django

## Base de datos

- PostgreSQL (preferido por integridad referencial y consultas complejas)
- MySQL (alternativa)

## Motor de optimización

| Opción                  | Tipo               | Licencia    |
| ----------------------- | ------------------ | ----------- |
| OR-Tools (Google)       | Solver exacto MILP | Open source |
| PuLP + CBC              | Solver exacto MILP | Open source |
| Algoritmo greedy propio | Heurística         | N/A         |

## Interfaz de usuario

- Aplicación web con formularios simples (no requiere conocimientos técnicos)
- Exportación de informes en Excel/PDF
- Panel de resumen mensual

---

# 16. Conclusión

El problema corresponde a un **sistema dinámico adaptativo** con las siguientes características formales:

- **Clase de problema**: optimización combinatoria entera (NP-difícil en el caso general, tratable en el tamaño real del problema).
- **Horizonte**: mensual con estado acumulado anual.
- **Tipo de lazo**: cerrado respecto a la frecuencia mínima anual (retroalimentación a través del estado $v_{jm}$) y abierto respecto al precio de bencina (parámetro exógeno).
- **Escalabilidad**: el modelo escala linealmente con el número de auditores; cada auditor es un subproblema independiente.

La formalización con variables binarias permite implementar el motor de selección en cualquier lenguaje con acceso a un solver MILP, manteniendo la interfaz de usuario simple y operable por personas no técnicas.
