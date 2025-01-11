from flask import Flask, request, jsonify, render_template
import sqlite3
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE = "fb_jiji_merged.db"

# Database connection function
def connect_db():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.execute("PRAGMA foreign_keys = 1")
        return conn
    except sqlite3.Error as e:
        logging.error("Database connection failed: " + str(e))
        return None

# Ensure Reliability_Score column exists
def ensure_reliability_score_column(conn):
    try:
        cursor = conn.cursor()
        cursor.execute(""" 
            ALTER TABLE fb_jiji_merged_tb 
            ADD COLUMN Reliability_Score REAL DEFAULT 0.0;
        """)
        conn.commit()
    except sqlite3.Error as e:
        if "duplicate column name" in str(e).lower():
            pass  # Column already exists
        else:
            logging.error(f"Error ensuring Reliability_Score column: {e}")

# Function to calculate Reliability Score
def compute_reliability_score(price, listings_count):
    if listings_count <= 0:
        return 0  # Handle division by zero
    score = (1 / (price + 1)) * 10  # Higher price should lower reliability score
    score += (1 / listings_count) * 5  # More listings improve reliability
    return round(score, 2)

# Function to calculate costs
def calculate_costs(conn, product_list):
    cursor = conn.cursor()
    total_cost = 0
    breakdown = []

    # Ensure the table for storing calculated costs exists
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS calculated_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Product_Matched TEXT NOT NULL,
            Keyword TEXT NOT NULL,
            Quantity INTEGER NOT NULL,
            Unit_Price REAL NOT NULL,
            Total_Cost REAL NOT NULL,
            Supplier TEXT,
            Location TEXT,
            URL TEXT,
            Reliability_Score REAL,
            UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
        );
    """)

    for item in product_list:
        product_keyword = item.get('product')
        quantity = item.get('quantity', 0)

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 0

        if not product_keyword or quantity <= 0:
            continue

        try:
            cursor.execute(""" 
                SELECT Product, MIN(Price) AS Best_Price, Location, URL, Seller_name, Average_Price, Listings_Count, Reliability_Score
                FROM fb_jiji_merged_tb
                WHERE LOWER(Product) LIKE LOWER(?)
                GROUP BY Product
                ORDER BY Best_Price ASC
                LIMIT 1;
            """, (f"%{product_keyword}%",))
            data = cursor.fetchone()

            if data:
                reliability_score = compute_reliability_score(data[1], data[6])  # Example: listings_count
                cost = data[1] * quantity
                total_cost += cost
                breakdown.append({
                    "Product (Matched)": data[0],
                    "Keyword": product_keyword,
                    "Quantity": quantity,
                    "Unit Price": data[1],
                    "Total Cost": cost,
                    "Supplier": data[4],
                    "Location": data[2],
                    "URL": data[3],
                    "Reliability Score": reliability_score
                })

                cursor.execute(""" 
                    INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, URL, Reliability_Score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (data[0], product_keyword, quantity, data[1], cost, data[4], data[2], data[3], reliability_score))
            else:
                breakdown.append({
                    "Product (Matched)": "Not Found",
                    "Keyword": product_keyword,
                    "Quantity": quantity,
                    "Unit Price": "N/A",
                    "Total Cost": "N/A",
                    "Supplier": "N/A",
                    "Location": "N/A",
                    "URL": "N/A",
                    "Reliability Score": "N/A"
                })
        except Exception as e:
            logging.error(f"Error in cost calculation: {e}")

    conn.commit()
    return {"total_cost": total_cost, "breakdown": breakdown}

# API route for cost estimation
@app.route('/calculate_costs', methods=['POST'])
def api_calculate_costs():
    conn = connect_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        product_list = []
        for key in request.form:
            if key.startswith('product_') and request.form[key]:
                index = key.split('_')[1]
                product = request.form[key]
                quantity = request.form.get(f'quantity_{index}', 0)
                product_list.append({"product": product, "quantity": quantity})

        results = calculate_costs(conn, product_list)
        return jsonify(results)
    except Exception as e:
        logging.error(f"Error in cost estimation: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.before_first_request
def create_tables():
    conn = connect_db()
    if conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute(""" 
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Product TEXT NOT NULL,
                    Price REAL NOT NULL,
                    Location TEXT NOT NULL,
                    URL TEXT,
                    Seller_name TEXT NOT NULL,
                    Average_Price REAL,
                    Listings_Count INTEGER,
                    Reliability_Score REAL
                );
            """)
            ensure_reliability_score_column(conn)
        conn.close()

# Route to Recommend Suppliers
@app.route('/recommend_suppliers', methods=['POST'])
def recommend_suppliers():
    try:
        data = request.form
        product_keyword = data.get('product_keyword', '')
        preferred_location = data.get('preferred_location', '')
        limit = int(data.get('limit', 10))  # Default limit is 10 if not specified

        conn = connect_db()
        cursor = conn.cursor()

        query = """
        SELECT 
            Product, 
            Price, 
            Location, 
            URL, 
            Seller_name, 
            Average_Price, 
            Listings_Count, 
            Reliability_Score 
        FROM suppliers 
        WHERE Product LIKE ?
        """
        params = [f"%{product_keyword}%"]

        if preferred_location:
            query += " AND Location LIKE ?"
            params.append(f"%{preferred_location}%")

        query += " LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        data = cursor.fetchall()

        results = [
            {
                "Supplier": row[4],
                "Location": row[2],
                "Price": row[1],
                "Matched Product": row[0],
                "Reliability Score": row[7],
                "URL": row[3],
            }
            for row in data
        ]

        conn.close()
        return jsonify({"results": results})

    except Exception as e:
        logging.error(f"Error in recommending suppliers: {e}")
        return jsonify({"error": "An error occurred while fetching recommendations."}), 500

# Route to Add Supplier
@app.route('/add_supplier', methods=['POST'])
def add_supplier():
    try:
        data = request.form
        product = data.get('product')
        price = float(data.get('price', 0))  # Ensure price is float
        location = data.get('location')
        url = data.get('url')
        seller_name = data.get('seller_name')
        average_price = float(data.get('average_price', 0))  # Ensure average price is float
        listings_count = int(data.get('listings_count', 0))  # Ensure listings count is integer
        reliability_score = float(data.get('reliability_score', 0))  # Ensure reliability score is float

        conn = connect_db()
        cursor = conn.cursor()

        query = """ 
        INSERT INTO suppliers (Product, Price, Location, URL, Seller_name, Average_Price, Listings_Count, Reliability_Score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (product, price, location, url, seller_name, average_price, listings_count, reliability_score))
        conn.commit()
        conn.close()

        return jsonify({"message": "Supplier added successfully!"})

    except Exception as e:
        logging.error(f"Error in adding supplier: {e}")
        return jsonify({"error": "An error occurred while adding the supplier."}), 500

# Route to Update Supplier
@app.route('/update_supplier/<int:id>', methods=['POST'])
def update_supplier(id):
    try:
        data = request.form
        product = data.get('product')
        price = float(data.get('price', 0))  # Ensure price is float
        location = data.get('location')
        url = data.get('url')
        seller_name = data.get('seller_name')
        average_price = float(data.get('average_price', 0))  # Ensure average price is float
        listings_count = int(data.get('listings_count', 0))  # Ensure listings count is integer
        reliability_score = float(data.get('reliability_score', 0))  # Ensure reliability score is float

        conn = connect_db()
        cursor = conn.cursor()

        query = """ 
        UPDATE suppliers 
        SET Product = ?, Price = ?, Location = ?, URL = ?, Seller_name = ?, Average_Price = ?, Listings_Count = ?, Reliability_Score = ?
        WHERE id = ?
        """
        cursor.execute(query, (product, price, location, url, seller_name, average_price, listings_count, reliability_score, id))
        conn.commit()
        conn.close()

        return jsonify({"message": "Supplier updated successfully!"})

    except Exception as e:
        logging.error(f"Error in updating supplier: {e}")
        return jsonify({"error": "An error occurred while updating the supplier."}), 500

# Route to Delete Supplier
@app.route('/delete_supplier/<int:id>', methods=['DELETE'])
def delete_supplier(id):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        query = "DELETE FROM suppliers WHERE id = ?"
        cursor.execute(query, (id,))
        conn.commit()
        conn.close()

        return jsonify({"message": "Supplier deleted successfully!"})

    except Exception as e:
        logging.error(f"Error in deleting supplier: {e}")
        return jsonify({"error": "An error occurred while deleting the supplier."}), 500

# Render the home page
@app.route('/')
def home():
    return render_template('index.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)