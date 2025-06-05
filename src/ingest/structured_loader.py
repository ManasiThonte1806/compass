# src/ingest/structured_loader.py

import duckdb
import pandas as pd
import os # Import os module to handle file paths

def main():
    # Define the base directory for data
    # This makes the script runnable from the project root or src/ingest
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    data_path = os.path.join(project_root, 'data', 'structured')
    db_path = os.path.join(data_path, 'allyin_compass.db') # Path for the persistent DuckDB file

    print(f"Attempting to load CSVs from: {data_path}")
    print(f"DuckDB database will be saved/loaded from: {db_path}")

    # Initialize DuckDB connection (persistent database)
    con = None # Initialize con to None
    try:
        con = duckdb.connect(database=db_path, read_only=False)
        print("Connected to DuckDB successfully.")
    except Exception as e:
        print(f"Error connecting to DuckDB at {db_path}: {e}")
        return # Exit the function if connection fails

    # --- Load customers.csv ---
    try:
        customers_csv_path = os.path.join(data_path, 'customers.csv')
        customers_df = pd.read_csv(customers_csv_path)
        # Use CREATE OR REPLACE TABLE to ensure it's updated if script is run multiple times
        con.execute("CREATE OR REPLACE TABLE customers AS SELECT * FROM customers_df")
        print(f"Successfully loaded '{os.path.basename(customers_csv_path)}' into DuckDB as 'customers' table.")
    except FileNotFoundError:
        print(f"Error: '{os.path.basename(customers_csv_path)}' not found at {customers_csv_path}. Please ensure it exists.")
    except pd.errors.EmptyDataError:
        print(f"Warning: '{os.path.basename(customers_csv_path)}' is empty. No data loaded for 'customers'.")
    except Exception as e:
        print(f"An unexpected error occurred while loading '{os.path.basename(customers_csv_path)}': {e}")

    # --- Load orders.csv ---
    try:
        orders_csv_path = os.path.join(data_path, 'orders.csv')
        orders_df = pd.read_csv(orders_csv_path)
        con.execute("CREATE OR REPLACE TABLE orders AS SELECT * FROM orders_df")
        print(f"Successfully loaded '{os.path.basename(orders_csv_path)}' into DuckDB as 'orders' table.")
    except FileNotFoundError:
        print(f"Error: '{os.path.basename(orders_csv_path)}' not found at {orders_csv_path}. Please ensure it exists.")
    except pd.errors.EmptyDataError:
        print(f"Warning: '{os.path.basename(orders_csv_path)}' is empty. No data loaded for 'orders'.")
    except Exception as e:
        print(f"An unexpected error occurred while loading '{os.path.basename(orders_csv_path)}': {e}")

    # --- Load products.csv ---
    try:
        products_csv_path = os.path.join(data_path, 'products.csv')
        products_df = pd.read_csv(products_csv_path)
        con.execute("CREATE OR REPLACE TABLE products AS SELECT * FROM products_df")
        print(f"Successfully loaded '{os.path.basename(products_csv_path)}' into DuckDB as 'products' table.")
    except FileNotFoundError:
        print(f"Error: '{os.path.basename(products_csv_path)}' not found at {products_csv_path}. Please ensure it exists.")
    except pd.errors.EmptyDataError:
        print(f"Warning: '{os.path.basename(products_csv_path)}' is empty. No data loaded for 'products'.")
    except Exception as e:
        print(f"An unexpected error occurred while loading '{os.path.basename(products_csv_path)}': {e}")

    print("\nStructured data loading attempts complete.")

    # --- Explore DuckDB Tables ---
    print("\n--- Exploring DuckDB Tables ---")

    # Explore the 'customers' table
    print("\nTop 10 rows from 'customers' table:")
    try:
        customers_sample = con.execute("SELECT * FROM customers LIMIT 10").df()
        if not customers_sample.empty:
            print(customers_sample)
        else:
            print("No data in 'customers' table.")
    except Exception as e:
        print(f"Error exploring 'customers' table: {e}")

    # Explore the 'orders' table
    print("\nTop 10 rows from 'orders' table:")
    try:
        orders_sample = con.execute("SELECT * FROM orders LIMIT 10").df()
        if not orders_sample.empty:
            print(orders_sample)
        else:
            print("No data in 'orders' table.")
    except Exception as e:
        print(f"Error exploring 'orders' table: {e}")

    # Explore the 'products' table
    print("\nTop 10 rows from 'products' table:")
    try:
        products_sample = con.execute("SELECT * FROM products LIMIT 10").df()
        if not products_sample.empty:
            print(products_sample)
        else:
            print("No data in 'products' table.")
    except Exception as e:
        print(f"Error exploring 'products' table: {e}")

    # Close the DuckDB connection when done
    if con: # Ensure connection exists before trying to close
        con.close()
        print("\nDuckDB connection closed.")

if __name__ == "__main__":
    main()
