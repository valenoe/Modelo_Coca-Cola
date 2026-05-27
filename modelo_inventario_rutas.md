# Sistema de Inventario de Rutas para Auditores

## Modelo de inventario con variables binarias

# 1. Definición del problema

El sistema debe seleccionar rutas mensuales para cada auditor considerando:

- una cantidad fija de días hábiles;
- un límite máximo de kilómetros;
- una frecuencia mínima anual de visitas;
- priorización por antigüedad.

El problema puede modelarse como un problema de optimización combinatoria similar al **Knapsack Problem**.

---

# 2. Conjuntos

## Auditores

```math
i \in A
```

Donde:

- \(A\) = conjunto de auditores.

---

## Rutas

```math
j \in R_i
```

Donde:

- \(R_i\) = conjunto de rutas asignadas al auditor \(i\).

---

# 3. Parámetros

| Parámetro | Descripción                                             |
| --------- | ------------------------------------------------------- |
| \(km_j\)  | kilómetros de la ruta \(j\)                             |
| \(D_i\)   | días hábiles del auditor \(i\)                          |
| \(K_i\)   | límite mensual de kilómetros (\(Km_con_bono\))          |
| \(a_j\)   | antigüedad de la ruta \(j\)                             |
| \(f_j\)   | frecuencia anual mínima requerida                       |
| \(v_j\)   | cantidad de veces que la ruta ya fue visitada en el año |

---

# 4. Variable de decisión

La variable principal del modelo es binaria.

```math
x_{ij} =
\begin{cases}
1 & \text{si la ruta } j \text{ es asignada al auditor } i \\
0 & \text{en otro caso}
\end{cases}
```

Esto significa:

- \(x\_{ij} = 1\) → la ruta se programa este mes;
- \(x\_{ij} = 0\) → la ruta no se programa.

---

# 5. Restricciones

## 5.1 Restricción de cantidad de rutas

Cada auditor debe realizar exactamente una ruta por día hábil.

```math
\sum_{j \in R_i} x_{ij} = D_i
```

---

## 5.2 Restricción de kilómetros

La suma de kilómetros no puede superar el límite mensual disponible.

```math
\sum_{j \in R_i} km_j \cdot x_{ij} \leq K_i
```

---

## 5.3 Restricción de frecuencia mínima anual

Cada ruta debe alcanzar una cantidad mínima de visitas durante el año.

```math
v_j + x_{ij} \geq f_j
```

o bien, acumulado anual:

```math
\sum_{m=1}^{12} x_{ijm} \geq f_j
```

Donde:

- \(x\_{ijm}\) indica si la ruta \(j\) fue realizada por el auditor \(i\) en el mes \(m\).

---

# 6. Función objetivo

El sistema prioriza rutas con mayor antigüedad.

Por ello, la función objetivo puede definirse como:

```math
\max \sum_{j \in R_i} a_j \cdot x_{ij}
```

Esto busca:

- maximizar la atención de rutas antiguas;
- reducir acumulación de rutas pendientes;
- mantener rotación equilibrada.

---

# 7. Interpretación del modelo

El sistema intenta encontrar una combinación de rutas que:

1. complete exactamente los días hábiles;
2. no exceda los kilómetros disponibles;
3. priorice rutas antiguas;
4. mantenga la frecuencia anual.

Este comportamiento es equivalente a un problema de optimización combinatoria.

---

# 8. Relación con el problema de la mochila

El modelo es similar al problema clásico de la mochila (**Knapsack Problem**):

| Problema mochila  | Sistema de rutas       |
| ----------------- | ---------------------- |
| Objetos           | Rutas                  |
| Peso              | Kilómetros             |
| Capacidad         | Km disponibles         |
| Valor             | Antigüedad/prioridad   |
| Selección binaria | Ruta seleccionada o no |

La diferencia principal es que aquí además existen:

- restricciones de frecuencia anual;
- cantidad exacta de rutas;
- rotación temporal.

---

# 9. ¿Por qué Excel no es suficiente?

Excel puede servir para:

- ingresar datos;
- visualizar reportes;
- realizar cálculos simples.

Sin embargo, este problema:

- es combinatorio;
- cambia dinámicamente cada mes;
- requiere historial;
- necesita priorización automática.

Por ello, una solución completa normalmente requiere:

- base de datos;
- backend;
- algoritmo de optimización;
- interfaz simple para usuarios.

Excel puede funcionar como interfaz auxiliar, pero no como motor principal del sistema.

---

# 10. Posibles tecnologías

## Backend

- Python
- FastAPI
- Django
- Node.js

## Base de datos

- PostgreSQL
- MySQL

## Algoritmos

- Programación lineal entera
- Heurísticas
- OR-Tools
- PuLP

## Interfaz

- Web simple
- Formularios tipo Excel
- Panel de reportes

---

# 11. Modelo conceptual del sistema

```text
Precio bencina
        ↓
Cálculo Km disponibles
        ↓
Selección óptima de rutas
        ↓
Control frecuencia anual
        ↓
Programación mensual
        ↓
Pagos e informes
```

---

# 12. Conclusión

El problema corresponde a un sistema dinámico adaptativo con características de optimización combinatoria.

La utilización de variables binarias permite formalizar matemáticamente la selección de rutas, transformando el problema en un modelo de programación lineal entera.

Debido a la cantidad de restricciones y al comportamiento dinámico mensual, el sistema excede las capacidades prácticas de Excel y requiere una solución computacional especializada.
