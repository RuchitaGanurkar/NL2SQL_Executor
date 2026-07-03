DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    signup_date DATE NOT NULL,
    region VARCHAR(50) NOT NULL
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL  -- 'completed', 'pending', 'cancelled'
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);


INSERT INTO customers (name, email, signup_date, region) VALUES
('Aarav Sharma', 'aarav.s@example.com', '2024-01-15', 'North'),
('Priya Patel', 'priya.p@example.com', '2024-02-20', 'West'),
('Rohan Mehta', 'rohan.m@example.com', '2024-03-10', 'South'),
('Sneha Reddy', 'sneha.r@example.com', '2024-04-05', 'South'),
('Vikram Singh', 'vikram.s@example.com', '2024-05-12', 'North'),
('Ananya Iyer', 'ananya.i@example.com', '2024-06-18', 'West'),
('Karan Joshi', 'karan.j@example.com', '2024-07-22', 'East'),
('Diya Nair', 'diya.n@example.com', '2024-08-30', 'South'),
('Aditya Rao', 'aditya.r@example.com', '2024-09-14', 'North'),
('Ishita Gupta', 'ishita.g@example.com', '2024-10-01', 'East');

INSERT INTO products (name, category, price) VALUES
('Wireless Mouse', 'Electronics', 599.00),
('Mechanical Keyboard', 'Electronics', 2499.00),
('Office Chair', 'Furniture', 5999.00),
('Standing Desk', 'Furniture', 12999.00),
('Notebook Set', 'Stationery', 199.00),
('Pen Pack', 'Stationery', 99.00),
('USB-C Hub', 'Electronics', 1299.00),
('Desk Lamp', 'Furniture', 899.00),
('Backpack', 'Accessories', 1599.00),
('Water Bottle', 'Accessories', 399.00);

INSERT INTO orders (customer_id, order_date, status) VALUES
(1, '2025-01-10', 'completed'),
(2, '2025-01-15', 'completed'),
(3, '2025-02-01', 'completed'),
(1, '2025-02-10', 'cancelled'),
(4, '2025-02-20', 'completed'),
(5, '2025-03-05', 'completed'),
(6, '2025-03-10', 'pending'),
(2, '2025-03-15', 'completed'),
(7, '2025-04-01', 'completed'),
(8, '2025-04-10', 'completed'),
(3, '2025-04-15', 'completed'),
(9, '2025-05-01', 'pending'),
(10, '2025-05-10', 'completed'),
(1, '2025-05-20', 'completed'),
(4, '2025-06-01', 'completed');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 2, 599.00),
(1, 5, 3, 199.00),
(2, 3, 1, 5999.00),
(3, 2, 1, 2499.00),
(3, 7, 1, 1299.00),
(4, 4, 1, 12999.00),
(5, 9, 2, 1599.00),
(6, 1, 1, 599.00),
(6, 6, 5, 99.00),
(7, 3, 2, 5999.00),
(8, 10, 4, 399.00),
(9, 2, 1, 2499.00),
(9, 7, 2, 1299.00),
(10, 8, 1, 899.00),
(11, 4, 1, 12999.00),
(12, 1, 3, 599.00),
(13, 5, 10, 199.00),
(14, 3, 1, 5999.00),
(14, 9, 1, 1599.00),
(15, 2, 2, 2499.00);