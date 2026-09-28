-- =============================================================================
-- SISTEMA TRANSACCIONAL (OLTP) RIPLEY - ESQUEMA RELACIONAL (3NF)
-- Base de datos operativa fuente para el proyecto de Inteligencia de Negocios
-- Motor: MySQL 8.0+
-- Codificación: UTF-8 (utf8mb4)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `ripley_oltp`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `ripley_oltp`;

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. MÓDULO ESTRUCTURA ORGANIZACIONAL Y TIENDAS
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS `ASIGNACION_CAJA`;
DROP TABLE IF EXISTS `EMPLEADO`;
DROP TABLE IF EXISTS `ROL_EMPLEADO`;
DROP TABLE IF EXISTS `TURNO_TRABAJO`;
DROP TABLE IF EXISTS `CAJA_POS`;
DROP TABLE IF EXISTS `TIENDA`;
DROP TABLE IF EXISTS `UBIGEO`;

CREATE TABLE `UBIGEO` (
    `id_ubigeo` VARCHAR(6) NOT NULL,
    `departamento` VARCHAR(50) NOT NULL,
    `provincia` VARCHAR(50) NOT NULL,
    `distrito` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id_ubigeo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `TIENDA` (
    `id_tienda` INT AUTO_INCREMENT NOT NULL,
    `codigo_tienda` VARCHAR(10) NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `direccion` VARCHAR(200) NOT NULL,
    `id_ubigeo` VARCHAR(6) NOT NULL,
    `superficie_m2` DECIMAL(10,2) NOT NULL,
    `aforo_maximo` INT NOT NULL,
    `estado` VARCHAR(20) NOT NULL DEFAULT 'Activa',
    PRIMARY KEY (`id_tienda`),
    UNIQUE KEY `uk_tienda_codigo` (`codigo_tienda`),
    KEY `idx_tienda_ubigeo` (`id_ubigeo`),
    CONSTRAINT `fk_tienda_ubigeo` FOREIGN KEY (`id_ubigeo`) 
        REFERENCES `UBIGEO` (`id_ubigeo`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `CAJA_POS` (
    `id_caja` INT AUTO_INCREMENT NOT NULL,
    `id_tienda` INT NOT NULL,
    `numero_caja` INT NOT NULL,
    `tipo_caja` VARCHAR(30) NOT NULL,
    `piso_ubicacion` INT NOT NULL DEFAULT 1,
    `mac_address` VARCHAR(20) NULL,
    `estado` VARCHAR(20) NOT NULL DEFAULT 'Operativa',
    PRIMARY KEY (`id_caja`),
    UNIQUE KEY `uk_caja_mac` (`mac_address`),
    KEY `idx_caja_tienda` (`id_tienda`),
    CONSTRAINT `fk_caja_tienda` FOREIGN KEY (`id_tienda`) 
        REFERENCES `TIENDA` (`id_tienda`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `TURNO_TRABAJO` (
    `id_turno` INT AUTO_INCREMENT NOT NULL,
    `nombre_turno` VARCHAR(50) NOT NULL,
    `hora_inicio` TIME NOT NULL,
    `hora_fin` TIME NOT NULL,
    PRIMARY KEY (`id_turno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ROL_EMPLEADO` (
    `id_rol` INT AUTO_INCREMENT NOT NULL,
    `nombre_rol` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id_rol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `EMPLEADO` (
    `id_empleado` INT AUTO_INCREMENT NOT NULL,
    `dni` VARCHAR(15) NOT NULL,
    `nombres` VARCHAR(100) NOT NULL,
    `apellidos` VARCHAR(100) NOT NULL,
    `id_rol` INT NOT NULL,
    `id_tienda_base` INT NOT NULL,
    `fecha_ingreso` DATE NOT NULL,
    `estado` VARCHAR(20) NOT NULL DEFAULT 'Activo',
    PRIMARY KEY (`id_empleado`),
    UNIQUE KEY `uk_empleado_dni` (`dni`),
    KEY `idx_empleado_rol` (`id_rol`),
    KEY `idx_empleado_tienda` (`id_tienda_base`),
    CONSTRAINT `fk_empleado_rol` FOREIGN KEY (`id_rol`) 
        REFERENCES `ROL_EMPLEADO` (`id_rol`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_empleado_tienda` FOREIGN KEY (`id_tienda_base`) 
        REFERENCES `TIENDA` (`id_tienda`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ASIGNACION_CAJA` (
    `id_asignacion` BIGINT AUTO_INCREMENT NOT NULL,
    `id_caja` INT NOT NULL,
    `id_empleado` INT NOT NULL,
    `id_turno` INT NOT NULL,
    `fecha_operacion` DATE NOT NULL,
    `hora_apertura` DATETIME NOT NULL,
    `hora_cierre` DATETIME NULL,
    `saldo_inicial` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `saldo_final` DECIMAL(10,2) NULL,
    PRIMARY KEY (`id_asignacion`),
    KEY `idx_asig_caja` (`id_caja`),
    KEY `idx_asig_empleado` (`id_empleado`),
    KEY `idx_asig_turno` (`id_turno`),
    CONSTRAINT `fk_asig_caja` FOREIGN KEY (`id_caja`) 
        REFERENCES `CAJA_POS` (`id_caja`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_asig_empleado` FOREIGN KEY (`id_empleado`) 
        REFERENCES `EMPLEADO` (`id_empleado`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_asig_turno` FOREIGN KEY (`id_turno`) 
        REFERENCES `TURNO_TRABAJO` (`id_turno`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. MÓDULO CATÁLOGO DE PRODUCTOS E INVENTARIO
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS `INVENTARIO_TIENDA`;
DROP TABLE IF EXISTS `PRODUCTO`;
DROP TABLE IF EXISTS `MARCA`;
DROP TABLE IF EXISTS `SUBCATEGORIA`;
DROP TABLE IF EXISTS `CATEGORIA`;
DROP TABLE IF EXISTS `LINEA_COMERCIAL`;
DROP TABLE IF EXISTS `PROVEEDOR`;

CREATE TABLE `PROVEEDOR` (
    `id_proveedor` INT AUTO_INCREMENT NOT NULL,
    `ruc` VARCHAR(11) NOT NULL,
    `razon_social` VARCHAR(150) NOT NULL,
    `contacto_comercial` VARCHAR(100) NULL,
    `telefono` VARCHAR(20) NULL,
    `email` VARCHAR(100) NULL,
    `condicion_pago` VARCHAR(50) NULL,
    `estado` VARCHAR(20) NOT NULL DEFAULT 'Activo',
    PRIMARY KEY (`id_proveedor`),
    UNIQUE KEY `uk_proveedor_ruc` (`ruc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `LINEA_COMERCIAL` (
    `id_linea` INT AUTO_INCREMENT NOT NULL,
    `codigo_linea` VARCHAR(10) NOT NULL,
    `nombre_linea` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id_linea`),
    UNIQUE KEY `uk_linea_codigo` (`codigo_linea`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `CATEGORIA` (
    `id_categoria` INT AUTO_INCREMENT NOT NULL,
    `id_linea` INT NOT NULL,
    `nombre_categoria` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id_categoria`),
    KEY `idx_categoria_linea` (`id_linea`),
    CONSTRAINT `fk_categoria_linea` FOREIGN KEY (`id_linea`) 
        REFERENCES `LINEA_COMERCIAL` (`id_linea`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `SUBCATEGORIA` (
    `id_subcategoria` INT AUTO_INCREMENT NOT NULL,
    `id_categoria` INT NOT NULL,
    `nombre_subcategoria` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id_subcategoria`),
    KEY `idx_subcategoria_categoria` (`id_categoria`),
    CONSTRAINT `fk_subcat_categoria` FOREIGN KEY (`id_categoria`) 
        REFERENCES `CATEGORIA` (`id_categoria`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `MARCA` (
    `id_marca` INT AUTO_INCREMENT NOT NULL,
    `nombre_marca` VARCHAR(100) NOT NULL,
    `es_marca_propia` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (`id_marca`),
    UNIQUE KEY `uk_marca_nombre` (`nombre_marca`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `PRODUCTO` (
    `id_producto` BIGINT AUTO_INCREMENT NOT NULL,
    `sku` VARCHAR(30) NOT NULL,
    `codigo_barras` VARCHAR(50) NULL,
    `nombre_producto` VARCHAR(200) NOT NULL,
    `id_subcategoria` INT NOT NULL,
    `id_marca` INT NOT NULL,
    `id_proveedor` INT NOT NULL,
    `precio_lista` DECIMAL(10,2) NOT NULL,
    `costo_estandar` DECIMAL(10,2) NOT NULL,
    `requiere_despacho` BOOLEAN NOT NULL DEFAULT FALSE,
    `estado` VARCHAR(20) NOT NULL DEFAULT 'Activo',
    PRIMARY KEY (`id_producto`),
    UNIQUE KEY `uk_producto_sku` (`sku`),
    UNIQUE KEY `uk_producto_barras` (`codigo_barras`),
    KEY `idx_producto_subcat` (`id_subcategoria`),
    KEY `idx_producto_marca` (`id_marca`),
    KEY `idx_producto_prov` (`id_proveedor`),
    CONSTRAINT `fk_producto_subcat` FOREIGN KEY (`id_subcategoria`) 
        REFERENCES `SUBCATEGORIA` (`id_subcategoria`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_producto_marca` FOREIGN KEY (`id_marca`) 
        REFERENCES `MARCA` (`id_marca`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_producto_prov` FOREIGN KEY (`id_proveedor`) 
        REFERENCES `PROVEEDOR` (`id_proveedor`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `INVENTARIO_TIENDA` (
    `id_inventario` BIGINT AUTO_INCREMENT NOT NULL,
    `id_tienda` INT NOT NULL,
    `id_producto` BIGINT NOT NULL,
    `stock_piso_venta` INT NOT NULL DEFAULT 0,
    `stock_almacen` INT NOT NULL DEFAULT 0,
    `stock_comprometido` INT NOT NULL DEFAULT 0,
    `punto_reorden` INT NOT NULL DEFAULT 10,
    `ultima_actualizacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id_inventario`),
    UNIQUE KEY `uk_inventario_tienda_prod` (`id_tienda`, `id_producto`),
    KEY `idx_inv_producto` (`id_producto`),
    CONSTRAINT `fk_inv_tienda` FOREIGN KEY (`id_tienda`) 
        REFERENCES `TIENDA` (`id_tienda`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_inv_producto` FOREIGN KEY (`id_producto`) 
        REFERENCES `PRODUCTO` (`id_producto`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. MÓDULO CLIENTES Y FIDELIZACIÓN
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS `CLIENTE`;
DROP TABLE IF EXISTS `TIPO_CLIENTE`;
DROP TABLE IF EXISTS `TIPO_DOCUMENTO`;

CREATE TABLE `TIPO_DOCUMENTO` (
    `id_tipo_doc` INT AUTO_INCREMENT NOT NULL,
    `codigo_sunat` VARCHAR(5) NOT NULL,
    `descripcion` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id_tipo_doc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `TIPO_CLIENTE` (
    `id_tipo_cliente` INT AUTO_INCREMENT NOT NULL,
    `nombre_tipo` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id_tipo_cliente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `CLIENTE` (
    `id_cliente` BIGINT AUTO_INCREMENT NOT NULL,
    `id_tipo_doc` INT NOT NULL,
    `numero_documento` VARCHAR(20) NOT NULL,
    `nombres` VARCHAR(100) NOT NULL,
    `apellidos` VARCHAR(100) NULL,
    `email` VARCHAR(150) NULL,
    `telefono` VARCHAR(20) NULL,
    `id_tipo_cliente` INT NOT NULL,
    `es_titular_tarjeta_ripley` BOOLEAN NOT NULL DEFAULT FALSE,
    `puntos_ripley_acumulados` INT NOT NULL DEFAULT 0,
    `fecha_registro` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id_cliente`),
    UNIQUE KEY `uk_cliente_doc` (`id_tipo_doc`, `numero_documento`),
    KEY `idx_cliente_tipo` (`id_tipo_cliente`),
    CONSTRAINT `fk_cliente_tipodoc` FOREIGN KEY (`id_tipo_doc`) 
        REFERENCES `TIPO_DOCUMENTO` (`id_tipo_doc`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_cliente_tipocliente` FOREIGN KEY (`id_tipo_cliente`) 
        REFERENCES `TIPO_CLIENTE` (`id_tipo_cliente`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. MÓDULO OPERATIVO DE VENTAS Y CAJAS (POS)
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS `PAGO_COMPROBANTE`;
DROP TABLE IF EXISTS `DETALLE_COMPROBANTE`;
DROP TABLE IF EXISTS `COMPROBANTE_PAGO`;
DROP TABLE IF EXISTS `METODO_PAGO`;

CREATE TABLE `METODO_PAGO` (
    `id_metodo_pago` INT AUTO_INCREMENT NOT NULL,
    `codigo_metodo` VARCHAR(20) NOT NULL,
    `descripcion` VARCHAR(100) NOT NULL,
    `aplica_comision` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (`id_metodo_pago`),
    UNIQUE KEY `uk_metodo_codigo` (`codigo_metodo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `COMPROBANTE_PAGO` (
    `id_comprobante` BIGINT AUTO_INCREMENT NOT NULL,
    `id_tienda` INT NOT NULL,
    `id_caja` INT NOT NULL,
    `id_empleado` INT NOT NULL,
    `id_cliente` BIGINT NOT NULL,
    `id_asignacion` BIGINT NOT NULL,
    `tipo_comprobante` VARCHAR(20) NOT NULL,
    `serie` VARCHAR(5) NOT NULL,
    `numero_correlativo` BIGINT NOT NULL,
    `fecha_hora_inicio_atencion` DATETIME NOT NULL,
    `fecha_hora_emision` DATETIME NOT NULL,
    `tiempo_atencion_segundos` INT NOT NULL,
    `subtotal_gravado` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    `igv` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    `total_descuento` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    `monto_total` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    `estado` VARCHAR(20) NOT NULL DEFAULT 'Emitido',
    PRIMARY KEY (`id_comprobante`),
    UNIQUE KEY `uk_comprobante_fiscal` (`tipo_comprobante`, `serie`, `numero_correlativo`),
    KEY `idx_comp_tienda` (`id_tienda`),
    KEY `idx_comp_caja` (`id_caja`),
    KEY `idx_comp_empleado` (`id_empleado`),
    KEY `idx_comp_cliente` (`id_cliente`),
    KEY `idx_comp_asignacion` (`id_asignacion`),
    KEY `idx_comp_fecha_emision` (`fecha_hora_emision`),
    CONSTRAINT `fk_comp_tienda` FOREIGN KEY (`id_tienda`) 
        REFERENCES `TIENDA` (`id_tienda`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_comp_caja` FOREIGN KEY (`id_caja`) 
        REFERENCES `CAJA_POS` (`id_caja`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_comp_empleado` FOREIGN KEY (`id_empleado`) 
        REFERENCES `EMPLEADO` (`id_empleado`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_comp_cliente` FOREIGN KEY (`id_cliente`) 
        REFERENCES `CLIENTE` (`id_cliente`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_comp_asig` FOREIGN KEY (`id_asignacion`) 
        REFERENCES `ASIGNACION_CAJA` (`id_asignacion`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `DETALLE_COMPROBANTE` (
    `id_detalle` BIGINT AUTO_INCREMENT NOT NULL,
    `id_comprobante` BIGINT NOT NULL,
    `id_producto` BIGINT NOT NULL,
    `cantidad` INT NOT NULL DEFAULT 1,
    `precio_unitario_venta` DECIMAL(10,2) NOT NULL,
    `costo_unitario_historico` DECIMAL(10,2) NOT NULL,
    `descuento_unitario` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `subtotal_linea` DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (`id_detalle`),
    KEY `idx_det_comprobante` (`id_comprobante`),
    KEY `idx_det_producto` (`id_producto`),
    CONSTRAINT `fk_det_comprobante` FOREIGN KEY (`id_comprobante`) 
        REFERENCES `COMPROBANTE_PAGO` (`id_comprobante`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_det_producto` FOREIGN KEY (`id_producto`) 
        REFERENCES `PRODUCTO` (`id_producto`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `PAGO_COMPROBANTE` (
    `id_pago` BIGINT AUTO_INCREMENT NOT NULL,
    `id_comprobante` BIGINT NOT NULL,
    `id_metodo_pago` INT NOT NULL,
    `monto_pagado` DECIMAL(10,2) NOT NULL,
    `numero_operacion_pos` VARCHAR(50) NULL,
    `fecha_hora_pago` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id_pago`),
    KEY `idx_pago_comprobante` (`id_comprobante`),
    KEY `idx_pago_metodo` (`id_metodo_pago`),
    CONSTRAINT `fk_pago_comprobante` FOREIGN KEY (`id_comprobante`) 
        REFERENCES `COMPROBANTE_PAGO` (`id_comprobante`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_pago_metodo` FOREIGN KEY (`id_metodo_pago`) 
        REFERENCES `METODO_PAGO` (`id_metodo_pago`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. MÓDULO AFLUENCIA, SENSORES IOT Y TRÁFICO PEATONAL
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS `LOG_AFLUENCIA_IOT`;
DROP TABLE IF EXISTS `DISPOSITIVO_SENSOR`;
DROP TABLE IF EXISTS `ZONA_TIENDA`;

CREATE TABLE `ZONA_TIENDA` (
    `id_zona` INT AUTO_INCREMENT NOT NULL,
    `id_tienda` INT NOT NULL,
    `nombre_zona` VARCHAR(100) NOT NULL,
    `tipo_zona` VARCHAR(30) NOT NULL,
    `aforo_limite` INT NOT NULL,
    PRIMARY KEY (`id_zona`),
    KEY `idx_zona_tienda` (`id_tienda`),
    CONSTRAINT `fk_zona_tienda` FOREIGN KEY (`id_tienda`) 
        REFERENCES `TIENDA` (`id_tienda`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `DISPOSITIVO_SENSOR` (
    `id_dispositivo` INT AUTO_INCREMENT NOT NULL,
    `id_zona` INT NOT NULL,
    `codigo_sensor` VARCHAR(50) NOT NULL,
    `tipo_sensor` VARCHAR(50) NOT NULL,
    `ip_dispositivo` VARCHAR(20) NOT NULL,
    `estado` VARCHAR(20) NOT NULL DEFAULT 'Activo',
    PRIMARY KEY (`id_dispositivo`),
    UNIQUE KEY `uk_sensor_codigo` (`codigo_sensor`),
    KEY `idx_sensor_zona` (`id_zona`),
    CONSTRAINT `fk_sensor_zona` FOREIGN KEY (`id_zona`) 
        REFERENCES `ZONA_TIENDA` (`id_zona`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `LOG_AFLUENCIA_IOT` (
    `id_log` BIGINT AUTO_INCREMENT NOT NULL,
    `id_dispositivo` INT NOT NULL,
    `fecha_hora_lectura` DATETIME NOT NULL,
    `conteo_entradas` INT NOT NULL DEFAULT 0,
    `conteo_salidas` INT NOT NULL DEFAULT 0,
    `aforo_instantaneo_calculado` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id_log`),
    KEY `idx_log_sensor` (`id_dispositivo`),
    KEY `idx_log_fecha_lectura` (`fecha_hora_lectura`),
    CONSTRAINT `fk_log_sensor` FOREIGN KEY (`id_dispositivo`) 
        REFERENCES `DISPOSITIVO_SENSOR` (`id_dispositivo`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
