# from flask import Flask, request, jsonify, render_template
# import sqlite3
# import logging

# # Initialize Flask app
# app = Flask(__name__)

# # Configure logging
# logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# DATABASE = "fb_jiji_merged.db"

# # Database connection function
# def connect_db():
#     try:
#         conn = sqlite3.connect(DATABASE)
#         conn.execute("PRAGMA foreign_keys = 1")
#         return conn
#     except sqlite3.Error as e:
#         logging.error("Database connection failed: " + str(e))
#         return None

# # Function to calculate costs
# def calculate_costs(conn, product_list):
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

#     # Ensure the table for storing calculated costs exists
#     cursor.execute(""" 
#         CREATE TABLE IF NOT EXISTS calculated_costs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             Product_Matched TEXT NOT NULL,
#             Keyword TEXT NOT NULL,
#             Quantity INTEGER NOT NULL,
#             Unit_Price REAL NOT NULL,
#             Total_Cost REAL NOT NULL,
#             Supplier TEXT,
#             Location TEXT,
#             URL TEXT,
#             UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
#         );
#     """)

#     for item in product_list:
#         product_keyword = item.get('product')
#         quantity = item.get('quantity', 0)

#         try:
#             quantity = int(quantity)
#         except ValueError:
#             quantity = 0

#         if not product_keyword or quantity <= 0:
#             continue

#         try:
#             cursor.execute(""" 
#                 SELECT Product, MIN(Price) AS Best_Price, Location, URL, Seller_name
#                 FROM fb_jiji_merged_tb
#                 WHERE LOWER(Product) LIKE LOWER(?)
#                 GROUP BY Product
#                 ORDER BY Best_Price ASC
#                 LIMIT 1;
#             """, (f"%{product_keyword}%",))
#             data = cursor.fetchone()

#             if data:
#                 cost = data[1] * quantity
#                 total_cost += cost
#                 breakdown.append({
#                     "Product (Matched)": data[0],
#                     "Keyword": product_keyword,
#                     "Quantity": quantity,
#                     "Unit Price": data[1],
#                     "Total Cost": cost,
#                     "Supplier": data[4],
#                     "Location": data[2],
#                     "URL": data[3],
#                 })

#                 cursor.execute(""" 
#                     INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, URL)
#                     VALUES (?, ?, ?, ?, ?, ?, ?, ?);
#                 """, (data[0], product_keyword, quantity, data[1], cost, data[4], data[2], data[3]))
#             else:
#                 breakdown.append({
#                     "Product (Matched)": "Not Found",
#                     "Keyword": product_keyword,
#                     "Quantity": quantity,
#                     "Unit Price": "N/A",
#                     "Total Cost": "N/A",
#                     "Supplier": "N/A",
#                     "Location": "N/A",
#                     "URL": "N/A",
#                 })
#         except Exception as e:
#             logging.error(f"Error in cost calculation: {e}")

#     conn.commit()
#     return {"total_cost": total_cost, "breakdown": breakdown}

# # API route for cost estimation
# @app.route('/calculate_costs', methods=['POST'])
# def api_calculate_costs():
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         product_list = []
#         for key in request.form:
#             if key.startswith('product_') and request.form[key]:
#                 index = key.split('_')[1]
#                 product = request.form[key]
#                 quantity = request.form.get(f'quantity_{index}', 0)
#                 product_list.append({"product": product, "quantity": quantity})

#         results = calculate_costs(conn, product_list)
#         return jsonify(results)
#     except Exception as e:
#         logging.error(f"Error in cost estimation: {e}")
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# # Route to Recommend Suppliers
# @app.route('/recommend_suppliers', methods=['POST'])
# def recommend_suppliers():
#     try:
#         data = request.form
#         product_keyword = data.get('product_keyword', '')
#         preferred_location = data.get('preferred_location', '')
#         limit = int(data.get('limit', 10))  # Default limit is 10 if not specified

#         conn = connect_db()
#         cursor = conn.cursor()

#         query = """
#         SELECT 
#             Product, 
#             Price, 
#             Location, 
#             URL, 
#             Seller_name 
#         FROM suppliers 
#         WHERE Product LIKE ?
#         """
#         params = [f"%{product_keyword}%"]

#         if preferred_location:
#             query += " AND Location LIKE ?"
#             params.append(f"%{preferred_location}%")

#         query += " LIMIT ?"
#         params.append(limit)

#         cursor.execute(query, params)
#         data = cursor.fetchall()

#         results = [
#             {
#                 "Supplier": row[0],
#                 "Location": row[1],
#                 "Price": row[2],
#                 "Matched Product": row[3],
#                 "URL": row[4],
#             }
#             for row in data
#         ]

#         conn.close()
#         return jsonify({"results": results})

#     except Exception as e:
#         logging.error(f"Error in recommending suppliers: {e}")
#         return jsonify({"error": "An error occurred while fetching recommendations."}), 500

# # Render the home page
# @app.route('/')
# def home():
#     return render_template('index.html')

# # Run the app
# if __name__ == '__main__':
#     app.run(debug=True)

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
                SELECT Product, Price, Location, URL, Seller_name
                FROM fb_jiji_merged_tb
                WHERE LOWER(Product) LIKE LOWER(?)
                LIMIT 1;
            """, (f"%{product_keyword}%",))
            data = cursor.fetchone()

            if data:
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
                })

                cursor.execute(""" 
                    INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, URL)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (data[0], product_keyword, quantity, data[1], cost, data[4], data[2], data[3]))
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
            Seller_name 
        FROM fb_jiji_merged_tb 
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
                "URL": row[3],
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