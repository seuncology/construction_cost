from flask import Flask, request, jsonify, render_template
import sqlite3
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection function
def connect_db(db_name="fb_jiji_merged.db"):
    try:
        conn = sqlite3.connect(db_name)
        conn.execute("PRAGMA foreign_keys = 1")
        ensure_reliability_score_column(conn)  # Ensure Reliability_Score column exists
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection failed: {e}")
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
def compute_reliability_score(price, product_matches):
    """
    Compute the reliability score based on price and the number of product matches.
    - Lower price results in higher reliability.
    - More product matches result in higher reliability.
    """
    score = (1 / (price + 1)) * 10  # Higher price should lower reliability score
    score += product_matches * 0.5  # More product matches improve reliability
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
                SELECT Product, MIN(Price) AS Best_Price, seller_name, Location
                FROM fb_jiji_merged_tb
                WHERE LOWER(Product) LIKE LOWER(?)
                GROUP BY Product
                ORDER BY Best_Price ASC
                LIMIT 1;
            """, (f"%{product_keyword}%",))
            data = cursor.fetchone()

            if data:
                # Compute the reliability score based on price and matches
                reliability_score = compute_reliability_score(data[1], 5)  # Example: 5 product matches

                cost = data[1] * quantity
                total_cost += cost
                breakdown.append({
                    "Product (Matched)": data[0],
                    "Keyword": product_keyword,
                    "Quantity": quantity,
                    "Unit Price": data[1],
                    "Total Cost": cost,
                    "Supplier": data[2],
                    "Location": data[3],
                    "Reliability Score": reliability_score
                })

                # Store results in the database with computed reliability score
                cursor.execute("""
                    INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, Reliability_Score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (data[0], product_keyword, quantity, data[1], cost, data[2], data[3], reliability_score))
            else:
                breakdown.append({
                    "Product (Matched)": "Not Found",
                    "Keyword": product_keyword,
                    "Quantity": quantity,
                    "Unit Price": "N/A",
                    "Total Cost": "N/A",
                    "Supplier": "N/A",
                    "Location": "N/A",
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

# Function to recommend suppliers
def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
    cursor = conn.cursor()
    results = []

    try:
        query = """
            SELECT seller_name, Location, Price, Product
            FROM fb_jiji_merged_tb
            WHERE LOWER(Product) LIKE LOWER(?)
        """
        params = [f"%{product_keyword}%"]

        if preferred_location:
            query += " AND LOWER(Location) LIKE LOWER(?)"
            params.append(f"%{preferred_location}%")

        query += " ORDER BY Price ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor.execute(query, params)
        data = cursor.fetchall()

        for row in data:
            # Compute the reliability score based on price and matches
            reliability_score = compute_reliability_score(row[2], 5)  # Example: 5 product matches

            results.append({
                "Supplier": row[0],
                "Location": row[1],
                "Price": row[2],
                "Matched Product": row[3],
                "Reliability Score": reliability_score
            })
    except Exception as e:
        logging.error(f"Error in recommending suppliers: {e}")

    return results

# API route for supplier recommendations
@app.route('/recommend_suppliers', methods=['POST'])
def api_recommend_suppliers():
    conn = connect_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        data = request.form
        product_keyword = data.get("product_keyword")
        preferred_location = data.get("preferred_location")
        limit = int(data.get("limit", 10))
        offset = int(data.get("offset", 0))

        if not product_keyword:
            return jsonify({"error": "Product keyword is required"}), 400

        results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
        return jsonify({"results": results})
    except Exception as e:
        logging.error(f"Error in supplier recommendation: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Render the home page
@app.route('/')
def home():
    return render_template('index.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
