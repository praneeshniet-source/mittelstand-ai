
import pandas as pd
import sqlite3

# Load the invoice dataset
invoices = pd.read_csv("data/raw/invoices.csv")

# Create or open our SQLite database
connection = sqlite3.connect("mittelstand.db")

# Store the CSV records as a database table
invoices.to_sql(
    "invoices",
    connection,
    if_exists="replace",
    index=False
)

print("Database created successfully!")
print(f"Records loaded: {len(invoices)}")

# Close the database connection
connection.close()
