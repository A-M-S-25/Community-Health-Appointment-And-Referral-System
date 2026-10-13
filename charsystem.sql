-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 13, 2026 at 02:06 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `charsystem`
--

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `appointment_id` int(10) UNSIGNED NOT NULL,
  `referral_id` int(10) UNSIGNED DEFAULT NULL,
  `facility_id` int(10) UNSIGNED NOT NULL,
  `appointment_datetime` datetime NOT NULL,
  `is_locked` tinyint(1) NOT NULL DEFAULT 0,
  `patient_id` int(10) UNSIGNED DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `appointments`
--

INSERT INTO `appointments` (`appointment_id`, `referral_id`, `facility_id`, `appointment_datetime`, `is_locked`, `patient_id`) VALUES
(1, 1, 3, '2026-10-15 10:30:00', 0, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `appointment_slots`
--

CREATE TABLE `appointment_slots` (
  `slot_id` int(10) UNSIGNED NOT NULL,
  `facility_id` int(10) UNSIGNED NOT NULL,
  `appointment_datetime` datetime NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Available',
  `created_by` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `appointment_slots`
--

INSERT INTO `appointment_slots` (`slot_id`, `facility_id`, `appointment_datetime`, `status`, `created_by`) VALUES
(1, 3, '2027-01-01 09:00:00', 'Available', 3),
(2, 9, '2026-10-13 23:20:00', 'Booked', 5),
(3, 9, '2026-10-14 13:21:00', 'Available', 5);

-- --------------------------------------------------------

--
-- Table structure for table `audit_logs`
--

CREATE TABLE `audit_logs` (
  `audit_id` int(10) UNSIGNED NOT NULL,
  `worker_id` int(10) UNSIGNED DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `resource_type` varchar(50) NOT NULL,
  `resource_id` varchar(100) DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`metadata`)),
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `audit_logs`
--

INSERT INTO `audit_logs` (`audit_id`, `worker_id`, `action`, `resource_type`, `resource_id`, `metadata`, `ip_address`, `created_at`) VALUES
(1, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 06:47:03'),
(2, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 06:48:45'),
(3, 3, 'export', 'referrals', NULL, '{}', '127.0.0.1', '2026-10-12 06:48:45'),
(4, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 06:50:26'),
(5, 3, 'book', 'appointment_slot', '1', '{}', '127.0.0.1', '2026-10-12 06:50:26'),
(6, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 06:51:21'),
(7, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 07:00:35'),
(8, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 07:01:01'),
(9, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 07:01:39'),
(10, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 07:41:39'),
(11, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 07:59:15'),
(12, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 07:59:34'),
(13, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 08:20:16'),
(14, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 08:24:09'),
(15, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 08:26:45'),
(16, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 08:52:31'),
(17, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 08:54:36'),
(18, 2, 'view', 'patient', '1', '{}', '127.0.0.1', '2026-10-12 08:55:42'),
(19, 2, 'view', 'patient', '1', '{}', '127.0.0.1', '2026-10-12 08:55:42'),
(20, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 08:56:16'),
(21, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 09:01:34'),
(22, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 09:26:48'),
(23, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 09:32:35'),
(24, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 09:33:23'),
(25, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 10:06:52'),
(26, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 10:08:07'),
(27, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 10:08:40'),
(28, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 10:52:04'),
(29, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 10:53:15'),
(30, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 10:58:43'),
(31, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 11:14:04'),
(32, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 11:15:25'),
(33, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 11:16:43'),
(34, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 11:17:28'),
(35, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 11:22:26'),
(36, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 11:36:11'),
(37, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 11:36:48'),
(38, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 11:48:07'),
(39, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 11:50:41'),
(40, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 11:51:17'),
(41, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 11:51:43'),
(42, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 11:54:33'),
(43, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 12:01:10'),
(44, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 12:08:36'),
(45, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 12:21:19'),
(46, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 12:21:52'),
(47, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 12:28:13'),
(48, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 12:28:58'),
(49, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 12:29:29'),
(50, 3, 'update', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 12:32:38'),
(51, 3, 'update', 'facility', '1', '{}', '127.0.0.1', '2026-10-12 12:35:52'),
(52, 3, 'update', 'facility', '1', '{}', '127.0.0.1', '2026-10-12 12:36:15'),
(53, 3, 'update', 'facility', '5', '{}', '127.0.0.1', '2026-10-12 12:38:38'),
(54, 3, 'update', 'facility', '1', '{}', '127.0.0.1', '2026-10-12 12:40:10'),
(55, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 12:58:00'),
(56, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 13:21:01'),
(57, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 13:23:15'),
(58, 1, 'view', 'referral', '1', '{}', '127.0.0.1', '2026-10-12 13:23:25'),
(59, 1, 'view', 'patient', '1', '{}', '127.0.0.1', '2026-10-12 13:23:32'),
(60, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 13:24:02'),
(61, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 13:33:36'),
(62, 3, 'update', 'facility', '6', '{}', '127.0.0.1', '2026-10-12 13:53:05'),
(63, 3, 'update', 'facility', '7', '{}', '127.0.0.1', '2026-10-12 13:56:16'),
(64, 3, 'update', 'facility', '8', '{}', '127.0.0.1', '2026-10-12 13:59:31'),
(65, 3, 'update', 'facility', '9', '{}', '127.0.0.1', '2026-10-12 14:01:23'),
(66, 3, 'update', 'facility', '10', '{}', '127.0.0.1', '2026-10-12 14:02:51'),
(67, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 14:05:39'),
(68, 3, 'update', 'facility', '11', '{}', '127.0.0.1', '2026-10-12 14:07:50'),
(69, 3, 'update', 'facility', '12', '{}', '127.0.0.1', '2026-10-12 14:09:22'),
(70, 3, 'update', 'facility', '13', '{}', '127.0.0.1', '2026-10-12 14:10:45'),
(71, 3, 'update', 'facility', '4', '{}', '127.0.0.1', '2026-10-12 14:12:20'),
(72, 3, 'update', 'facility', '14', '{}', '127.0.0.1', '2026-10-12 14:13:45'),
(73, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 14:16:09'),
(74, 3, 'update', 'worker', '4', '{}', '127.0.0.1', '2026-10-12 14:18:09'),
(75, 4, 'login', 'worker', '4', '{}', '127.0.0.1', '2026-10-12 14:19:22'),
(76, 4, 'create', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 14:21:23'),
(77, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 14:22:27'),
(78, 2, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 14:23:49'),
(79, 2, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 14:23:49'),
(80, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 14:25:14'),
(81, 1, 'view', 'referral', '1', '{}', '127.0.0.1', '2026-10-12 14:25:55'),
(82, 4, 'login', 'worker', '4', '{}', '127.0.0.1', '2026-10-12 14:26:34'),
(83, 4, 'login', 'worker', '4', '{}', '127.0.0.1', '2026-10-12 15:08:02'),
(84, 4, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 15:08:39'),
(85, 4, 'create', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 15:09:27'),
(86, 4, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 15:09:40'),
(87, 4, 'login', 'worker', '4', '{}', '127.0.0.1', '2026-10-12 16:40:59'),
(88, 4, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 16:52:54'),
(89, 4, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 16:54:27'),
(90, 4, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 17:01:17'),
(91, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 18:27:53'),
(92, 1, 'view', 'patient', '1', '{}', '127.0.0.1', '2026-10-12 18:30:03'),
(93, 4, 'login', 'worker', '4', '{}', '127.0.0.1', '2026-10-12 18:30:40'),
(94, 4, 'create', 'referral', '2', '{}', '127.0.0.1', '2026-10-12 18:32:09'),
(95, 4, 'view', 'referral', '2', '{}', '127.0.0.1', '2026-10-12 18:32:18'),
(96, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 18:33:08'),
(97, 5, 'login', 'worker', '5', '{}', '127.0.0.1', '2026-10-12 18:36:35'),
(98, 5, 'view', 'referral', '2', '{}', '127.0.0.1', '2026-10-12 18:36:50'),
(99, 5, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 18:37:29'),
(100, 5, 'view', 'referral', '2', '{}', '127.0.0.1', '2026-10-12 18:37:40'),
(101, 5, 'login', 'worker', '5', '{}', '127.0.0.1', '2026-10-12 19:29:48'),
(102, 5, 'view', 'referral', '2', '{}', '127.0.0.1', '2026-10-12 19:30:18'),
(103, 5, 'view', 'referral', '2', '{}', '127.0.0.1', '2026-10-12 19:31:44'),
(104, 5, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 19:31:57'),
(105, 1, 'login', 'worker', '1', '{}', '127.0.0.1', '2026-10-12 19:35:21'),
(106, 2, 'login', 'worker', '2', '{}', '127.0.0.1', '2026-10-12 19:36:14'),
(107, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 19:37:39'),
(108, 3, 'export', 'referrals', NULL, '{}', '127.0.0.1', '2026-10-12 19:39:43'),
(109, 3, 'export', 'referrals', NULL, '{}', '127.0.0.1', '2026-10-12 19:39:53'),
(110, 5, 'login', 'worker', '5', '{}', '127.0.0.1', '2026-10-12 20:06:10'),
(111, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-12 20:14:14'),
(112, 5, 'login', 'worker', '5', '{}', '127.0.0.1', '2026-10-12 20:20:01'),
(113, 5, 'status_change', 'referral', '2', '{}', '127.0.0.1', '2026-10-12 20:20:32'),
(114, 5, 'book', 'appointment_slot', '2', '{}', '127.0.0.1', '2026-10-12 20:20:41'),
(115, 4, 'login', 'worker', '4', '{}', '127.0.0.1', '2026-10-12 20:21:27'),
(116, 4, 'view', 'referral', '2', '{}', '127.0.0.1', '2026-10-12 20:21:58'),
(117, 4, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 20:22:30'),
(118, 4, 'view', 'patient', '2', '{}', '127.0.0.1', '2026-10-12 20:22:55'),
(119, 5, 'login', 'worker', '5', '{}', '127.0.0.1', '2026-10-13 10:20:53'),
(120, 5, 'view', 'referral', '2', '{}', '127.0.0.1', '2026-10-13 10:21:10'),
(121, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-13 10:24:13'),
(122, 5, 'login', 'worker', '5', '{}', '127.0.0.1', '2026-10-13 11:14:16'),
(123, 5, 'status_change', 'appointment', '2', '{}', '127.0.0.1', '2026-10-13 11:14:50'),
(124, 3, 'login', 'worker', '3', '{}', '127.0.0.1', '2026-10-13 11:32:36'),
(125, 3, 'status_change', 'appointment', '1', '{}', '127.0.0.1', '2026-10-13 11:34:15');

-- --------------------------------------------------------

--
-- Table structure for table `community_health_units`
--

CREATE TABLE `community_health_units` (
  `community_unit_id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL,
  `location` varchar(150) NOT NULL,
  `is_active` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `community_health_units`
--

INSERT INTO `community_health_units` (`community_unit_id`, `name`, `location`, `is_active`) VALUES
(1, 'Community Health Unit', 'Unspecified', 1),
(2, 'Laini Saba Community Health Unit', 'Laini Saba ward, Kibera, Nairobi County', 1),
(3, 'Gatwekera Community Health Unit', 'Gatwekera village, Kibera, Nairobi County', 1);

-- --------------------------------------------------------

--
-- Table structure for table `facilities`
--

CREATE TABLE `facilities` (
  `facility_id` int(10) UNSIGNED NOT NULL,
  `name` varchar(150) NOT NULL,
  `tier_level` tinyint(3) UNSIGNED NOT NULL,
  `contact_info` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`contact_info`)),
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `capacity` int(10) UNSIGNED NOT NULL DEFAULT 1
) ;

--
-- Dumping data for table `facilities`
--

INSERT INTO `facilities` (`facility_id`, `name`, `tier_level`, `contact_info`, `is_active`, `capacity`) VALUES
(1, 'Kibera Community Unit', 2, '{\"location\": \"Kibera\"}', 1, 10),
(2, 'Muguga Health Centre', 2, '{\"location\": \"Kibera\"}', 1, 1),
(3, 'Kisumu County Referral Hospital', 5, '{\"location\": \"Kisumu\"}', 1, 1),
(4, 'Kenyatta National Hospital', 6, '\"{\\\"phone\\\":\\\"+254 20 2726300\\\",\\\"email\\\":\\\"knhadmin@knh.or.ke\\\",\\\"location\\\":\\\"Upper Hill, Nairobi County\\\"}\"', 1, 1800),
(5, 'Test Facility', 2, '\"{\\\"location\\\":\\\"Test\\\"}\"', 1, 1),
(6, 'Uthiru Dispensary', 2, '\"{\\\"phone\\\":\\\"+254202210871\\\",\\\"email\\\":\\\"health@kiambu.go.ke\\\",\\\"location\\\":\\\"Uthiru, Kiambu County\\\"}\"', 1, 1),
(7, 'Mukuru Kwa Njenga Dispensary', 2, '\"{\\\"phone\\\":\\\"+254202224281\\\",\\\"email\\\":\\\"health@nairobi.go.ke\\\",\\\"location\\\":\\\"Embakasi South, Nairobi County\\\"}\"', 1, 2),
(8, 'Lang\'ata Health Centre', 3, '\"{\\\"phone\\\":\\\"+254 20 6002165\\\",\\\"email\\\":\\\"health@nairobi.go.ke\\\",\\\"location\\\":\\\"Lang\'ata, Nairobi County\\\"}\"', 1, 16),
(9, 'Kangemi Health Centre', 3, '\"{\\\"phone\\\":\\\"+254 20 4441584\\\",\\\"email\\\":\\\"info@nairobi.go.ke\\\",\\\"location\\\":\\\"Westlands, Nairobi County\\\"}\"', 1, 12),
(10, 'Mama Lucy Kibaki Hospital', 4, '\"{\\\"phone\\\":\\\"+254 719 073 000\\\",\\\"email\\\":\\\"info@mamalucykibakihospital.or.ke\\\",\\\"location\\\":\\\"Umoja II, Embakasi West, Nairobi County\\\"}\"', 1, 120),
(11, 'Mbagathi County Hospital', 4, '\"{\\\"phone\\\":\\\"+254 20 2724712\\\",\\\"email\\\":\\\"info@mbagathihospital.go.ke\\\",\\\"location\\\":\\\"Kenyatta Golf Course, Dagoretti North, Nairobi County\\\"}\"', 1, 200),
(12, 'Machakos Level 5 Hospital', 5, '\"{\\\"phone\\\":\\\"+254 44 21013\\\",\\\"email\\\":\\\"info@machakosgovernment.co.ke\\\",\\\"location\\\":\\\"Machakos Town, Machakos County\\\"}\"', 1, 400),
(13, 'Nakuru County Referral Hospital', 5, '\"{\\\"phone\\\":\\\"+254 51 2212361\\\",\\\"email\\\":\\\"info@nakuru.go.ke\\\",\\\"location\\\":\\\"Nakuru Town, Nakuru County\\\"}\"', 1, 800),
(14, 'Moi Teaching and Referral Hospital', 6, '\"{\\\"phone\\\":\\\"+254 53 2033471\\\",\\\"email\\\":\\\"ceo@mtrh.go.ke\\\",\\\"location\\\":\\\"Nandi Road, Eldoret, Uasin Gishu County\\\"}\"', 1, 1000);

-- --------------------------------------------------------

--
-- Table structure for table `healthcare_workers`
--

CREATE TABLE `healthcare_workers` (
  `worker_id` int(10) UNSIGNED NOT NULL,
  `facility_id` int(10) UNSIGNED DEFAULT NULL,
  `username` varchar(120) NOT NULL,
  `role` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `last_login_at` datetime DEFAULT NULL,
  `community_unit_id` int(10) UNSIGNED DEFAULT NULL
) ;

--
-- Dumping data for table `healthcare_workers`
--

INSERT INTO `healthcare_workers` (`worker_id`, `facility_id`, `username`, `role`, `password_hash`, `is_active`, `last_login_at`, `community_unit_id`) VALUES
(1, NULL, 'chp01', 'L1', 'scrypt:32768:8:1$2zPbx3ZpZoWGzSdz$39fa4a8d4a54bc23f0e7ece6efae7475cd0e192700d09245f11c7bfb7f3584886468d91f619232cfa935f55164492f2b9aa489d1395afe0d5d859a392aa5d7c9', 1, '2026-10-12 19:35:21', 1),
(2, 2, 'nurse02', 'L2', 'scrypt:32768:8:1$l2grvF7YuN0nj3AU$b4f0dcfd7371195e4c4a6eb46344d6911d98035f3f9ab0fb12d955d7d490ce8e4430727c35eb8c271960bcb8cdc5003282c773632a4a039d335210fdb2d0f2b8', 1, '2026-10-12 19:36:14', NULL),
(3, NULL, 'admin01', 'Admin', 'scrypt:32768:8:1$VD6PrptAWSrWPgG8$c8c808daee03e7b08f87b8001348a4d590bc77e0395daaf4c1bae699022cdeb350c3b17cab2400428be49ff7ef35d742dedfe9dc508f576a571b08424a9292f1', 1, '2026-10-13 11:32:36', NULL),
(4, NULL, 'Peter Gakuru', 'L1', 'scrypt:32768:8:1$4aookiCL1O69qEt3$591082d6d5eb66f0563afce4e807449bc74df1b661c0c5c6dd6e53e69102f21fe37b1af4ea83f0c3358ca836bd2ea981a4150e53aadeed2d75c89d187518b7ce', 1, '2026-10-12 20:21:27', 2),
(5, 9, 'Lilian Savai', 'L3', 'scrypt:32768:8:1$ZNmq8G9T4KQo3wIW$68a3ecf1fce29e3e7cb696ba69f99622f1380d3245ad71c1bbbeb253247b08dbbfd110f9b37fa3acbb6f4a0c3620e9edcb7177a562605dfd9bd460b9225cba7e', 1, '2026-10-13 11:14:16', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `patients`
--

CREATE TABLE `patients` (
  `patient_id` int(10) UNSIGNED NOT NULL,
  `phone_number` varchar(30) NOT NULL,
  `demographics` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`demographics`)),
  `community_unit_id` int(10) UNSIGNED DEFAULT NULL,
  `triage_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '{}' CHECK (json_valid(`triage_data`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `patients`
--

INSERT INTO `patients` (`patient_id`, `phone_number`, `demographics`, `community_unit_id`, `triage_data`) VALUES
(1, '+254700000001', '{\"name\": \"Jane Doe\", \"age\": 34}', NULL, '{}'),
(2, '+254712345678', '{\"name\": \"Mad Max\", \"age\": \"20\", \"phone_number\": \"+254712345678\"}', 2, '{}');

-- --------------------------------------------------------

--
-- Table structure for table `patient_admissions`
--

CREATE TABLE `patient_admissions` (
  `admission_id` int(10) UNSIGNED NOT NULL,
  `patient_id` int(10) UNSIGNED NOT NULL,
  `facility_id` int(10) UNSIGNED NOT NULL,
  `admitted_at` datetime NOT NULL,
  `discharged_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `referrals`
--

CREATE TABLE `referrals` (
  `referral_id` int(10) UNSIGNED NOT NULL,
  `patient_id` int(10) UNSIGNED NOT NULL,
  `origin_facility_id` int(10) UNSIGNED DEFAULT NULL,
  `destination_facility_id` int(10) UNSIGNED NOT NULL,
  `triage_notes` text NOT NULL,
  `status` varchar(30) NOT NULL DEFAULT 'Draft',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `origin_community_unit_id` int(10) UNSIGNED DEFAULT NULL
) ;

--
-- Dumping data for table `referrals`
--

INSERT INTO `referrals` (`referral_id`, `patient_id`, `origin_facility_id`, `destination_facility_id`, `triage_notes`, `status`, `created_at`, `origin_community_unit_id`) VALUES
(1, 1, NULL, 3, 'Fever and cough for 3 days', 'Cancelled', '2026-10-12 09:48:19', 1),
(2, 2, NULL, 9, 'Head Injury', 'Completed', '2026-10-12 18:32:09', 2);

-- --------------------------------------------------------

--
-- Table structure for table `referral_appointments`
--

CREATE TABLE `referral_appointments` (
  `booking_id` int(10) UNSIGNED NOT NULL,
  `referral_id` int(10) UNSIGNED NOT NULL,
  `slot_id` int(10) UNSIGNED NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Booked',
  `booked_by` int(10) UNSIGNED NOT NULL,
  `booked_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `referral_appointments`
--

INSERT INTO `referral_appointments` (`booking_id`, `referral_id`, `slot_id`, `status`, `booked_by`, `booked_at`) VALUES
(1, 1, 1, 'Cancelled', 3, '2026-10-12 06:50:26'),
(2, 2, 2, 'Completed', 5, '2026-10-12 20:20:41');

-- --------------------------------------------------------

--
-- Table structure for table `sms_messages`
--

CREATE TABLE `sms_messages` (
  `message_id` int(10) UNSIGNED NOT NULL,
  `recipient` varchar(30) NOT NULL,
  `body` text NOT NULL,
  `message_type` varchar(50) NOT NULL,
  `provider_message_id` varchar(120) DEFAULT NULL,
  `status` varchar(30) NOT NULL DEFAULT 'Queued',
  `retry_count` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `error_message` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `sms_messages`
--

INSERT INTO `sms_messages` (`message_id`, `recipient`, `body`, `message_type`, `provider_message_id`, `status`, `retry_count`, `error_message`, `created_at`, `updated_at`) VALUES
(1, '+254700000001', 'Your appointment has been confirmed for 2027-01-01 09:00:00 at Kisumu County Referral Hospital.', 'booking_confirmation', '11d11cbaedf449b6975d6a108d9b01cf', 'Queued', 0, NULL, '2026-10-12 06:50:26', '2026-10-12 06:50:26'),
(2, '+254712345678', 'Your patient record has been created in the community health system.', 'patient_registration', '86ed82ccc8684f6c855abb13d2284090', 'Queued', 0, NULL, '2026-10-12 14:21:23', '2026-10-12 14:21:23'),
(3, '+254712345678', 'Your patient record has been created in the community health system.', 'patient_registration', '75891c05644148deb152fa95ebfd7d60', 'Queued', 0, NULL, '2026-10-12 15:09:27', '2026-10-12 15:09:27'),
(4, '+254712345678', 'Your appointment has been confirmed for 2026-10-13 23:20:00 at Kangemi Health Centre.', 'booking_confirmation', '345e0ce7a3384480a1d5acc38fd2bf27', 'Queued', 0, NULL, '2026-10-12 20:20:41', '2026-10-12 20:20:41');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`appointment_id`),
  ADD UNIQUE KEY `uq_appointment_facility_datetime` (`facility_id`,`appointment_datetime`),
  ADD KEY `ix_appointments_referral` (`referral_id`),
  ADD KEY `ix_appointments_facility_time` (`facility_id`,`appointment_datetime`),
  ADD KEY `fk_appointments_patient` (`patient_id`);

--
-- Indexes for table `appointment_slots`
--
ALTER TABLE `appointment_slots`
  ADD PRIMARY KEY (`slot_id`),
  ADD UNIQUE KEY `uq_slot_facility_datetime` (`facility_id`,`appointment_datetime`),
  ADD KEY `ix_slots_facility_status` (`facility_id`,`status`),
  ADD KEY `fk_slots_created_by` (`created_by`);

--
-- Indexes for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD PRIMARY KEY (`audit_id`),
  ADD KEY `ix_audit_created_at` (`created_at`),
  ADD KEY `ix_audit_worker` (`worker_id`);

--
-- Indexes for table `community_health_units`
--
ALTER TABLE `community_health_units`
  ADD PRIMARY KEY (`community_unit_id`);

--
-- Indexes for table `facilities`
--
ALTER TABLE `facilities`
  ADD PRIMARY KEY (`facility_id`);

--
-- Indexes for table `healthcare_workers`
--
ALTER TABLE `healthcare_workers`
  ADD PRIMARY KEY (`worker_id`),
  ADD UNIQUE KEY `uq_healthcare_workers_username` (`username`),
  ADD KEY `ix_healthcare_workers_facility` (`facility_id`);

--
-- Indexes for table `patients`
--
ALTER TABLE `patients`
  ADD PRIMARY KEY (`patient_id`),
  ADD UNIQUE KEY `uq_patients_phone_number` (`phone_number`);

--
-- Indexes for table `patient_admissions`
--
ALTER TABLE `patient_admissions`
  ADD PRIMARY KEY (`admission_id`),
  ADD KEY `patient_id` (`patient_id`),
  ADD KEY `facility_id` (`facility_id`);

--
-- Indexes for table `referrals`
--
ALTER TABLE `referrals`
  ADD PRIMARY KEY (`referral_id`),
  ADD KEY `ix_referrals_patient` (`patient_id`),
  ADD KEY `ix_referrals_origin_facility` (`origin_facility_id`),
  ADD KEY `ix_referrals_destination_facility` (`destination_facility_id`),
  ADD KEY `ix_referrals_status` (`status`);

--
-- Indexes for table `referral_appointments`
--
ALTER TABLE `referral_appointments`
  ADD PRIMARY KEY (`booking_id`),
  ADD UNIQUE KEY `uq_referral_booking` (`referral_id`),
  ADD UNIQUE KEY `uq_slot_booking` (`slot_id`),
  ADD KEY `fk_booking_worker` (`booked_by`);

--
-- Indexes for table `sms_messages`
--
ALTER TABLE `sms_messages`
  ADD PRIMARY KEY (`message_id`),
  ADD KEY `ix_sms_status` (`status`),
  ADD KEY `ix_sms_created_at` (`created_at`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `appointment_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `appointment_slots`
--
ALTER TABLE `appointment_slots`
  MODIFY `slot_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `audit_logs`
--
ALTER TABLE `audit_logs`
  MODIFY `audit_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=126;

--
-- AUTO_INCREMENT for table `community_health_units`
--
ALTER TABLE `community_health_units`
  MODIFY `community_unit_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `facilities`
--
ALTER TABLE `facilities`
  MODIFY `facility_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `healthcare_workers`
--
ALTER TABLE `healthcare_workers`
  MODIFY `worker_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `patients`
--
ALTER TABLE `patients`
  MODIFY `patient_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `patient_admissions`
--
ALTER TABLE `patient_admissions`
  MODIFY `admission_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `referrals`
--
ALTER TABLE `referrals`
  MODIFY `referral_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `referral_appointments`
--
ALTER TABLE `referral_appointments`
  MODIFY `booking_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `sms_messages`
--
ALTER TABLE `sms_messages`
  MODIFY `message_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `appointments`
--
ALTER TABLE `appointments`
  ADD CONSTRAINT `fk_appointments_facility` FOREIGN KEY (`facility_id`) REFERENCES `facilities` (`facility_id`),
  ADD CONSTRAINT `fk_appointments_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`),
  ADD CONSTRAINT `fk_appointments_referral` FOREIGN KEY (`referral_id`) REFERENCES `referrals` (`referral_id`);

--
-- Constraints for table `appointment_slots`
--
ALTER TABLE `appointment_slots`
  ADD CONSTRAINT `fk_slots_created_by` FOREIGN KEY (`created_by`) REFERENCES `healthcare_workers` (`worker_id`),
  ADD CONSTRAINT `fk_slots_facility` FOREIGN KEY (`facility_id`) REFERENCES `facilities` (`facility_id`);

--
-- Constraints for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD CONSTRAINT `fk_audit_worker` FOREIGN KEY (`worker_id`) REFERENCES `healthcare_workers` (`worker_id`);

--
-- Constraints for table `healthcare_workers`
--
ALTER TABLE `healthcare_workers`
  ADD CONSTRAINT `fk_healthcare_workers_facility` FOREIGN KEY (`facility_id`) REFERENCES `facilities` (`facility_id`);

--
-- Constraints for table `patient_admissions`
--
ALTER TABLE `patient_admissions`
  ADD CONSTRAINT `patient_admissions_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`),
  ADD CONSTRAINT `patient_admissions_ibfk_2` FOREIGN KEY (`facility_id`) REFERENCES `facilities` (`facility_id`);

--
-- Constraints for table `referrals`
--
ALTER TABLE `referrals`
  ADD CONSTRAINT `fk_referrals_destination_facility` FOREIGN KEY (`destination_facility_id`) REFERENCES `facilities` (`facility_id`),
  ADD CONSTRAINT `fk_referrals_origin_facility` FOREIGN KEY (`origin_facility_id`) REFERENCES `facilities` (`facility_id`),
  ADD CONSTRAINT `fk_referrals_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`);

--
-- Constraints for table `referral_appointments`
--
ALTER TABLE `referral_appointments`
  ADD CONSTRAINT `fk_booking_referral` FOREIGN KEY (`referral_id`) REFERENCES `referrals` (`referral_id`),
  ADD CONSTRAINT `fk_booking_slot` FOREIGN KEY (`slot_id`) REFERENCES `appointment_slots` (`slot_id`),
  ADD CONSTRAINT `fk_booking_worker` FOREIGN KEY (`booked_by`) REFERENCES `healthcare_workers` (`worker_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
