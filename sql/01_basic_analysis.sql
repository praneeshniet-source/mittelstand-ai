
-- Display all invoices
SELECT *
FROM invoices;

-- Find only unpaid invoices
SELECT invoice_id, supplier, amount_eur
FROM invoices
WHERE status = 'Unpaid';

-- Calculate total invoice value
SELECT SUM(amount_eur) AS total_invoice_value
FROM invoices;
