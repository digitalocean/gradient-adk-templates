-- Sample Data for Cymbal Airlines Database

-- Insert Airports
INSERT INTO airports (iata_code, name, city, country, latitude, longitude, timezone) VALUES
('JFK', 'John F. Kennedy International Airport', 'New York', 'United States', 40.6413, -73.7781, 'America/New_York'),
('LAX', 'Los Angeles International Airport', 'Los Angeles', 'United States', 33.9425, -118.4081, 'America/Los_Angeles'),
('ORD', 'O''Hare International Airport', 'Chicago', 'United States', 41.9742, -87.9073, 'America/Chicago'),
('DFW', 'Dallas/Fort Worth International Airport', 'Dallas', 'United States', 32.8998, -97.0403, 'America/Chicago'),
('DEN', 'Denver International Airport', 'Denver', 'United States', 39.8561, -104.6737, 'America/Denver'),
('SFO', 'San Francisco International Airport', 'San Francisco', 'United States', 37.6213, -122.3790, 'America/Los_Angeles'),
('SEA', 'Seattle-Tacoma International Airport', 'Seattle', 'United States', 47.4502, -122.3088, 'America/Los_Angeles'),
('MIA', 'Miami International Airport', 'Miami', 'United States', 25.7959, -80.2870, 'America/New_York'),
('BOS', 'Boston Logan International Airport', 'Boston', 'United States', 42.3656, -71.0096, 'America/New_York'),
('ATL', 'Hartsfield-Jackson Atlanta International Airport', 'Atlanta', 'United States', 33.6407, -84.4277, 'America/New_York');

-- Insert Aircraft
INSERT INTO aircraft (registration, model, manufacturer, capacity_economy, capacity_business, capacity_first, year_manufactured) VALUES
('N101CA', 'Boeing 737-800', 'Boeing', 160, 16, 0, 2018),
('N102CA', 'Boeing 737-800', 'Boeing', 160, 16, 0, 2019),
('N201CA', 'Boeing 787-9', 'Boeing', 240, 28, 8, 2020),
('N202CA', 'Boeing 787-9', 'Boeing', 240, 28, 8, 2021),
('N301CA', 'Airbus A320neo', 'Airbus', 150, 12, 0, 2022),
('N302CA', 'Airbus A320neo', 'Airbus', 150, 12, 0, 2022),
('N401CA', 'Airbus A350-900', 'Airbus', 280, 36, 12, 2023),
('N402CA', 'Airbus A350-900', 'Airbus', 280, 36, 12, 2023);

-- Insert Customers
INSERT INTO customers (email, first_name, last_name, phone, loyalty_tier, loyalty_points) VALUES
('john.smith@email.com', 'John', 'Smith', '+1-555-0101', 'Gold', 45000),
('sarah.johnson@email.com', 'Sarah', 'Johnson', '+1-555-0102', 'Platinum', 125000),
('michael.williams@email.com', 'Michael', 'Williams', '+1-555-0103', 'Silver', 15000),
('emily.brown@email.com', 'Emily', 'Brown', '+1-555-0104', 'Bronze', 2500),
('david.jones@email.com', 'David', 'Jones', '+1-555-0105', 'Gold', 55000),
('jennifer.davis@email.com', 'Jennifer', 'Davis', '+1-555-0106', 'Platinum', 180000),
('robert.miller@email.com', 'Robert', 'Miller', '+1-555-0107', 'Silver', 22000),
('lisa.wilson@email.com', 'Lisa', 'Wilson', '+1-555-0108', 'Bronze', 5000),
('james.taylor@email.com', 'James', 'Taylor', '+1-555-0109', 'Gold', 67000),
('amanda.anderson@email.com', 'Amanda', 'Anderson', '+1-555-0110', 'Silver', 18000),
('christopher.thomas@email.com', 'Christopher', 'Thomas', '+1-555-0111', 'Bronze', 3200),
('jessica.jackson@email.com', 'Jessica', 'Jackson', '+1-555-0112', 'Platinum', 210000),
('daniel.white@email.com', 'Daniel', 'White', '+1-555-0113', 'Gold', 48000),
('michelle.harris@email.com', 'Michelle', 'Harris', '+1-555-0114', 'Silver', 28000),
('matthew.martin@email.com', 'Matthew', 'Martin', '+1-555-0115', 'Bronze', 1500);

-- Insert Flights (spanning 2024-2025)
INSERT INTO flights (flight_number, departure_airport_iata, arrival_airport_iata, aircraft_id, scheduled_departure, scheduled_arrival, actual_departure, actual_arrival, status, base_price_economy, base_price_business, base_price_first) VALUES
-- Daily flights JFK-LAX
('CA101', 'JFK', 'LAX', 1, '2025-01-15 08:00:00', '2025-01-15 11:30:00', '2025-01-15 08:15:00', '2025-01-15 11:45:00', 'Completed', 299.00, 899.00, NULL),
('CA102', 'LAX', 'JFK', 2, '2025-01-15 14:00:00', '2025-01-15 22:30:00', '2025-01-15 14:00:00', '2025-01-15 22:25:00', 'Completed', 299.00, 899.00, NULL),
('CA101', 'JFK', 'LAX', 1, '2025-01-16 08:00:00', '2025-01-16 11:30:00', '2025-01-16 08:05:00', '2025-01-16 11:35:00', 'Completed', 299.00, 899.00, NULL),
('CA102', 'LAX', 'JFK', 2, '2025-01-16 14:00:00', '2025-01-16 22:30:00', '2025-01-16 14:30:00', '2025-01-16 23:00:00', 'Completed', 299.00, 899.00, NULL),
('CA101', 'JFK', 'LAX', 1, '2025-01-17 08:00:00', '2025-01-17 11:30:00', NULL, NULL, 'Scheduled', 349.00, 999.00, NULL),
-- Flights ORD-SFO
('CA201', 'ORD', 'SFO', 3, '2025-01-15 09:00:00', '2025-01-15 11:30:00', '2025-01-15 09:10:00', '2025-01-15 11:40:00', 'Completed', 249.00, 749.00, 1499.00),
('CA202', 'SFO', 'ORD', 4, '2025-01-15 13:00:00', '2025-01-15 19:00:00', '2025-01-15 13:00:00', '2025-01-15 18:55:00', 'Completed', 249.00, 749.00, 1499.00),
('CA201', 'ORD', 'SFO', 3, '2025-01-16 09:00:00', '2025-01-16 11:30:00', '2025-01-16 09:00:00', '2025-01-16 11:28:00', 'Completed', 249.00, 749.00, 1499.00),
-- Flights DFW-SEA
('CA301', 'DFW', 'SEA', 5, '2025-01-15 07:00:00', '2025-01-15 09:30:00', '2025-01-15 07:00:00', '2025-01-15 09:25:00', 'Completed', 199.00, 599.00, NULL),
('CA302', 'SEA', 'DFW', 6, '2025-01-15 11:00:00', '2025-01-15 16:30:00', '2025-01-15 11:45:00', '2025-01-15 17:15:00', 'Completed', 199.00, 599.00, NULL),
-- Flights MIA-BOS
('CA401', 'MIA', 'BOS', 7, '2025-01-15 06:00:00', '2025-01-15 09:30:00', '2025-01-15 06:00:00', '2025-01-15 09:28:00', 'Completed', 279.00, 839.00, 1679.00),
('CA402', 'BOS', 'MIA', 8, '2025-01-15 12:00:00', '2025-01-15 15:30:00', '2025-01-15 12:20:00', '2025-01-15 15:50:00', 'Completed', 279.00, 839.00, 1679.00),
-- Future flights
('CA501', 'ATL', 'DEN', 1, '2025-01-20 10:00:00', '2025-01-20 12:00:00', NULL, NULL, 'Scheduled', 229.00, 689.00, NULL),
('CA502', 'DEN', 'ATL', 2, '2025-01-20 15:00:00', '2025-01-20 20:00:00', NULL, NULL, 'Scheduled', 229.00, 689.00, NULL);

-- Insert Tickets
INSERT INTO tickets (ticket_number, flight_id, customer_id, seat_class, seat_number, price, booking_date, status, checked_in, baggage_count) VALUES
('TKT-001-2025', 1, 1, 'Economy', '24A', 299.00, '2025-01-01 10:00:00', 'Completed', TRUE, 1),
('TKT-002-2025', 1, 2, 'Business', '2A', 899.00, '2025-01-02 14:30:00', 'Completed', TRUE, 2),
('TKT-003-2025', 1, 3, 'Economy', '25B', 299.00, '2025-01-05 09:15:00', 'Completed', TRUE, 1),
('TKT-004-2025', 2, 4, 'Economy', '18C', 299.00, '2025-01-03 11:00:00', 'Completed', TRUE, 0),
('TKT-005-2025', 2, 5, 'Business', '3B', 899.00, '2025-01-04 16:45:00', 'Completed', TRUE, 2),
('TKT-006-2025', 3, 6, 'Economy', '22A', 299.00, '2025-01-10 08:00:00', 'Completed', TRUE, 1),
('TKT-007-2025', 3, 7, 'Economy', '22B', 299.00, '2025-01-10 08:00:00', 'Completed', TRUE, 1),
('TKT-008-2025', 6, 8, 'First', '1A', 1499.00, '2025-01-05 12:00:00', 'Completed', TRUE, 3),
('TKT-009-2025', 6, 9, 'Business', '5C', 749.00, '2025-01-08 14:20:00', 'Completed', TRUE, 2),
('TKT-010-2025', 7, 10, 'Economy', '30A', 249.00, '2025-01-12 10:30:00', 'Completed', TRUE, 1),
('TKT-011-2025', 9, 11, 'Economy', '15D', 199.00, '2025-01-10 09:00:00', 'Completed', TRUE, 0),
('TKT-012-2025', 11, 12, 'First', '1B', 1679.00, '2025-01-01 15:00:00', 'Completed', TRUE, 4),
('TKT-013-2025', 11, 13, 'Business', '4A', 839.00, '2025-01-07 11:30:00', 'Completed', TRUE, 2),
('TKT-014-2025', 13, 14, 'Economy', '28C', 229.00, '2025-01-15 16:00:00', 'Confirmed', FALSE, 1),
('TKT-015-2025', 14, 15, 'Economy', '20A', 229.00, '2025-01-16 09:45:00', 'Confirmed', FALSE, 0);

-- Insert Flight History (historical analytics data)
INSERT INTO flight_history (flight_id, flight_number, departure_airport_iata, departure_city, arrival_airport_iata, arrival_city, scheduled_departure, actual_departure, scheduled_arrival, actual_arrival, delay_minutes, passengers_count, revenue, flight_date, day_of_week, month, year) VALUES
-- 2024 Historical Data
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-01-15 08:00:00', '2024-01-15 08:10:00', '2024-01-15 11:30:00', '2024-01-15 11:40:00', 10, 145, 52350.00, '2024-01-15', 'Monday', 'January', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-02-15 08:00:00', '2024-02-15 08:00:00', '2024-02-15 11:30:00', '2024-02-15 11:28:00', -2, 162, 58320.00, '2024-02-15', 'Thursday', 'February', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-03-15 08:00:00', '2024-03-15 08:45:00', '2024-03-15 11:30:00', '2024-03-15 12:15:00', 45, 158, 56880.00, '2024-03-15', 'Friday', 'March', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-04-15 08:00:00', '2024-04-15 08:05:00', '2024-04-15 11:30:00', '2024-04-15 11:35:00', 5, 170, 61200.00, '2024-04-15', 'Monday', 'April', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-05-15 08:00:00', '2024-05-15 08:00:00', '2024-05-15 11:30:00', '2024-05-15 11:25:00', -5, 175, 63000.00, '2024-05-15', 'Wednesday', 'May', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-06-15 08:00:00', '2024-06-15 09:30:00', '2024-06-15 11:30:00', '2024-06-15 13:00:00', 90, 176, 66880.00, '2024-06-15', 'Saturday', 'June', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-07-15 08:00:00', '2024-07-15 08:20:00', '2024-07-15 11:30:00', '2024-07-15 11:50:00', 20, 176, 70400.00, '2024-07-15', 'Monday', 'July', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-08-15 08:00:00', '2024-08-15 08:00:00', '2024-08-15 11:30:00', '2024-08-15 11:30:00', 0, 172, 68800.00, '2024-08-15', 'Thursday', 'August', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-09-15 08:00:00', '2024-09-15 08:15:00', '2024-09-15 11:30:00', '2024-09-15 11:45:00', 15, 155, 55800.00, '2024-09-15', 'Sunday', 'September', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-10-15 08:00:00', '2024-10-15 08:00:00', '2024-10-15 11:30:00', '2024-10-15 11:28:00', -2, 148, 53280.00, '2024-10-15', 'Tuesday', 'October', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-11-15 08:00:00', '2024-11-15 08:30:00', '2024-11-15 11:30:00', '2024-11-15 12:00:00', 30, 165, 59400.00, '2024-11-15', 'Friday', 'November', 2024),
(NULL, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2024-12-15 08:00:00', '2024-12-15 08:00:00', '2024-12-15 11:30:00', '2024-12-15 11:32:00', 2, 176, 70400.00, '2024-12-15', 'Sunday', 'December', 2024),
-- ORD-SFO route
(NULL, 'CA201', 'ORD', 'Chicago', 'SFO', 'San Francisco', '2024-01-20 09:00:00', '2024-01-20 09:00:00', '2024-01-20 11:30:00', '2024-01-20 11:28:00', -2, 220, 66000.00, '2024-01-20', 'Saturday', 'January', 2024),
(NULL, 'CA201', 'ORD', 'Chicago', 'SFO', 'San Francisco', '2024-04-20 09:00:00', '2024-04-20 09:15:00', '2024-04-20 11:30:00', '2024-04-20 11:45:00', 15, 245, 85750.00, '2024-04-20', 'Saturday', 'April', 2024),
(NULL, 'CA201', 'ORD', 'Chicago', 'SFO', 'San Francisco', '2024-07-20 09:00:00', '2024-07-20 10:00:00', '2024-07-20 11:30:00', '2024-07-20 12:30:00', 60, 268, 107200.00, '2024-07-20', 'Saturday', 'July', 2024),
(NULL, 'CA201', 'ORD', 'Chicago', 'SFO', 'San Francisco', '2024-10-20 09:00:00', '2024-10-20 09:05:00', '2024-10-20 11:30:00', '2024-10-20 11:35:00', 5, 235, 70500.00, '2024-10-20', 'Sunday', 'October', 2024),
-- 2025 Data
(1, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2025-01-15 08:00:00', '2025-01-15 08:15:00', '2025-01-15 11:30:00', '2025-01-15 11:45:00', 15, 168, 60480.00, '2025-01-15', 'Wednesday', 'January', 2025),
(3, 'CA101', 'JFK', 'New York', 'LAX', 'Los Angeles', '2025-01-16 08:00:00', '2025-01-16 08:05:00', '2025-01-16 11:30:00', '2025-01-16 11:35:00', 5, 172, 61920.00, '2025-01-16', 'Thursday', 'January', 2025);

-- Insert Ticket Sales History
INSERT INTO ticket_sales_history (ticket_id, flight_id, customer_id, sale_date, sale_timestamp, seat_class, price, days_before_departure, customer_loyalty_tier, promotion_code, channel) VALUES
(1, 1, 1, '2025-01-01', '2025-01-01 10:00:00', 'Economy', 299.00, 14, 'Gold', NULL, 'Website'),
(2, 1, 2, '2025-01-02', '2025-01-02 14:30:00', 'Business', 899.00, 13, 'Platinum', 'PLAT10', 'Mobile App'),
(3, 1, 3, '2025-01-05', '2025-01-05 09:15:00', 'Economy', 299.00, 10, 'Silver', NULL, 'Website'),
(4, 2, 4, '2025-01-03', '2025-01-03 11:00:00', 'Economy', 299.00, 12, 'Bronze', NULL, 'Call Center'),
(5, 2, 5, '2025-01-04', '2025-01-04 16:45:00', 'Business', 899.00, 11, 'Gold', NULL, 'Website'),
(6, 3, 6, '2025-01-10', '2025-01-10 08:00:00', 'Economy', 299.00, 6, 'Platinum', 'LASTMIN', 'Mobile App'),
(7, 3, 7, '2025-01-10', '2025-01-10 08:00:00', 'Economy', 299.00, 6, 'Silver', NULL, 'Mobile App'),
(8, 6, 8, '2025-01-05', '2025-01-05 12:00:00', 'First', 1499.00, 10, 'Bronze', NULL, 'Travel Agent'),
(9, 6, 9, '2025-01-08', '2025-01-08 14:20:00', 'Business', 749.00, 7, 'Gold', 'GOLD15', 'Website'),
(10, 7, 10, '2025-01-12', '2025-01-12 10:30:00', 'Economy', 249.00, 3, 'Silver', 'LASTMIN', 'Mobile App'),
(11, 9, 11, '2025-01-10', '2025-01-10 09:00:00', 'Economy', 199.00, 5, 'Bronze', NULL, 'Website'),
(12, 11, 12, '2025-01-01', '2025-01-01 15:00:00', 'First', 1679.00, 14, 'Platinum', 'PLAT10', 'Mobile App'),
(13, 11, 13, '2025-01-07', '2025-01-07 11:30:00', 'Business', 839.00, 8, 'Gold', NULL, 'Website'),
(14, 13, 14, '2025-01-15', '2025-01-15 16:00:00', 'Economy', 229.00, 5, 'Silver', NULL, 'Website'),
(15, 14, 15, '2025-01-16', '2025-01-16 09:45:00', 'Economy', 229.00, 4, 'Bronze', 'SAVE20', 'Call Center');
