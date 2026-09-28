-- =============================================================================
-- DATA WAREHOUSE ANALÍTICO (DATA MART) - ESQUEMA DIMENSIONAL RIPLEY
-- Modelo Constelación de Hechos (Fact Constellation) según Ralph Kimball
-- Motor: MySQL 8.0+
-- Codificación: UTF-8 (utf8mb4)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `ripley_dw`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `ripley_dw`;

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. TABLAS DE DIMENSIONES CONFORMES
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS `FACT_VENTAS`;
DROP TABLE IF EXISTS `FACT_AFLUENCIA_TIENDA`;
DROP TABLE IF EXISTS `DIM_FECHA`;
DROP TABLE IF EXISTS `DIM_HORA`;
DROP TABLE IF EXISTS `DIM_TIENDA`;
DROP TABLE IF EXISTS `DIM_PRODUCTO`;
DROP TABLE IF EXISTS `DIM_CAJA`;
DROP TABLE IF EXISTS `DIM_PERSONAL`;
DROP TABLE IF EXISTS `DIM_MEDIO_PAGO`;
DROP TABLE IF EXISTS `DIM_CLIENTE`;

-- 1.1 Dimensión Fecha / Calendario
CREATE TABLE `DIM_FECHA` (
    `id_fecha` INT NOT NULL,  -- Clave formato YYYYMMDD (ej. 20260826)
    `fecha` DATE NOT NULL,
    `anio` SMALLINT NOT NULL,
    `trimestre` TINYINT NOT NULL,
    `mes` TINYINT NOT NULL,
    `nombre_mes` VARCHAR(15) NOT NULL,
    `dia` TINYINT NOT NULL,
    `nombre_dia` VARCHAR(15) NOT NULL,
    `numero_dia_semana` TINYINT NOT NULL,
    `es_fin_de_semana` BOOLEAN NOT NULL DEFAULT FALSE,
    `es_feriado` BOOLEAN NOT NULL DEFAULT FALSE,
    `temporada_comercial` VARCHAR(30) NOT NULL DEFAULT 'Regular',
    PRIMARY KEY (`id_fecha`),
    UNIQUE KEY `uk_fecha_calendario` (`fecha`),
    KEY `idx_fecha_anio_mes` (`anio`, `mes`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.2 Dimensión Franja Horaria
CREATE TABLE `DIM_HORA` (
    `id_hora` INT NOT NULL,  -- Clave formato HHMM (ej. 1830)
    `hora_entera` TINYINT NOT NULL,
    `minuto` TINYINT NOT NULL,
    `franja_horaria` VARCHAR(20) NOT NULL,  -- ej. '18:00 - 19:00'
    `tipo_horario` VARCHAR(20) NOT NULL,    -- 'Hora Pico', 'Hora Valle', 'Hora Normal'
    `turno` VARCHAR(15) NOT NULL,           -- 'Mañana', 'Tarde', 'Noche'
    PRIMARY KEY (`id_hora`),
    KEY `idx_hora_tipo` (`tipo_horario`),
    KEY `idx_hora_turno` (`turno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.3 Dimensión Tienda / Sucursal
CREATE TABLE `DIM_TIENDA` (
    `id_tienda` INT NOT NULL AUTO_INCREMENT,  -- Clave sustituta (SK)
    `codigo_tienda` VARCHAR(10) NOT NULL,    -- Clave natural (NK)
    `nombre_tienda` VARCHAR(100) NOT NULL,
    `formato_tienda` VARCHAR(50) NOT NULL,
    `centro_comercial` VARCHAR(100) NOT NULL,
    `departamento` VARCHAR(50) NOT NULL,
    `provincia` VARCHAR(50) NOT NULL,
    `distrito` VARCHAR(50) NOT NULL,
    `aforo_maximo` INT NOT NULL,
    `superficie_m2` DECIMAL(10,2) NOT NULL,
    `total_cajas_instaladas` INT NOT NULL,
    PRIMARY KEY (`id_tienda`),
    UNIQUE KEY `uk_dim_tienda_codigo` (`codigo_tienda`),
    KEY `idx_dim_tienda_geografia` (`departamento`, `provincia`, `distrito`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.4 Dimensión Producto / Catálogo
CREATE TABLE `DIM_PRODUCTO` (
    `id_producto` INT NOT NULL AUTO_INCREMENT,  -- Clave sustituta (SK)
    `sku` VARCHAR(30) NOT NULL,                 -- Clave natural (NK)
    `nombre_producto` VARCHAR(150) NOT NULL,
    `marca` VARCHAR(60) NOT NULL,
    `marca_propia` BOOLEAN NOT NULL DEFAULT FALSE,
    `categoria` VARCHAR(60) NOT NULL,
    `subcategoria` VARCHAR(60) NOT NULL,
    `departamento_comercial` VARCHAR(60) NOT NULL,
    `precio_lista` DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (`id_producto`),
    UNIQUE KEY `uk_dim_prod_sku` (`sku`),
    KEY `idx_dim_prod_cat` (`categoria`, `subcategoria`),
    KEY `idx_dim_prod_marca` (`marca`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.5 Dimensión Caja / Punto de Venta (POS)
CREATE TABLE `DIM_CAJA` (
    `id_caja` INT NOT NULL AUTO_INCREMENT,  -- Clave sustituta (SK)
    `codigo_caja` VARCHAR(20) NOT NULL,     -- Clave natural (NK)
    `numero_piso` TINYINT NOT NULL DEFAULT 1,
    `zona_caja` VARCHAR(50) NOT NULL,
    `tipo_caja` VARCHAR(30) NOT NULL,
    `estado_caja` VARCHAR(20) NOT NULL DEFAULT 'Operativa',
    PRIMARY KEY (`id_caja`),
    UNIQUE KEY `uk_dim_caja_codigo` (`codigo_caja`),
    KEY `idx_dim_caja_tipo` (`tipo_caja`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.6 Dimensión Personal / Colaborador
CREATE TABLE `DIM_PERSONAL` (
    `id_empleado` INT NOT NULL AUTO_INCREMENT,  -- Clave sustituta (SK)
    `codigo_empleado` VARCHAR(20) NOT NULL,     -- Clave natural (DNI / Planilla)
    `nombre_completo` VARCHAR(120) NOT NULL,
    `cargo` VARCHAR(50) NOT NULL,
    `turno_programado` VARCHAR(30) NOT NULL,
    `tipo_contrato` VARCHAR(30) NOT NULL DEFAULT 'Full-Time',
    PRIMARY KEY (`id_empleado`),
    UNIQUE KEY `uk_dim_emp_codigo` (`codigo_empleado`),
    KEY `idx_dim_emp_cargo` (`cargo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.7 Dimensión Medio de Pago
CREATE TABLE `DIM_MEDIO_PAGO` (
    `id_medio_pago` INT NOT NULL AUTO_INCREMENT,  -- Clave sustituta (SK)
    `tipo_medio_pago` VARCHAR(50) NOT NULL,
    `canal_pago` VARCHAR(30) NOT NULL,
    `es_tarjeta_ripley` BOOLEAN NOT NULL DEFAULT FALSE,
    `emisor_financiero` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id_medio_pago`),
    KEY `idx_dim_pago_tarjeta` (`es_tarjeta_ripley`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.8 Dimensión Cliente
CREATE TABLE `DIM_CLIENTE` (
    `id_cliente` INT NOT NULL AUTO_INCREMENT,  -- Clave sustituta (SK)
    `codigo_cliente` VARCHAR(50) NOT NULL,     -- Hash DNI / Código Socio
    `tipo_cliente` VARCHAR(50) NOT NULL,
    `segmento_fidelidad` VARCHAR(50) NOT NULL,
    `rango_edad` VARCHAR(30) NOT NULL,
    `genero` VARCHAR(20) NOT NULL,
    PRIMARY KEY (`id_cliente`),
    UNIQUE KEY `uk_dim_cli_codigo` (`codigo_cliente`),
    KEY `idx_dim_cli_segmento` (`segmento_fidelidad`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. REGISTROS COMODÍN / DESCONOCIDOS (ESTÁNDAR RALPH KIMBALL)
-- -----------------------------------------------------------------------------

INSERT INTO `DIM_FECHA` (`id_fecha`, `fecha`, `anio`, `trimestre`, `mes`, `nombre_mes`, `dia`, `nombre_dia`, `numero_dia_semana`, `es_fin_de_semana`, `es_feriado`, `temporada_comercial`)
VALUES (-1, '1900-01-01', 1900, 1, 1, 'No especificado', 1, 'No especificado', 1, FALSE, FALSE, 'Desconocido');

INSERT INTO `DIM_HORA` (`id_hora`, `hora_entera`, `minuto`, `franja_horaria`, `tipo_horario`, `turno`)
VALUES (-1, 0, 0, 'No especificado', 'Desconocido', 'Desconocido');

INSERT INTO `DIM_TIENDA` (`id_tienda`, `codigo_tienda`, `nombre_tienda`, `formato_tienda`, `centro_comercial`, `departamento`, `provincia`, `distrito`, `aforo_maximo`, `superficie_m2`, `total_cajas_instaladas`)
VALUES (-1, 'N/A', 'Tienda No Identificada', 'Desconocido', 'Desconocido', 'Desconocido', 'Desconocido', 'Desconocido', 0, 0.00, 0);

INSERT INTO `DIM_PRODUCTO` (`id_producto`, `sku`, `nombre_producto`, `marca`, `marca_propia`, `categoria`, `subcategoria`, `departamento_comercial`, `precio_lista`)
VALUES (-1, 'SKU-UNKNOWN', 'Producto Desconocido / Genérico', 'Desconocido', FALSE, 'Desconocido', 'Desconocido', 'Desconocido', 0.00);

INSERT INTO `DIM_CAJA` (`id_caja`, `codigo_caja`, `numero_piso`, `zona_caja`, `tipo_caja`, `estado_caja`)
VALUES (-1, 'POS-UNKNOWN', 0, 'Desconocida', 'Desconocido', 'Inactiva');

INSERT INTO `DIM_PERSONAL` (`id_empleado`, `codigo_empleado`, `nombre_completo`, `cargo`, `turno_programado`, `tipo_contrato`)
VALUES (-1, 'EMP-UNKNOWN', 'Colaborador No Asignado', 'No identificado', 'No asignado', 'No asignado');

INSERT INTO `DIM_MEDIO_PAGO` (`id_medio_pago`, `tipo_medio_pago`, `canal_pago`, `es_tarjeta_ripley`, `emisor_financiero`)
VALUES (-1, 'Medio de Pago No Identificado', 'Desconocido', FALSE, 'Desconocido');

INSERT INTO `DIM_CLIENTE` (`id_cliente`, `codigo_cliente`, `tipo_cliente`, `segmento_fidelidad`, `rango_edad`, `genero`)
VALUES (-1, 'CLI-UNKNOWN', 'Cliente No Fidelizado / Anónimo', 'Sin Fidelizar', 'No especificado', 'No especificado');

-- -----------------------------------------------------------------------------
-- 3. TABLAS DE HECHOS (FACT TABLES)
-- -----------------------------------------------------------------------------

-- 3.1 Tabla de Hechos: FACT_VENTAS (Grano Atómico / Transaccional)
CREATE TABLE `FACT_VENTAS` (
    `id_hecho_venta` BIGINT NOT NULL AUTO_INCREMENT,
    `id_fecha` INT NOT NULL,
    `id_hora` INT NOT NULL,
    `id_tienda` INT NOT NULL,
    `id_producto` INT NOT NULL,
    `id_caja` INT NOT NULL,
    `id_empleado` INT NOT NULL,
    `id_medio_pago` INT NOT NULL,
    `id_cliente` INT NOT NULL,
    `numero_ticket` VARCHAR(30) NOT NULL,  -- Dimensión Degenerada
    `cantidad_unidades` INT NOT NULL DEFAULT 1,
    `precio_unitario_venta` DECIMAL(10,2) NOT NULL,
    `monto_descuento` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `subtotal_neto` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `monto_igv` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `monto_total_venta` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `costo_total_linea` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `margen_bruto` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `tiempo_espera_cola_seg` INT NOT NULL DEFAULT 0,
    `tiempo_atencion_caja_seg` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id_hecho_venta`),
    KEY `idx_fact_vnt_fecha` (`id_fecha`),
    KEY `idx_fact_vnt_hora` (`id_hora`),
    KEY `idx_fact_vnt_tienda` (`id_tienda`),
    KEY `idx_fact_vnt_producto` (`id_producto`),
    KEY `idx_fact_vnt_caja` (`id_caja`),
    KEY `idx_fact_vnt_empleado` (`id_empleado`),
    KEY `idx_fact_vnt_medio_pago` (`id_medio_pago`),
    KEY `idx_fact_vnt_cliente` (`id_cliente`),
    KEY `idx_fact_vnt_ticket` (`numero_ticket`),
    CONSTRAINT `fk_fact_vnt_fecha` FOREIGN KEY (`id_fecha`) REFERENCES `DIM_FECHA` (`id_fecha`),
    CONSTRAINT `fk_fact_vnt_hora` FOREIGN KEY (`id_hora`) REFERENCES `DIM_HORA` (`id_hora`),
    CONSTRAINT `fk_fact_vnt_tienda` FOREIGN KEY (`id_tienda`) REFERENCES `DIM_TIENDA` (`id_tienda`),
    CONSTRAINT `fk_fact_vnt_producto` FOREIGN KEY (`id_producto`) REFERENCES `DIM_PRODUCTO` (`id_producto`),
    CONSTRAINT `fk_fact_vnt_caja` FOREIGN KEY (`id_caja`) REFERENCES `DIM_CAJA` (`id_caja`),
    CONSTRAINT `fk_fact_vnt_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `DIM_PERSONAL` (`id_empleado`),
    CONSTRAINT `fk_fact_vnt_medio_pago` FOREIGN KEY (`id_medio_pago`) REFERENCES `DIM_MEDIO_PAGO` (`id_medio_pago`),
    CONSTRAINT `fk_fact_vnt_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `DIM_CLIENTE` (`id_cliente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.2 Tabla de Hechos: FACT_AFLUENCIA_TIENDA (Instantánea Periódica Horaria)
CREATE TABLE `FACT_AFLUENCIA_TIENDA` (
    `id_hecho_afluencia` BIGINT NOT NULL AUTO_INCREMENT,
    `id_fecha` INT NOT NULL,
    `id_hora` INT NOT NULL,
    `id_tienda` INT NOT NULL,
    `cantidad_personas_ingreso` INT NOT NULL DEFAULT 0,
    `cantidad_personas_salida` INT NOT NULL DEFAULT 0,
    `aforo_promedio_ocupado` INT NOT NULL DEFAULT 0,
    `porcentaje_saturacion_aforo` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    `cajas_activas_operando` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id_hecho_afluencia`),
    KEY `idx_fact_afl_fecha` (`id_fecha`),
    KEY `idx_fact_afl_hora` (`id_hora`),
    KEY `idx_fact_afl_tienda` (`id_tienda`),
    CONSTRAINT `fk_fact_afl_fecha` FOREIGN KEY (`id_fecha`) REFERENCES `DIM_FECHA` (`id_fecha`),
    CONSTRAINT `fk_fact_afl_hora` FOREIGN KEY (`id_hora`) REFERENCES `DIM_HORA` (`id_hora`),
    CONSTRAINT `fk_fact_afl_tienda` FOREIGN KEY (`id_tienda`) REFERENCES `DIM_TIENDA` (`id_tienda`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
