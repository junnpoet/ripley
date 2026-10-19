# PROYECTO DE INTELIGENCIA DE NEGOCIOS: RIPLEY PERÚ

**Título:** *Modelo de Inteligencia de Negocios para el análisis y optimización de la gestión de ventas y afluencia en horas pico de la empresa comercial Ripley*  
**Organización:** Ripley Perú S.A.  
**Alcance Operativo:** Tiendas físicas representativas (Jockey Plaza, San Miguel, Mall Aventura Arequipa)  
**Período de Análisis:** Campaña Comercial de Alta Demanda (Julio 2026 - Fiestas Patrias, 31 días)

---

## 1. Planteamiento del Problema de Negocio

En el entorno de las tiendas por departamento en el Perú, Ripley enfrenta una desconexión crítica entre la dinámica de atracción de clientes y la capacidad operativa de atención en piso de venta:

1. **Cuellos de Botella en Puntos de Venta (POS):** Durante las horas pico (tarde/noche de 18:00 a 21:00 y fines de semana), la afluencia de visitantes se triplica, pero la dotación de cajas y cajeros se mantiene rígida o subdimensionada, generando colas extensas.
2. **Fuga de Ingresos por Abandono de Compras (*Walk-outs / Cart Abandonment*):** Los clientes que ya seleccionaron productos desisten de la compra al percibir tiempos de espera en cola superiores a los 6-10 minutos, dejando carritos o prendas abandonadas en tienda.
3. **Caída de la Tasa de Conversión en Horarios de Mayor Oportunidad:** Paradójicamente, en las franjas horarias con mayor tráfico de personas, la tasa de conversión (visitantes que compran) cae entre 8 y 12 puntos porcentuales respecto a las horas valle.
4. **Desfase en la Reposición de Inventario:** Las categorías de alta rotación (Moda, Calzado, Tecnología) sufren quiebres de stock en anaquel durante los picos de venta porque los equipos de trastienda no cuentan con alertas predictivas de consumo intradía.

---

## 2. Objetivos del Proyecto

### Objetivo General
Diseñar e implementar una solución integral de Inteligencia de Negocios (Data Warehouse bajo metodología Ralph Kimball y dashboards analíticos) que permita correlacionar el flujo de afluencia peatonal (sensores IoT) con las transacciones comerciales efectivas (POS), identificando con precisión los cuellos de botella en horas pico para optimizar la dotación del personal y maximizar la facturación.

### Objetivos Específicos
1. **Aislar y cuantificar los patrones de venta intradía y semanales:** Medir la concentración de ingresos y tickets en horas pico vs. horas valle mediante segmentación temporal granular.
2. **Correlacionar afluencia peatonal vs. ventas efectivas:** Calcular la tasa de conversión horaria por sede para dimensionar económicamente el impacto del abandono de compras.
3. **Monitorear el rendimiento y congestión del servicio en caja:** Evaluar tiempos de espera en cola, tiempos de atención por terminal y carga transaccional por cajero.
4. **Identificar la rotación horaria de categorías comerciales:** Determinar qué familias de productos lideran el consumo en horas pico para optimizar el reabastecimiento en sala de venta.
5. **Construir un cuadro de mando ejecutivo (Dashboard):** Proveer visualizaciones accionables para gerencia de tienda, operaciones y planificación comercial.

---

## 3. Beneficios Esperados para Ripley

* **Incremento Directo de Ventas (+3% a +5% en facturación de campaña):** Al habilitar oportunamente cajas volantes y módulos de autoatención (Self-Checkout) en horas pico, reduciendo el abandono de carritos.
* **Optimización del Costo Laboral y Eficiencia de Turnos:** Redistribución inteligente del personal de caja desde horas valle (donde sobran recursos) hacia los turnos de alta concentración de público.
* **Reducción de Tiempos de Espera:** Disminución del tiempo promedio en cola de 8–10 minutos a menos de 4 minutos en horas punta, mejorando la satisfacción del cliente (NPS).
* **Disponibilidad Continua de Producto:** Disminución de quiebres de góndola en las categorías más demandadas durante los picos comerciales.

---

## 4. Principales Indicadores y Métricas Clave (KPIs)

* **Tasa de Conversión de Tienda (%):** `(Total Tickets Emitidos / Total Visitantes Ingresados) * 100`
* **Venta Total y Margen Bruto por Franja Horaria:** Facturación y rentabilidad desglosada por hora y día.
* **Ticket Promedio Horario (S/.):** Comparativa del valor promedio de canasta en Horas Pico vs. Horas Valle.
* **Tiempo Promedio de Espera en Cola (seg/min):** Minutos que aguarda el cliente antes de ser atendido.
* **Tiempo Promedio de Atención en Caja (seg):** Duración del escaneo, embolsado y procesamiento de cobro.
* **Índice de Saturación de Aforo (%):** `(Aforo Ocupado / Aforo Máximo Autorizado) * 100`

---

## 5. Productos Analíticos y Dashboard Esperado

1. **Mapa de Calor (Heatmap) de Ventas:** Visualización bidimensional (Día de la semana vs. Hora de 10:00 a 22:00) para detectar patrones de congestión e ingresos.
2. **Gráfico de Doble Eje (Afluencia vs. Transacciones):** Curva comparativa de personas que ingresan a tienda frente a tickets pagados, evidenciando la brecha de abandono en horas pico.
3. **Tarjetas de Desempeño Ejecutivo (KPI Cards):** Ingresos acumulados, ticket promedio general vs. pico, tiempo medio de cola y tasa de conversión global.
4. **Ranking de Rotación de Categorías y Marcas:** Gráficos de barras que muestren los departamentos líderes en horarios punta para priorizar reposición de trastienda.
