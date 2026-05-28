# Informe Número 3

# Implementación del Sistema de Rutas para Auditores

---

# 1. Stack tecnológico

| Componente          | Tecnología   | Rol                                             |
| ------------------- | ------------ | ----------------------------------------------- |
| Motor de cálculo    | Python 3     | Km_con_bono, greedy, pagos                      |
| Base de datos       | SQLite       | Persistencia local (archivo `.db`)              |
| Servidor web local  | Flask        | Interfaz entre motor y navegador                |
| Interfaz de usuario | HTML/CSS     | Formularios e informes en navegador             |
| Empaquetado         | PyInstaller  | Genera `.exe` ejecutable sin instalar Python    |
| Respaldo compartido | Google Drive | Sincronización del archivo `.db` entre usuarios |

**Decisiones clave:**

- SQLite como base de datos: un solo archivo `.db`, sin servidor, sincronizable por Google Drive.
- Flask corre localmente (`localhost`): el usuario abre el navegador como si fuera una página web, sin instalar nada adicional tras el `.exe`.
- No se usa Excel como motor: el problema de selección de rutas es combinatorio y requiere código. Excel puede usarse como referencia externa pero no como motor.

---

# 2. Arquitectura del sistema

```
[Usuario abre .exe]
        ↓
[Flask inicia en localhost]
        ↓
[Navegador abre interfaz]
        ↓
[Usuario ingresa precio bencina + días hábiles]
        ↓
[Motor Python calcula Km_con_bono por auditor]
        ↓
[Greedy selecciona rutas del mes]
        ↓
[Sistema genera informe mensual]
        ↓
[BD SQLite se actualiza]
        ↓
[Google Drive sincroniza .db automáticamente]
```

---

# 3. Base de datos

## 3.1 Esquema

| Tabla                  | Descripción                                                                 |
| ---------------------- | --------------------------------------------------------------------------- |
| `auditor`              | Datos fijos por auditor: nombre, ciudad, rendimiento km/litro               |
| `ruta`                 | Lista de rutas por auditor con distancia en km                              |
| `historial_km`         | Km recorridos por auditor por mes (2025 y siguientes)                       |
| `parametro_mes`        | Precio bencina y días hábiles por mes/año                                   |
| `programacion_mensual` | Rutas asignadas a cada auditor por mes                                      |
| `registro_pago`        | Bono y pago por km por auditor por mes                                      |
| `config`               | Parámetros configurables: tarifa, precio bencina anterior, delta frecuencia |

## 3.2 Carga inicial

Fuentes utilizadas:

- `Rutas___Kilometros_Auditores.xlsx`: rutas por auditor (5 hojas, una por auditor activo)
- `_ABR26_Roble_Ajuste_KM_macros.xlsm`: histórico km 2025 (hoja "Resumen mensual")
- `24052026_Proyección_Presupuesto_v2.xlsx`: presupuesto mensual 2026 (Hoja2, fila 3)

Resultado de la carga:

| Auditor          | Ciudad       | Rendimiento | Rutas | Meses histórico |
| ---------------- | ------------ | ----------- | ----- | --------------- |
| Carlos Acevedo   | Talca        | 11 km/L     | 48    | 12 (2025)       |
| Samuel Inostroza | Curicó       | 17 km/L     | 31    | 12 (2025)       |
| Cristian Lizama  | San Fernando | 17 km/L     | 52    | 12 (2025)       |
| Pablo Villarroel | Talca        | 12 km/L     | 39    | 12 (2025)       |
| Mauricio Picart  | Talca        | 15 km/L     | 43    | 12 (2025)       |

**Nota:** Marco Contreras (Parral) renunció. Su histórico 2025 quedó guardado en la BD para referencia. Su espacio queda disponible para el auditor que llegue en reemplazo, sin necesidad de rediseñar el sistema.

## 3.3 Parámetros configurables iniciales

| Clave                     | Valor | Descripción                                |
| ------------------------- | ----- | ------------------------------------------ |
| `tarifa_actual`           | 140   | Tarifa por km año actual ($)               |
| `tarifa_anterior`         | 120   | Tarifa por km año anterior ($)             |
| `precio_bencina_anterior` | 1188  | Precio bencina 2025 ($/litro)              |
| `delta_frecuencia`        | 2     | Ajuste al mínimo de rotaciones por auditor |

## 3.4 Presupuesto mensual 2026

Ingresado desde `24052026_Proyección_Presupuesto_v2.xlsx`, Hoja2, fila 3:

| Mes        | Presupuesto total ($) |
| ---------- | --------------------- |
| Enero      | 1.829.760             |
| Febrero    | 1.200.360             |
| Marzo      | 1.316.640             |
| Abril      | 1.662.720             |
| Mayo       | 1.978.340             |
| Junio      | 1.812.100             |
| Julio      | 1.812.100             |
| Agosto     | 1.812.100             |
| Septiembre | 1.812.100             |
| Octubre    | 1.812.100             |
| Noviembre  | 1.812.100             |
| Diciembre  | 1.812.100             |

---

# 4. Motor de cálculo

## 4.1 Estado

🔲 Pendiente de implementación

## 4.2 Descripción

El motor implementa la sección 7 del Informe 2 (cálculo de Km_con_bono) y la sección 9 (algoritmo greedy de selección de rutas).

**Entradas:**

- Precio bencina del mes (ingresado por usuario)
- Días hábiles del mes (ingresado por usuario)

**Salidas por auditor:**

- Km_con_bono (límite efectivo del mes)
- Lista de rutas asignadas
- Bono de estabilización
- Pago por km

---

# 5. Interfaz web local (Flask)

## 5.1 Estado

🔲 Pendiente de implementación

---

# 6. Empaquetado (.exe)

## 6.1 Estado

🔲 Pendiente de implementación

---

_Este informe se actualiza a medida que avanza la implementación._
