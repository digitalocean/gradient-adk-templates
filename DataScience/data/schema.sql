-- Cymbal Airlines Sample Database Schema
-- Compatible with PostgreSQL and MySQL

-- Airports table
CREATE TABLE IF NOT EXISTS airports (
    airport_id SERIAL PRIMARY KEY,
    iata_code VARCHAR(3) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    timezone VARCHAR(50)
);

-- Aircraft table
CREATE TABLE IF NOT EXISTS aircraft (
    aircraft_id SERIAL PRIMARY KEY,
    registration VARCHAR(20) UNIQUE NOT NULL,
    model VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    capacity_economy INT NOT NULL,
    capacity_business INT NOT NULL,
    capacity_first INT NOT NULL,
    year_manufactured INT
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    loyalty_tier VARCHAR(20) DEFAULT 'Bronze',
    loyalty_points INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flights table
CREATE TABLE IF NOT EXISTS flights (
    flight_id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    departure_airport_iata VARCHAR(3) NOT NULL,
    arrival_airport_iata VARCHAR(3) NOT NULL,
    aircraft_id INT,
    scheduled_departure TIMESTAMP NOT NULL,
    scheduled_arrival TIMESTAMP NOT NULL,
    actual_departure TIMESTAMP,
    actual_arrival TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Scheduled',
    base_price_economy DECIMAL(10, 2),
    base_price_business DECIMAL(10, 2),
    base_price_first DECIMAL(10, 2),
    FOREIGN KEY (departure_airport_iata) REFERENCES airports(iata_code),
    FOREIGN KEY (arrival_airport_iata) REFERENCES airports(iata_code),
    FOREIGN KEY (aircraft_id) REFERENCES aircraft(aircraft_id)
);

-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    flight_id INT NOT NULL,
    customer_id INT NOT NULL,
    seat_class VARCHAR(20) NOT NULL,
    seat_number VARCHAR(5),
    price DECIMAL(10, 2) NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Confirmed',
    checked_in BOOLEAN DEFAULT FALSE,
    baggage_count INT DEFAULT 0,
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Flight history (for analytics - denormalized)
CREATE TABLE IF NOT EXISTS flight_history (
    history_id SERIAL PRIMARY KEY,
    flight_id INT,
    flight_number VARCHAR(10),
    departure_airport_iata VARCHAR(3),
    departure_city VARCHAR(100),
    arrival_airport_iata VARCHAR(3),
    arrival_city VARCHAR(100),
    scheduled_departure TIMESTAMP,
    actual_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    delay_minutes INT,
    passengers_count INT,
    revenue DECIMAL(12, 2),
    flight_date DATE,
    day_of_week VARCHAR(10),
    month VARCHAR(20),
    year INT
);

-- Ticket sales history (for analytics)
CREATE TABLE IF NOT EXISTS ticket_sales_history (
    sale_id SERIAL PRIMARY KEY,
    ticket_id INT,
    flight_id INT,
    customer_id INT,
    sale_date DATE,
    sale_timestamp TIMESTAMP,
    seat_class VARCHAR(20),
    price DECIMAL(10, 2),
    days_before_departure INT,
    customer_loyalty_tier VARCHAR(20),
    promotion_code VARCHAR(20),
    channel VARCHAR(50)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_flights_departure ON flights(departure_airport_iata);
CREATE INDEX IF NOT EXISTS idx_flights_arrival ON flights(arrival_airport_iata);
CREATE INDEX IF NOT EXISTS idx_flights_date ON flights(scheduled_departure);
CREATE INDEX IF NOT EXISTS idx_tickets_flight ON tickets(flight_id);
CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_flight_history_date ON flight_history(flight_date);
CREATE INDEX IF NOT EXISTS idx_sales_history_date ON ticket_sales_history(sale_date);
