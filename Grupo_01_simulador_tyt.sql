-- =============================================================================
-- PROYECTO: SIMULADOR DE CUESTIONARIOS SABER TyT
-- PRIMERA ENTREGA: SCRIPT DDL DE BASE DE DATOS (SIN WARNINGS)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `simulador_tyt` 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE `simulador_tyt`;

-- -----------------------------------------------------------------------------
-- 1. TABLA: categorias
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `categorias`;
CREATE TABLE `categorias` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_unicode_ci,
  `activo` boolean NOT NULL DEFAULT TRUE,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. TABLA: cuestionarios
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `cuestionarios`;
CREATE TABLE `cuestionarios` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_unicode_ci,
  `fecha_apertura` datetime NOT NULL,
  `fecha_cierre` datetime NOT NULL,
  `tiempo_limite_minutos` int NOT NULL,
  `intentos_permitidos` int NOT NULL,
  `calificacion_maxima` decimal(5,2) NOT NULL,
  `calificacion_aprobacion` decimal(5,2) NOT NULL,
  `mezclar_preguntas` boolean NOT NULL DEFAULT FALSE,
  `mezclar_respuestas` boolean NOT NULL DEFAULT FALSE,
  `permitir_revision` boolean NOT NULL DEFAULT TRUE,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Borrador',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `chk_cuestionario_calif_aprob` CHECK (((`calificacion_aprobacion` >= 0) and (`calificacion_aprobacion` <= `calificacion_maxima`))),
  CONSTRAINT `chk_cuestionario_calif_max` CHECK ((`calificacion_maxima` > 0)),
  CONSTRAINT `chk_cuestionario_estado` CHECK ((`estado` in (_utf8mb4'Borrador',_utf8mb4'Programado',_utf8mb4'Disponible',_utf8mb4'Cerrado'))),
  CONSTRAINT `chk_cuestionario_fechas` CHECK ((`fecha_cierre` > `fecha_apertura`)),
  CONSTRAINT `chk_cuestionario_intentos` CHECK ((`intentos_permitidos` > 0)),
  CONSTRAINT `chk_cuestionario_tiempo` CHECK ((`tiempo_limite_minutos` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. TABLA: importaciones
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `importaciones`;
CREATE TABLE `importaciones` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre_archivo` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_carga` datetime NOT NULL,
  `total_filas` int NOT NULL DEFAULT '0',
  `total_validas` int NOT NULL DEFAULT '0',
  `total_errores` int NOT NULL DEFAULT '0',
  `detalle_log` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. TABLA: intentos
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `intentos`;
CREATE TABLE `intentos` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `cuestionario_id` bigint NOT NULL,
  `nombre_estudiante` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `codigo_estudiante` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `numero_intento` int NOT NULL DEFAULT '1',
  `fecha_inicio` datetime NOT NULL,
  `fecha_fin` datetime DEFAULT NULL,
  `puntaje_obtenido` decimal(5,2) DEFAULT NULL,
  `calificacion_final` decimal(5,2) DEFAULT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'En Progreso',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_intentos_cuestionario` (`cuestionario_id`),
  KEY `idx_intentos_estudiante` (`codigo_estudiante`),
  CONSTRAINT `fk_intentos_cuestionarios` FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionarios` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_intento_estado` CHECK ((`estado` in (_utf8mb4'En Progreso',_utf8mb4'Finalizado',_utf8mb4'Anulado'))),
  CONSTRAINT `chk_intento_numero` CHECK ((`numero_intento` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. TABLA: preguntas
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `preguntas`;
CREATE TABLE `preguntas` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `categoria_id` bigint NOT NULL,
  `tipo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `texto_base` text COLLATE utf8mb4_unicode_ci,
  `enunciado` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `retroalimentacion` text COLLATE utf8mb4_unicode_ci,
  `puntaje_base` decimal(5,2) NOT NULL DEFAULT '1.00',
  `activo` boolean NOT NULL DEFAULT TRUE,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_preguntas_categoria` (`categoria_id`),
  KEY `idx_preguntas_activo` (`activo`),
  CONSTRAINT `fk_preguntas_categorias` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_pregunta_puntaje` CHECK ((`puntaje_base` > 0)),
  CONSTRAINT `chk_pregunta_tipo` CHECK ((`tipo` in (_utf8mb4'MULTIPLE',_utf8mb4'VERDADERO_FALSO')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. TABLA: cuestionario_preguntas
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `cuestionario_preguntas`;
CREATE TABLE `cuestionario_preguntas` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `cuestionario_id` bigint NOT NULL,
  `pregunta_id` bigint NOT NULL,
  `orden` int NOT NULL DEFAULT '1',
  `puntaje_ponderado` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cuestionario_pregunta` (`cuestionario_id`,`pregunta_id`),
  KEY `idx_cp_cuestionario` (`cuestionario_id`),
  KEY `idx_cp_pregunta` (`pregunta_id`),
  CONSTRAINT `fk_cp_cuestionarios` FOREIGN KEY (`cuestionario_id`) REFERENCES `cuestionarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cp_preguntas` FOREIGN KEY (`pregunta_id`) REFERENCES `preguntas` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_cp_puntaje` CHECK ((`puntaje_ponderado` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 7. TABLA: opciones_respuesta
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `opciones_respuesta`;
CREATE TABLE `opciones_respuesta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `pregunta_id` bigint NOT NULL,
  `letra` char(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `texto` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `es_correcta` boolean NOT NULL DEFAULT FALSE,
  PRIMARY KEY (`id`),
  KEY `idx_opciones_pregunta` (`pregunta_id`),
  CONSTRAINT `fk_opciones_preguntas` FOREIGN KEY (`pregunta_id`) REFERENCES `preguntas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_opcion_letra` CHECK ((`letra` in (_utf8mb4'A',_utf8mb4'B',_utf8mb4'C',_utf8mb4'D')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 8. TABLA: respuestas_intento
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `respuestas_intento`;
CREATE TABLE `respuestas_intento` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `intento_id` bigint NOT NULL,
  `pregunta_id` bigint NOT NULL,
  `opcion_seleccionada_id` bigint DEFAULT NULL,
  `es_correcta` boolean NOT NULL DEFAULT FALSE,
  `puntaje_asignado` decimal(5,2) NOT NULL DEFAULT '0.00',
  `marcada_revision` boolean NOT NULL DEFAULT FALSE,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_intento_pregunta` (`intento_id`,`pregunta_id`),
  KEY `fk_respuestas_opciones` (`opcion_seleccionada_id`),
  KEY `idx_respuestas_intento` (`intento_id`),
  KEY `idx_respuestas_pregunta` (`pregunta_id`),
  CONSTRAINT `fk_respuestas_intentos` FOREIGN KEY (`intento_id`) REFERENCES `intentos` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_respuestas_opciones` FOREIGN KEY (`opcion_seleccionada_id`) REFERENCES `opciones_respuesta` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_respuestas_preguntas` FOREIGN KEY (`pregunta_id`) REFERENCES `preguntas` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
