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

# Function to calculate costs
def calculate_costs(conn, items):
    total_cost = 0
    breakdown = []

    for item in items:
        product_keyword = item['product']
        quantity = item['quantity']

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 0

        if not product_keyword or quantity <= 0:
            continue

        try:
            cursor = conn.cursor()

            # Step 1: Find products that match the keyword
            cursor.execute(""" 
                SELECT Product, Price, Seller_name, Location, URL
                FROM fb_jiji_merged_tb
                WHERE LOWER(Product) LIKE LOWER(?);
            """, (f"%{product_keyword}%",))
            matched_products = cursor.fetchall()

            # Step 2: If no products match, log and continue
            if not matched_products:
                breakdown.append({
                    "Product (Matched)": "Not Found",
                    "Quantity": quantity,
                    "Supplier": "N/A",
                    "Total Cost": "N/A",
                    "Unit Price": "N/A",
                    "Location": "N/A",
                    "URL": "N/A",
                })
                continue

            # Step 3: Calculate the average price
            average_price = sum(price for _, price, *_ in matched_products) / len(matched_products)

            # Step 4: Find the product with the price closest to the average price
            best_match = min(matched_products, key=lambda x: abs(x[1] - average_price))

            # Step 5: Calculate total cost for the best match
            cost = best_match[1] * quantity
            total_cost += cost
            breakdown.append({
                "Product (Matched)": best_match[0],
                "Quantity": quantity,
                "Supplier": best_match[2],  # Get supplier from matched product
                "Total Cost": cost,
                "Unit Price": best_match[1],
                "Location": best_match[3],  # Get location from matched product
                "URL": best_match[4],  # Get URL from matched product
            })
        except Exception as e:
            logging.error(f"Error in cost calculation: {e}")

    return {"total_cost": total_cost, "breakdown": breakdown}

# API route for cost estimation
@app.route('/estimate_costs', methods=['POST'])
def api_estimate_costs():
    conn = connect_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        data = request.json
        items = data.get('items', [])
        results = calculate_costs(conn, items)
        return jsonify(results)
    except Exception as e:
        logging.error(f"Error in cost estimation: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Route to recommend suppliers
@app.route('/recommend_suppliers', methods=['POST'])
def recommend_suppliers():
    try:
        data = request.json
        product_keyword = data.get('product_keyword', '')
        preferred_location = data.get('preferred_location', '')
        limit = data.get('limit', 10)  # Default limit to 10 if not provided

        conn = connect_db()
        cursor = conn.cursor()

        query = """
        SELECT 
            Product, 
            Price, 
            Seller_name,
            Location,
            URL 
        FROM fb_jiji_merged_tb 
        WHERE Product LIKE ?
        """
        params = [f"%{product_keyword}%"]

        if preferred_location:
            query += " AND Location LIKE ?"
            params.append(f"%{preferred_location}%")

        query += " LIMIT ?"
        params.append(limit)  # Include the limit in the query parameters

        cursor.execute(query, params)
        data = cursor.fetchall()

        results = [
            {
                "Supplier": row[2],
                "Location": row[3],
                "Price": row[1],
                "Matched Product": row[0],
                "URL": row[4],
            }
            for row in data
        ]

        conn.close()
        return jsonify({"results": results})

    except Exception as e:
        logging.error(f"Error in recommending suppliers: {e}")
        return jsonify({"error": "An error occurred while fetching recommendations."}), 500

# Render the home page
@app.route('/')
def home():
    return render_template('index.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)