-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: sistema_web
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add reporte',6,'add_reporte'),(22,'Can change reporte',6,'change_reporte'),(23,'Can delete reporte',6,'delete_reporte'),(24,'Can view reporte',6,'view_reporte'),(25,'Can add user',7,'add_usuario'),(26,'Can change user',7,'change_usuario'),(27,'Can delete user',7,'delete_usuario'),(28,'Can view user',7,'view_usuario'),(29,'Can add asistencia',8,'add_asistencia'),(30,'Can change asistencia',8,'change_asistencia'),(31,'Can delete asistencia',8,'delete_asistencia'),(32,'Can view asistencia',8,'view_asistencia'),(33,'Can add tarea',9,'add_tarea'),(34,'Can change tarea',9,'change_tarea'),(35,'Can delete tarea',9,'delete_tarea'),(36,'Can view tarea',9,'view_tarea'),(37,'Can add attendance summary',10,'add_attendancesummary'),(38,'Can change attendance summary',10,'change_attendancesummary'),(39,'Can delete attendance summary',10,'delete_attendancesummary'),(40,'Can view attendance summary',10,'view_attendancesummary'),(41,'Can add evento',11,'add_evento'),(42,'Can change evento',11,'change_evento'),(43,'Can delete evento',11,'delete_evento'),(44,'Can view evento',11,'view_evento'),(45,'Can add notification',12,'add_notification'),(46,'Can change notification',12,'change_notification'),(47,'Can delete notification',12,'delete_notification'),(48,'Can view notification',12,'view_notification'),(49,'Can add personal',13,'add_personal'),(50,'Can change personal',13,'change_personal'),(51,'Can delete personal',13,'delete_personal'),(52,'Can view personal',13,'view_personal');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_gestion_a` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_gestion_a` FOREIGN KEY (`user_id`) REFERENCES `gestion_asociacion_usuario` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'contenttypes','contenttype'),(8,'gestion_asociacion','asistencia'),(10,'gestion_asociacion','attendancesummary'),(11,'gestion_asociacion','evento'),(12,'gestion_asociacion','notification'),(13,'gestion_asociacion','personal'),(6,'gestion_asociacion','reporte'),(9,'gestion_asociacion','tarea'),(7,'gestion_asociacion','usuario'),(5,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2024-11-21 02:22:46.502198'),(2,'contenttypes','0002_remove_content_type_name','2024-11-21 02:22:46.564063'),(3,'auth','0001_initial','2024-11-21 02:22:46.825046'),(4,'auth','0002_alter_permission_name_max_length','2024-11-21 02:22:46.894387'),(5,'auth','0003_alter_user_email_max_length','2024-11-21 02:22:46.903389'),(6,'auth','0004_alter_user_username_opts','2024-11-21 02:22:46.911474'),(7,'auth','0005_alter_user_last_login_null','2024-11-21 02:22:46.919073'),(8,'auth','0006_require_contenttypes_0002','2024-11-21 02:22:46.923074'),(9,'auth','0007_alter_validators_add_error_messages','2024-11-21 02:22:46.930593'),(10,'auth','0008_alter_user_username_max_length','2024-11-21 02:22:46.948744'),(11,'auth','0009_alter_user_last_name_max_length','2024-11-21 02:22:46.957658'),(12,'auth','0010_alter_group_name_max_length','2024-11-21 02:22:46.977556'),(13,'auth','0011_update_proxy_permissions','2024-11-21 02:22:46.984557'),(14,'auth','0012_alter_user_first_name_max_length','2024-11-21 02:22:46.992558'),(15,'gestion_asociacion','0001_initial','2024-11-21 02:22:47.487359'),(16,'admin','0001_initial','2024-11-21 02:22:47.626688'),(17,'admin','0002_logentry_remove_auto_add','2024-11-21 02:22:47.634187'),(18,'admin','0003_logentry_add_action_flag_choices','2024-11-21 02:22:47.643115'),(19,'sessions','0001_initial','2024-11-21 02:22:47.678170'),(20,'gestion_asociacion','0002_attendancesummary_evento_notification_personal','2024-11-27 00:27:03.573044'),(21,'gestion_asociacion','0002_alter_attendancesummary_options_alter_evento_options_and_more','2025-01-29 03:18:06.195519'),(22,'gestion_asociacion','0003_alter_asistencia_options_and_more','2025-02-09 02:12:49.552632');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('0sppb6po6ud7coxkfypftllo2hypzu6f','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thKtk:PjsUgAcgAfxR2RDZqO6EfpCdc9_N64tJ42IfwXD78-8','2025-02-11 03:55:52.302844'),('0yn6r468lnkf59a3hi0uu4uhsmq8154u','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thNmB:Bc9iXE7hk5NkXJTA0oOotOk9eXOO55GYivAqnLuzE-E','2025-02-11 07:00:15.325727'),('3qtdgdv7xej819vzn5ln5fv1pht2lvwn','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thiW3:iNJfg-pdkCNg4Pw_GKAen1Vhq7_LlfXAV1kB10Cnfy8','2025-02-12 05:08:59.503142'),('5bfcoz28m1p2qii30lfgl1z8xqiqfx2z','eyJfcGFzc3dvcmRfcmVzZXRfdG9rZW4iOiJjbDB3bWwtMDBlYzJhMWIwOWMxODU1YzUwMGVhZTNkZjQxMDQxMjgifQ:1thfPI:gu_4vMpJOkYkqOojcLzsmC202WFg3Io48-lj4IM30tE','2025-02-12 01:49:48.090699'),('75atdgfskegca08n0639teiery752gs4','e30:1thvqD:BW864BSp3wzv1UsuspQ5j3qOQWXr5hqKgkLfgHOLkMI','2025-02-12 19:22:41.593655'),('77ymsqcu3ima1yij6z6bqn5o42o2pw9q','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thiyi:znzWLwu_1s3qn3VHUiTKuO5jFY58rvTQv5My5tuCV4Q','2025-02-12 05:38:36.771954'),('8v70wzvhxz2cg9sfzgoe6hfph0eo6rgj','eyJfcGFzc3dvcmRfcmVzZXRfdG9rZW4iOiJjbDEwMzctZWQ3YjA3MWYxZWE0NTQwNWRiZTUyOWQxNGJhZTJjZjEifQ:1thgJu:NIpIbQhSWsun82oq48n33Z-_M0CsRMu_URmQgaeBRJY','2025-02-12 02:48:18.537983'),('9vrt439qj4wy503kct5gude4hdgqgz2c','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thhin:4BKY_EnrSx17BX_fm42bsOkEd7wpElE-gPQBen2O9Ig','2025-02-12 04:18:05.933728'),('a4vnag8kqfab78espdu7jkeq8rpdgr5w','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thKuJ:uylx5qyticJstsw1Scyu7ODdEyV9GL0bg7QZJ0qHRxQ','2025-02-11 03:56:27.773681'),('g4ew6plxuw8d5wrk14jz59eiodqdjnbq','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thj99:ocPZ2x6VIG6Gkb14EE_8p-Bc3E1LKQLyQRDraQ2DtFs','2025-02-12 05:49:23.499623'),('h88y3aexmo181yqp25n2cwry48cgmz10','.eJxVjDsOwjAQBe_iGiI7cfyhpOcM1np3TQJRjOwABeLuBClN2jcz7yPCA2p950KhcOUlLPnOszgJnOTLl2NyNmlsvWmTkp4l9Mq7ru_JWW10G8VBBHguQ3hWLmGktdT7LQKuj39AN5ivucE8L2WMzV9pNlqbSyaezpu7OxigDmvdJYPWJMPGRwXgHekUnWeHqLWStufIVnHLTC5hlCixiwola0uJCcT3B4LdTbA:1theru:Cc5gz2TKLNeaSEeXb1V3Bt1igY5qE9NvyJCHPNXq7wU','2025-02-12 01:15:18.945681'),('iko5skuv3dnlzna3cc036ty1i2mk8gcr','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thOLi:8F9QDCKH2FnuhtOBZzAh0Uz-t1yT3uVty7xyhOiUNow','2025-02-11 07:36:58.466491'),('jmki7ohzpbom3o47glmup35g0ed9z3f1','.eJxVjMEOwiAQRP-FsyFtZSnr0bvfQBZ2kaqBpLQn47_bJj3oYS7z3sxbeVqX7Ncms59YXZRRp98uUHxK2QE_qNyrjrUs8xT0ruiDNn2rLK_r4f4dZGp5W5PpnJxHtH0cY-IA1gGJoKBNgZhsSojAyQwdyOAMMxCELYQJCXr1-QIHLDjk:1thgfA:zZtA939wKoC9DgTwDSa2OmbCr1cG0uYOZ7zSBdh8JhE','2025-02-12 03:10:16.330772'),('mqu6rqh7diaale0yefbbdt8ac35aej4o','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thi4I:c4Y8vARwXDm2QAhIeXfpler-jSy7DK2qvTHYopbTeeI','2025-02-12 04:40:18.840628'),('pj9cdqzfr5m7v7z28pmx3l9k8fkn2zw2','.eJxVjMEOwiAQRP-FsyFtZSnr0bvfQBZ2kaqBpLQn47_bJj3oYS7z3sxbeVqX7Ncms59YXZRRp98uUHxK2QE_qNyrjrUs8xT0ruiDNn2rLK_r4f4dZGp5W5PpnJxHtH0cY-IA1gGJoKBNgZhsSojAyQwdyOAMMxCELYQJCXr1-QIHLDjk:1thtJi:cBJmtGyp_-5ToRqgxn54bN0oemY27g9egts8CHd21i0','2025-02-12 16:40:58.323428'),('qq6iuumj48t2f53js76cjnep4rhal0jg','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thLQK:IKtq-aouBBM4Ya8aieOCJykqGdl9J3eThVFYWKZq6Yw','2025-02-11 04:29:32.477944'),('rd5cvr8dx1bpm8wyrvt9krs317pvpeyg','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thOWC:yeWyyYTUPwOi9DxIVMk0uFBblmRdhRbJC5VVNbf9Q-k','2025-02-11 07:47:48.217160'),('sav78q6loxasnpt2ez2b18d293li0md5','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thOtT:pDfYYVr-0PRnvzbvSOqhzs_UMPSG_eD4pH25_hJ4WYQ','2025-02-11 08:11:51.613532'),('uea848oczzd6tlhvowanh5e2av0cflnm','.eJxVjEEOwiAQRe_C2hAGhQGX7nuGhhlAqgaS0q6MdzckXej2v_f-W8xh38q897TOSxRXYcTpd6PAz1QHiI9Q701yq9u6kByKPGiXU4vpdTvcv4MSehm1wovLGnxksuDYozbKYwBHRlunjObkDWtCBLDn6CyFzA6RyKqMID5fw-Y3Jg:1thhY1:H2ARLRfNfTYyyh1O0ewE48P4F5QnAJqYejfiFFDn1YA','2025-02-12 04:06:57.100758');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_asistencia`
--

DROP TABLE IF EXISTS `gestion_asociacion_asistencia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_asistencia` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `hora_entrada` time(6) DEFAULT NULL,
  `hora_salida` time(6) DEFAULT NULL,
  `usuario_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `gestion_asociacion_a_usuario_id_9f93c013_fk_gestion_a` (`usuario_id`),
  CONSTRAINT `gestion_asociacion_a_usuario_id_9f93c013_fk_gestion_a` FOREIGN KEY (`usuario_id`) REFERENCES `gestion_asociacion_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_asistencia`
--

LOCK TABLES `gestion_asociacion_asistencia` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_asistencia` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_asistencia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_attendancesummary`
--

DROP TABLE IF EXISTS `gestion_asociacion_attendancesummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_attendancesummary` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `present` int NOT NULL,
  `absent` int NOT NULL,
  `late` int NOT NULL,
  `date` date NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_attendancesummary`
--

LOCK TABLES `gestion_asociacion_attendancesummary` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_attendancesummary` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_attendancesummary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_evento`
--

DROP TABLE IF EXISTS `gestion_asociacion_evento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_evento` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `titulo` varchar(100) NOT NULL,
  `fecha` date NOT NULL,
  `descripcion` longtext NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_evento`
--

LOCK TABLES `gestion_asociacion_evento` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_evento` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_evento` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_notification`
--

DROP TABLE IF EXISTS `gestion_asociacion_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `message` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_notification`
--

LOCK TABLES `gestion_asociacion_notification` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_notification` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_personal`
--

DROP TABLE IF EXISTS `gestion_asociacion_personal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_personal` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(254) NOT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `departamento` varchar(50) NOT NULL,
  `comentarios` longtext,
  `fecha_creacion` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_personal`
--

LOCK TABLES `gestion_asociacion_personal` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_personal` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_personal` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_reporte`
--

DROP TABLE IF EXISTS `gestion_asociacion_reporte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_reporte` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `titulo` varchar(200) NOT NULL,
  `contenido` longtext NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_reporte`
--

LOCK TABLES `gestion_asociacion_reporte` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_reporte` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_reporte` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_tarea`
--

DROP TABLE IF EXISTS `gestion_asociacion_tarea`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_tarea` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `descripcion` longtext NOT NULL,
  `fecha_asignada` date NOT NULL,
  `fecha_limite` date NOT NULL,
  `usuario_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `gestion_asociacion_t_usuario_id_66cf9c66_fk_gestion_a` (`usuario_id`),
  CONSTRAINT `gestion_asociacion_t_usuario_id_66cf9c66_fk_gestion_a` FOREIGN KEY (`usuario_id`) REFERENCES `gestion_asociacion_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_tarea`
--

LOCK TABLES `gestion_asociacion_tarea` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_tarea` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_tarea` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_usuario`
--

DROP TABLE IF EXISTS `gestion_asociacion_usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_usuario` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `direccion` longtext,
  `genero` varchar(10) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `rol` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_usuario`
--

LOCK TABLES `gestion_asociacion_usuario` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_usuario` DISABLE KEYS */;
INSERT INTO `gestion_asociacion_usuario` VALUES (1,'pbkdf2_sha256$870000$l7vyQZm2b59OyHPY9YhR1I$VajolQcNdfmItxD0au4ZUqWVpMo4kWsuCjMr2bbT/s0=',NULL,0,'churrito','Vanessa','Morales','vane@gmail.com',0,1,'2024-11-21 03:02:38.043853','5542126889','Calle tutifruta','F','2005-06-22','Miembro'),(2,'pbkdf2_sha256$870000$rzULn11XkjoBlxYUcdOV18$8htlsygmi6qlW1G+cM69Axz4PPMoST36wcY6ANiOGQA=',NULL,0,'fer','prueba','123','hteam284@gmail.com',0,1,'2024-12-12 03:28:12.637015','5543125678','Lucio amonos','M','2002-04-22','Miembro'),(3,'pbkdf2_sha256$870000$rGPrhaNIHHioDD2vQAHq4f$JLkqD/RSUMzQ8hDhNtcHBVYpYJxfBIzqOgXC6YB6rFA=','2024-12-14 02:27:53.992808',0,'Iwanol','Ivan','Hernandez','ivan@gmail.com',0,1,'2024-12-12 03:51:40.996289','5589086723','Pedro sola','M','2002-12-12','Miembro'),(4,'pbkdf2_sha256$870000$w66Z9y15AEGpuwy8mGo4gl$fLUxt/mWo++v++w0MH9ucpveipHZWST5ts56Gyp0QgI=','2025-02-11 16:41:15.644477',0,'InsanoFer','Fernando Gerardo','Morales Martinez','fernandoaz3519@gmail.com',0,1,'2025-01-30 22:10:58.171188','5510309901','21 de marzo #98 C.P 56607','M','2002-04-29','Miembro'),(5,'pbkdf2_sha256$870000$wofsRRcI4RrwADUflRDHMf$FWcyKUARVQweYU//svAZG/a91tv2JxV0J9peWR4RzYU=','2025-02-11 16:09:40.442629',0,'GranFer','Gerardo','Morales','fernando_mm@tesch.edu.mx',0,1,'2025-02-10 03:35:08.936984','5510309901','Pedrito Sola Cp.56607','M','2002-03-12','Administrador');
/*!40000 ALTER TABLE `gestion_asociacion_usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_usuario_groups`
--

DROP TABLE IF EXISTS `gestion_asociacion_usuario_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_usuario_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gestion_asociacion_usuar_usuario_id_group_id_ec4c174d_uniq` (`usuario_id`,`group_id`),
  KEY `gestion_asociacion_u_group_id_f2346aad_fk_auth_grou` (`group_id`),
  CONSTRAINT `gestion_asociacion_u_group_id_f2346aad_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `gestion_asociacion_u_usuario_id_e33fd979_fk_gestion_a` FOREIGN KEY (`usuario_id`) REFERENCES `gestion_asociacion_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_usuario_groups`
--

LOCK TABLES `gestion_asociacion_usuario_groups` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_usuario_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_usuario_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gestion_asociacion_usuario_user_permissions`
--

DROP TABLE IF EXISTS `gestion_asociacion_usuario_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gestion_asociacion_usuario_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gestion_asociacion_usuar_usuario_id_permission_id_cc564c2f_uniq` (`usuario_id`,`permission_id`),
  KEY `gestion_asociacion_u_permission_id_a716981e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `gestion_asociacion_u_permission_id_a716981e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `gestion_asociacion_u_usuario_id_d0dfe02f_fk_gestion_a` FOREIGN KEY (`usuario_id`) REFERENCES `gestion_asociacion_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gestion_asociacion_usuario_user_permissions`
--

LOCK TABLES `gestion_asociacion_usuario_user_permissions` WRITE;
/*!40000 ALTER TABLE `gestion_asociacion_usuario_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `gestion_asociacion_usuario_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-11 18:42:13
