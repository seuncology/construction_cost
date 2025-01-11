# # # from flask import Flask, request, jsonify, render_template
# # # import sqlite3
# # # import logging

# # # # Initialize Flask app
# # # app = Flask(__name__)

# # # # Configure logging
# # # logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# # # # Database connection function
# # # def connect_db(db_name="fb_jiji_merged.db"):
# # #     try:
# # #         conn = sqlite3.connect(db_name)
# # #         conn.execute("PRAGMA foreign_keys = 1")
# # #         ensure_reliability_score_column(conn)  # Ensure Reliability_Score column exists
# # #         return conn
# # #     except sqlite3.Error as e:
# # #         logging.error(f"Database connection failed: {e}")
# # #         return None

# # # # Ensure Reliability_Score column exists
# # # def ensure_reliability_score_column(conn):
# # #     try:
# # #         cursor = conn.cursor()
# # #         cursor.execute("""
# # #             ALTER TABLE fb_jiji_merged_tb 
# # #             ADD COLUMN Reliability_Score REAL DEFAULT 0.0;
# # #         """)
# # #         conn.commit()
# # #     except sqlite3.Error as e:
# # #         if "duplicate column name" in str(e).lower():
# # #             pass  # Column already exists
# # #         else:
# # #             logging.error(f"Error ensuring Reliability_Score column: {e}")

# # # # Function to calculate Reliability Score
# # # def compute_reliability_score(price, product_matches):
# # #     score = (1 / (price + 1)) * 10  # Higher price should lower reliability score
# # #     score += product_matches * 0.5  # More product matches improve reliability
# # #     return round(score, 2)

# # # # Function to calculate costs
# # # def calculate_costs(conn, product_list):
# # #     cursor = conn.cursor()
# # #     total_cost = 0
# # #     breakdown = []

# # #     # Ensure the table for storing calculated costs exists
# # #     cursor.execute("""
# # #         CREATE TABLE IF NOT EXISTS calculated_costs (
# # #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #             Product_Matched TEXT NOT NULL,
# # #             Keyword TEXT NOT NULL,
# # #             Quantity INTEGER NOT NULL,
# # #             Unit_Price REAL NOT NULL,
# # #             Total_Cost REAL NOT NULL,
# # #             Supplier TEXT,
# # #             Location TEXT,
# # #             Reliability_Score REAL,
# # #             UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
# # #         );
# # #     """)

# # #     for item in product_list:
# # #         product_keyword = item.get('product')
# # #         quantity = item.get('quantity', 0)
# # #         try:
# # #             quantity = int(quantity)
# # #         except ValueError:
# # #             quantity = 0

# # #         if not product_keyword or quantity <= 0:
# # #             continue

# # #         try:
# # #             cursor.execute("""
# # #                 SELECT Product, MIN(Price) AS Best_Price, seller_name, Location
# # #                 FROM fb_jiji_merged_tb
# # #                 WHERE LOWER(Product) LIKE LOWER(?)
# # #                 GROUP BY Product
# # #                 ORDER BY Best_Price ASC
# # #                 LIMIT 1;
# # #             """, (f"%{product_keyword}%",))
# # #             data = cursor.fetchone()

# # #             if data:
# # #                 reliability_score = compute_reliability_score(data[1], 5)  # Example: 5 product matches
# # #                 cost = data[1] * quantity
# # #                 total_cost += cost
# # #                 breakdown.append({
# # #                     "Product (Matched)": data[0],
# # #                     "Keyword": product_keyword,
# # #                     "Quantity": quantity,
# # #                     "Unit Price": data[1],
# # #                     "Total Cost": cost,
# # #                     "Supplier": data[2],
# # #                     "Location": data[3],
# # #                     "Reliability Score": reliability_score
# # #                 })

# # #                 cursor.execute("""
# # #                     INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, Reliability_Score)
# # #                     VALUES (?, ?, ?, ?, ?, ?, ?, ?);
# # #                 """, (data[0], product_keyword, quantity, data[1], cost, data[2], data[3], reliability_score))
# # #             else:
# # #                 breakdown.append({
# # #                     "Product (Matched)": "Not Found",
# # #                     "Keyword": product_keyword,
# # #                     "Quantity": quantity,
# # #                     "Unit Price": "N/A",
# # #                     "Total Cost": "N/A",
# # #                     "Supplier": "N/A",
# # #                     "Location": "N/A",
# # #                     "Reliability Score": "N/A"
# # #                 })
# # #         except Exception as e:
# # #             logging.error(f"Error in cost calculation: {e}")

# # #     conn.commit()
# # #     return {"total_cost": total_cost, "breakdown": breakdown}

# # # # API route for cost estimation
# # # @app.route('/calculate_costs', methods=['POST'])
# # # def api_calculate_costs():
# # #     conn = connect_db()
# # #     if not conn:
# # #         return jsonify({"error": "Database connection failed"}), 500

# # #     try:
# # #         product_list = []
# # #         for key in request.form:
# # #             if key.startswith('product_') and request.form[key]:
# # #                 index = key.split('_')[1]
# # #                 product = request.form[key]
# # #                 quantity = request.form.get(f'quantity_{index}', 0)
# # #                 product_list.append({"product": product, "quantity": quantity})

# # #         results = calculate_costs(conn, product_list)
# # #         return jsonify(results)
# # #     except Exception as e:
# # #         logging.error(f"Error in cost estimation: {e}")
# # #         return jsonify({"error": str(e)}), 500
# # #     finally:
# # #         conn.close()

# # # # Function to recommend suppliers
# # # def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
# # #     cursor = conn.cursor()
# # #     results = []

# # #     try:
# # #         query = """
# # #             SELECT seller_name, Location, Price, Product
# # #             FROM fb_jiji_merged_tb
# # #             WHERE LOWER(Product) LIKE LOWER(?)
# # #         """
# # #         params = [f"%{product_keyword}%"]

# # #         if preferred_location:
# # #             query += " AND LOWER(Location) LIKE LOWER(?)"
# # #             params.append(f"%{preferred_location}%")

# # #         query += " ORDER BY Price ASC LIMIT ? OFFSET ?;"
# # #         params.extend([limit, offset])

# # #         cursor.execute(query, params)
# # #         data = cursor.fetchall()

# # #         for row in data:
# # #             reliability_score = compute_reliability_score(row[2], 5)  # Example: 5 product matches
# # #             results.append({
# # #                 "Supplier": row[0],
# # #                 "Location": row[1],
# # #                 "Price": row[2],
# # #                 "Matched Product": row[3],
# # #                 "Reliability Score": reliability_score
# # #             })
# # #     except Exception as e:
# # #         logging.error(f"Error in recommending suppliers: {e}")

# # #     return results

# # # # API route for supplier recommendations
# # # @app.route('/recommend_suppliers', methods=['POST'])
# # # def api_recommend_suppliers():
# # #     conn = connect_db()
# # #     if not conn:
# # #         return jsonify({"error": "Database connection failed"}), 500

# # #     try:
# # #         data = request.form
# # #         product_keyword = data.get("product_keyword")
# # #         preferred_location = data.get("preferred_location")
# # #         limit = int(data.get("limit", 10))
# # #         offset = int(data.get("offset", 0))

# # #         if not product_keyword:
# # #             return jsonify({"error": "Product keyword is required"}), 400

# # #         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
# # #         return jsonify({"results": results})
# # #     except Exception as e:
# # #         logging.error(f"Error in supplier recommendation: {e}")
# # #         return jsonify({"error": str(e)}), 500
# # #     finally:
# # #         conn.close()

# # # # Render the home page
# # # @app.route('/')
# # # def home():
# # #     return render_template('index.html')

# # # # Run the app
# # # if __name__ == '__main__':
# # #     app.run(debug=True)


# # from flask import Flask, request, jsonify, render_template
# # import sqlite3
# # import logging

# # # Initialize Flask app
# # app = Flask(__name__)

# # # Configure logging
# # logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# # # Database connection function
# # def connect_db(db_name="fb_jiji_merged.db"):
# #     try:
# #         conn = sqlite3.connect(db_name)
# #         conn.execute("PRAGMA foreign_keys = 1")
# #         ensure_reliability_score_column(conn)  # Ensure Reliability_Score column exists
# #         return conn
# #     except sqlite3.Error as e:
# #         logging.error(f"Database connection failed: {e}")
# #         return None

# # # Ensure Reliability_Score column exists
# # def ensure_reliability_score_column(conn):
# #     try:
# #         cursor = conn.cursor()
# #         cursor.execute("""
# #             ALTER TABLE fb_jiji_merged_tb 
# #             ADD COLUMN Reliability_Score REAL DEFAULT 0.0;
# #         """)
# #         conn.commit()
# #     except sqlite3.Error as e:
# #         if "duplicate column name" in str(e).lower():
# #             pass  # Column already exists
# #         else:
# #             logging.error(f"Error ensuring Reliability_Score column: {e}")

# # # Function to calculate Reliability Score
# # def compute_reliability_score(price, product_matches):
# #     score = (1 / (price + 1)) * 10  # Higher price should lower reliability score
# #     score += product_matches * 0.5  # More product matches improve reliability
# #     return round(score, 2)

# # # Function to calculate costs
# # def calculate_costs(conn, product_list):
# #     cursor = conn.cursor()
# #     total_cost = 0
# #     breakdown = []

# #     # Ensure the table for storing calculated costs exists
# #     cursor.execute("""
# #         CREATE TABLE IF NOT EXISTS calculated_costs (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             Product_Matched TEXT NOT NULL,
# #             Keyword TEXT NOT NULL,
# #             Quantity INTEGER NOT NULL,
# #             Unit_Price REAL NOT NULL,
# #             Total_Cost REAL NOT NULL,
# #             Supplier TEXT,
# #             Location TEXT,
# #             Reliability_Score REAL,
# #             UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
# #         );
# #     """)

# #     for item in product_list:
# #         product_keyword = item.get('product')
# #         quantity = item.get('quantity', 0)
# #         try:
# #             quantity = int(quantity)
# #         except ValueError:
# #             quantity = 0

# #         if not product_keyword or quantity <= 0:
# #             continue

# #         try:
# #             cursor.execute("""
# #                 SELECT Product, MIN(Price) AS Best_Price, seller_name, Location
# #                 FROM fb_jiji_merged_tb
# #                 WHERE LOWER(Product) LIKE LOWER(?)
# #                 GROUP BY Product
# #                 ORDER BY Best_Price ASC
# #                 LIMIT 1;
# #             """, (f"%{product_keyword}%",))
# #             data = cursor.fetchone()

# #             if data:
# #                 reliability_score = compute_reliability_score(data[1], 5)  # Example: 5 product matches
# #                 cost = data[1] * quantity
# #                 total_cost += cost
# #                 breakdown.append({
# #                     "Product (Matched)": data[0],
# #                     "Keyword": product_keyword,
# #                     "Quantity": quantity,
# #                     "Unit Price": data[1],
# #                     "Total Cost": cost,
# #                     "Supplier": data[2],
# #                     "Location": data[3],
# #                     "Reliability Score": reliability_score
# #                 })

# #                 cursor.execute("""
# #                     INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, Reliability_Score)
# #                     VALUES (?, ?, ?, ?, ?, ?, ?, ?);
# #                 """, (data[0], product_keyword, quantity, data[1], cost, data[2], data[3], reliability_score))
# #             else:
# #                 breakdown.append({
# #                     "Product (Matched)": "Not Found",
# #                     "Keyword": product_keyword,
# #                     "Quantity": quantity,
# #                     "Unit Price": "N/A",
# #                     "Total Cost": "N/A",
# #                     "Supplier": "N/A",
# #                     "Location": "N/A",
# #                     "Reliability Score": "N/A"
# #                 })
# #         except Exception as e:
# #             logging.error(f"Error in cost calculation: {e}")

# #     conn.commit()
# #     return {"total_cost": total_cost, "breakdown": breakdown}

# # # API route for cost estimation
# # @app.route('/calculate_costs', methods=['POST'])
# # def api_calculate_costs():
# #     conn = connect_db()
# #     if not conn:
# #         return jsonify({"error": "Database connection failed"}), 500

# #     try:
# #         product_list = []
# #         for key in request.form:
# #             if key.startswith('product_') and request.form[key]:
# #                 index = key.split('_')[1]
# #                 product = request.form[key]
# #                 quantity = request.form.get(f'quantity_{index}', 0)
# #                 product_list.append({"product": product, "quantity": quantity})

# #         results = calculate_costs(conn, product_list)
# #         return jsonify(results)
# #     except Exception as e:
# #         logging.error(f"Error in cost estimation: {e}")
# #         return jsonify({"error": str(e)}), 500
# #     finally:
# #         conn.close()

# # # Function to recommend suppliers
# # def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
# #     cursor = conn.cursor()
# #     results = []

# #     try:
# #         query = """
# #             SELECT seller_name, Location, Price, Product
# #             FROM fb_jiji_merged_tb
# #             WHERE LOWER(Product) LIKE LOWER(?)
# #         """
# #         params = [f"%{product_keyword}%"]

# #         if preferred_location:
# #             query += " AND LOWER(Location) LIKE LOWER(?)"
# #             params.append(f"%{preferred_location}%")

# #         query += " ORDER BY Price ASC LIMIT ? OFFSET ?;"
# #         params.extend([limit, offset])

# #         cursor.execute(query, params)
# #         data = cursor.fetchall()

# #         for row in data:
# #             reliability_score = compute_reliability_score(row[2], 5)  # Example: 5 product matches
# #             results.append({
# #                 "Supplier": row[0],
# #                 "Location": row[1],
# #                 "Price": row[2],
# #                 "Matched Product": row[3],
# #                 "Reliability Score": reliability_score
# #             })
# #     except Exception as e:
# #         logging.error(f"Error in recommending suppliers: {e}")

# #     return results

# # # API route for supplier recommendations
# # @app.route('/recommend_suppliers', methods=['POST'])
# # def api_recommend_suppliers():
# #     conn = connect_db()
# #     if not conn:
# #         return jsonify({"error": "Database connection failed"}), 500

# #     try:
# #         data = request.form
# #         product_keyword = data.get("product_keyword")
# #         preferred_location = data.get("preferred_location")
# #         limit = int(data.get("limit", 10))
# #         offset = int(data.get("offset", 0))

# #         if not product_keyword:
# #             return jsonify({"error": "Product keyword is required"}), 400

# #         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
# #         return jsonify({"results": results})
# #     except Exception as e:
# #         logging.error(f"Error in supplier recommendation: {e}")
# #         return jsonify({"error": str(e)}), 500
# #     finally:
# #         conn.close()

# # # Render the home page
# # @app.route('/')
# # def home():
# #     return render_template('index.html')

# # # Run the app
# # if __name__ == '__main__':
# #     app.run(debug=True)

# # from flask import Flask, request, jsonify, render_template
# # import sqlite3
# # import logging

# # # Initialize Flask app
# # app = Flask(__name__)

# # # Configure logging
# # logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# # # Database connection function
# # def connect_db(db_name="fb_jiji_merged.db"):
# #     try:
# #         conn = sqlite3.connect(db_name)
# #         conn.execute("PRAGMA foreign_keys = 1")
# #         ensure_reliability_score_column(conn)  # Ensure Reliability_Score column exists
# #         return conn
# #     except sqlite3.Error as e:
# #         logging.error(f"Database connection failed: {e}")
# #         return None

# # # Ensure Reliability_Score column exists
# # def ensure_reliability_score_column(conn):
# #     try:
# #         cursor = conn.cursor()
# #         cursor.execute("""
# #             ALTER TABLE fb_jiji_merged_tb 
# #             ADD COLUMN Reliability_Score REAL DEFAULT 0.0;
# #         """)
# #         conn.commit()
# #     except sqlite3.Error as e:
# #         if "duplicate column name" in str(e).lower():
# #             pass  # Column already exists
# #         else:
# #             logging.error(f"Error ensuring Reliability_Score column: {e}")

# # # Function to calculate Reliability Score
# # def compute_reliability_score(price, listings_count):
# #     if listings_count == 0:
# #         return 0  # Handle division by zero
# #     score = (1 / (price + 1)) * 10  # Higher price should lower reliability score
# #     score += (1 / listings_count) * 5  # More listings improve reliability
# #     return round(score, 2)

# # # Function to calculate costs
# # def calculate_costs(conn, product_list):
# #     cursor = conn.cursor()
# #     total_cost = 0
# #     breakdown = []

# #     # Ensure the table for storing calculated costs exists
# #     cursor.execute("""
# #         CREATE TABLE IF NOT EXISTS calculated_costs (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             Product_Matched TEXT NOT NULL,
# #             Keyword TEXT NOT NULL,
# #             Quantity INTEGER NOT NULL,
# #             Unit_Price REAL NOT NULL,
# #             Total_Cost REAL NOT NULL,
# #             Supplier TEXT,
# #             Location TEXT,
# #             URL TEXT,
# #             Reliability_Score REAL,
# #             UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
# #         );
# #     """)

# #     for item in product_list:
# #         product_keyword = item.get('product')
# #         quantity = item.get('quantity', 0)
# #         try:
# #             quantity = int(quantity)
# #         except ValueError:
# #             quantity = 0

# #         if not product_keyword or quantity <= 0:
# #             continue

# #         try:
# #             cursor.execute("""
# #                 SELECT Product, MIN(Price) AS Best_Price, Location, URL, Seller_name, Average_Price, Listings_Count, Reliability_Score
# #                 FROM fb_jiji_merged_tb
# #                 WHERE LOWER(Product) LIKE LOWER(?)
# #                 GROUP BY Product
# #                 ORDER BY Best_Price ASC
# #                 LIMIT 1;
# #             """, (f"%{product_keyword}%",))
# #             data = cursor.fetchone()

# #             if data:
# #                 reliability_score = compute_reliability_score(data[1], data[6])  # Example: listings_count
# #                 cost = data[1] * quantity
# #                 total_cost += cost
# #                 breakdown.append({
# #                     "Product (Matched)": data[0],
# #                     "Keyword": product_keyword,
# #                     "Quantity": quantity,
# #                     "Unit Price": data[1],
# #                     "Total Cost": cost,
# #                     "Supplier": data[4],
# #                     "Location": data[2],
# #                     "URL": data[3],
# #                     "Reliability Score": reliability_score
# #                 })

# #                 cursor.execute("""
# #                     INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, URL, Reliability_Score)
# #                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
# #                 """, (data[0], product_keyword, quantity, data[1], cost, data[4], data[2], data[3], reliability_score))
# #             else:
# #                 breakdown.append({
# #                     "Product (Matched)": "Not Found",
# #                     "Keyword": product_keyword,
# #                     "Quantity": quantity,
# #                     "Unit Price": "N/A",
# #                     "Total Cost": "N/A",
# #                     "Supplier": "N/A",
# #                     "Location": "N/A",
# #                     "URL": "N/A",
# #                     "Reliability Score": "N/A"
# #                 })
# #         except Exception as e:
# #             logging.error(f"Error in cost calculation: {e}")

# #     conn.commit()
# #     return {"total_cost": total_cost, "breakdown": breakdown}

# # # API route for cost estimation
# # @app.route('/calculate_costs', methods=['POST'])
# # def api_calculate_costs():
# #     conn = connect_db()
# #     if not conn:
# #         return jsonify({"error": "Database connection failed"}), 500

# #     try:
# #         product_list = []
# #         for key in request.form:
# #             if key.startswith('product_') and request.form[key]:
# #                 index = key.split('_')[1]
# #                 product = request.form[key]
# #                 quantity = request.form.get(f'quantity_{index}', 0)
# #                 product_list.append({"product": product, "quantity": quantity})

# #         results = calculate_costs(conn, product_list)
# #         return jsonify(results)
# #     except Exception as e:
# #         logging.error(f"Error in cost estimation: {e}")
# #         return jsonify({"error": str(e)}), 500
# #     finally:
# #         conn.close()

# # # Function to recommend suppliers
# # def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
# #     cursor = conn.cursor()
# #     results = []

# #     try:
# #         query = """
# #             SELECT Seller_name, Location, Price, URL, Product, Reliability_Score
# #             FROM fb_jiji_merged_tb
# #             WHERE LOWER(Product) LIKE LOWER(?)
# #         """
# #         params = [f"%{product_keyword}%"]

# #         if preferred_location:
# #             query += " AND LOWER(Location) LIKE LOWER(?)"
# #             params.append(f"%{preferred_location}%")

# #         query += " ORDER BY Price ASC LIMIT ? OFFSET ?;"
# #         params.extend([limit, offset])

# #         cursor.execute(query, params)
# #         data = cursor.fetchall()

# #         for row in data:
# #             results.append({
# #                 "Supplier": row[0],
# #                 "Location": row[1],
# #                 "Price": row[2],
# #                 "URL": row[3],
# #                 "Matched Product": row[4],
# #                 "Reliability Score": row[5]
# #             })
# #     except Exception as e:
# #         logging.error(f"Error in recommending suppliers: {e}")

# #     return results

# # # API route for supplier recommendations
# # @app.route('/recommend_suppliers', methods=['POST'])
# # def api_recommend_suppliers():
# #     conn = connect_db()
# #     if not conn:
# #         return jsonify({"error": "Database connection failed"}), 500

# #     try:
# #         data = request.form
# #         product_keyword = data.get("product_keyword")
# #         preferred_location = data.get("preferred_location")
# #         limit = int(data.get("limit", 10))
# #         offset = int(data.get("offset", 0))

# #         if not product_keyword:
# #             return jsonify({"error": "Product keyword is required"}), 400

# #         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
# #         return jsonify({"results": results})
# #     except Exception as e:
# #         logging.error(f"Error in supplier recommendation: {e}")
# #         return jsonify({"error": str(e)}), 500
# #     finally:
# #         conn.close()

# # # Render the home page
# # @app.route('/')
# # def home():
# #     return render_template('index.html')

# # # Run the app
# # if __name__ == '__main__':
# #     app.run(debug=True)

# from flask import Flask, request, jsonify, render_template
# import sqlite3
# import logging

# # Initialize Flask app
# app = Flask(__name__)

# # Configure logging
# logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# # Database connection function
# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         conn.execute("PRAGMA foreign_keys = 1")
#         ensure_reliability_score_column(conn)  # Ensure Reliability_Score column exists
#         return conn
#     except sqlite3.Error as e:
#         logging.error(f"Database connection failed: {e}")
#         return None

# # Ensure Reliability_Score column exists
# def ensure_reliability_score_column(conn):
#     try:
#         cursor = conn.cursor()
#         cursor.execute("""
#             ALTER TABLE fb_jiji_merged_tb 
#             ADD COLUMN Reliability_Score REAL DEFAULT 0.0;
#         """)
#         conn.commit()
#     except sqlite3.Error as e:
#         if "duplicate column name" in str(e).lower():
#             pass  # Column already exists
#         else:
#             logging.error(f"Error ensuring Reliability_Score column: {e}")

# # Function to calculate Reliability Score
# def compute_reliability_score(price, listings_count):
#     if listings_count == 0:
#         return 0  # Handle division by zero
#     score = (1 / (price + 1)) * 10  # Higher price should lower reliability score
#     score += (1 / listings_count) * 5  # More listings improve reliability
#     return round(score, 2)

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
#             Reliability_Score REAL,
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
#                 SELECT Product, MIN(Price) AS Best_Price, Location, URL, Seller_name, Average_Price, Listings_Count, Reliability_Score
#                 FROM fb_jiji_merged_tb
#                 WHERE LOWER(Product) LIKE LOWER(?)
#                 GROUP BY Product
#                 ORDER BY Best_Price ASC
#                 LIMIT 1;
#             """, (f"%{product_keyword}%",))
#             data = cursor.fetchone()

#             if data:
#                 reliability_score = compute_reliability_score(data[1], data[6])  # Example: listings_count
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
#                     "Reliability Score": reliability_score
#                 })

#                 cursor.execute("""
#                     INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, URL, Reliability_Score)
#                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
#                 """, (data[0], product_keyword, quantity, data[1], cost, data[4], data[2], data[3], reliability_score))
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
#                     "Reliability Score": "N/A"
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

# # Function to recommend suppliers
# def recommend_suppliers(conn, product_keyword, preferred_location, limit, offset):
#     try:
#         cursor = conn.cursor()

#         # SQL query to retrieve supplier recommendations
#         query = """
#         SELECT 
#             Product, 
#             Price, 
#             Location, 
#             URL, 
#             Seller_name, 
#             Average_Price, 
#             Listings_Count, 
#             Reliability_Score 
#         FROM suppliers 
#         WHERE Product LIKE ?
#         """
#         params = [f"%{product_keyword}%"]

#         # Add location filter if specified
#         if preferred_location:
#             query += " AND Location LIKE ?"
#             params.append(f"%{preferred_location}%")

#         # Add limit and offset
#         query += " LIMIT ? OFFSET ?"
#         params.extend([limit, offset])

#         # Execute the query
#         cursor.execute(query, params)
#         data = cursor.fetchall()

#         # Map results to the expected output format
#         results = []
#         for row in data:
#             # Ensure all fields are mapped correctly
#             product = row[0]
#             price = row[1]
#             location = row[2]
#             url = row[3]
#             seller_name = row[4]
#             average_price = row[5]
#             listings_count = row[6]
#             reliability_score = row[7] if row[7] is not None else 0.0  # Default reliability score if None

#             results.append({
#                 "Matched Product": product,           # Include the product name
#                 "Price": price,                       # Current price of the product
#                 "Location": location,                 # Supplier location
#                 "URL": url,                           # Supplier/product URL
#                 "Supplier": seller_name,              # Name of the supplier
#                 "Average Price": average_price,       # Average price of the product
#                 "Listings Count": listings_count,     # Number of product listings
#                 "Reliability Score": reliability_score  # Reliability score of the supplier
#             })

#         return results

#     except Exception as e:
#         logging.error(f"Error in recommending suppliers: {e}")
#         return []

# # # API route for supplier recommendations
# # @app.route('/recommend_suppliers', methods=['POST'])
# # def api_recommend_suppliers():
# #     conn = connect_db()
# #     if not conn:
# #         return jsonify({"error": "Database connection failed"}), 500

# #     try:
# #         data = request.form
# #         product_keyword = data.get("product_keyword")
# #         preferred_location = data.get("preferred_location")
# #         limit = int(data.get("limit", 10))
# #         offset = int(data.get("offset", 0))

# #         if not product_keyword:
# #             return jsonify({"error": "Product keyword is required"}), 400

# #         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
# #         return jsonify({"results": results})
# #     except Exception as e:
# #         logging.error(f"Error in supplier recommendation: {e}")
# #         return jsonify({"error": str(e)}), 500
# #     finally:
# #         conn.close()

# @app.route('/recommend_suppliers', methods=['POST'])
# def recommend_suppliers():
#     try:
#         product_keyword = request.form.get('product_keyword')
#         preferred_location = request.form.get('preferred_location')
#         limit = int(request.form.get('limit', 0))  # Default to 0 (no limit)

#         # Query the database for matching suppliers
#         query = db.session.query(Supplier).filter(Supplier.product.ilike(f"%{product_keyword}%"))
#         if preferred_location:
#             query = query.filter(Supplier.location.ilike(f"%{preferred_location}%"))
        
#         results = query.limit(limit).all() if limit > 0 else query.all()

#         # Prepare the output
#         response = {
#             "results": [
#                 {
#                     "Supplier": supplier.name,
#                     "Location": supplier.location,
#                     "Price": supplier.price,
#                     "Matched Product": supplier.product,
#                     "Reliability Score": supplier.reliability_score,
#                     "URL": supplier.url,
#                 }
#                 for supplier in results
#             ]
#         }
#         return jsonify(response)
#     except Exception as e:
#         logging.error(f"Error fetching supplier recommendations: {e}")
#         return jsonify({"error": "An error occurred while fetching recommendations."}), 500


# # Function to recommend suppliers
# # Function to recommend suppliers
# # def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
# #     cursor = conn.cursor()
# #     results = []

# #     try:
# #         query = """
# #             SELECT Product, Price, Location, URL, Seller_name, Reliability_Score
# #             FROM fb_jiji_merged_tb
# #             WHERE LOWER(Product) LIKE LOWER(?)
# #         """
# #         params = [f"%{product_keyword}%"]

# #         if preferred_location:
# #             query += " AND LOWER(Location) LIKE LOWER(?)"
# #             params.append(f"%{preferred_location}%")

# #         query += " ORDER BY Price ASC LIMIT ? OFFSET ?;"
# #         params.extend([limit, offset])

# #         cursor.execute(query, params)
# #         data = cursor.fetchall()

# #         for row in data:
# #             # Ensure all required fields are properly mapped
# #             product = row[0]
# #             price = row[1]
# #             location = row[2]
# #             url = row[3]
# #             seller_name = row[4]
# #             reliability_score = row[5] if row[5] is not None else 0.0  # Default reliability score if None

# #             results.append({
# #                 "Matched Product": product,  # Explicitly include the product name
# #                 "Price": price,
# #                 "Location": location,
# #                 "URL": url,
# #                 "Supplier": seller_name,
# #                 "Reliability Score": reliability_score  # Include reliability score in the output
# #             })
# #     except Exception as e:
# #         logging.error(f"Error in recommending suppliers: {e}")

# #     return results


# # # API route for supplier recommendations
# # @app.route('/recommend_suppliers', methods=['POST'])
# # def api_recommend_suppliers():
# #     conn = connect_db()
# #     if not conn:
# #         return jsonify({"error": "Database connection failed"}), 500

# #     try:
# #         data = request.form
# #         product_keyword = data.get("product_keyword")
# #         preferred_location = data.get("preferred_location")
# #         limit = int(data.get("limit", 10))
# #         offset = int(data.get("offset", 0))

# #         if not product_keyword:
# #             return jsonify({"error": "Product keyword is required"}), 400

# #         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
# #         return jsonify({"results": results})
# #     except Exception as e:
# #         logging.error(f"Error in supplier recommendation: {e}")
# #         return jsonify({"error": str(e)}), 500
# #     finally:
# #         conn.close()

# # # Render the home page
# # @app.route('/')
# # def home():
# #     return render_template('index.html')

# # # Run the app
# # if __name__ == '__main__':
# #     app.run(debug=True)


# # # API route for supplier recommendations
# # @app.route('/recommend_suppliers', methods=['POST'])
# # def api_recommend_suppliers():
# #     conn = connect_db()
# #     if not conn:
# #         return jsonify({"error": "Database connection failed"}), 500

# #     try:
# #         data = request.form
# #         product_keyword = data.get("product_keyword")
# #         preferred_location = data.get("preferred_location")
# #         limit = int(data.get("limit", 10))
# #         offset = int(data.get("offset", 0))

# #         if not product_keyword:
# #             return jsonify({"error": "Product keyword is required"}), 400

# #         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
# #         return jsonify({"results": results})
# #     except Exception as e:
# #         logging.error(f"Error in supplier recommendation: {e}")
# #         return jsonify({"error": str(e)}), 500
# #     finally:
# #         conn.close()

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

 #Database connection function
def connect_db(db_name="fb_jiji_merged.db"):
    try:
        conn = sqlite3.connect(db_name)
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
    if listings_count == 0:
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

# Function to recommend suppliers
def recommend_suppliers(conn, product_keyword, preferred_location, limit, offset):
    try:
        cursor = conn.cursor()

        # SQL query to retrieve supplier recommendations
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

        # Add location filter if specified
        if preferred_location:
            query += " AND Location LIKE ?"
            params.append(f"%{preferred_location}%")

        # Add limit and offset
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # Execute the query
        cursor.execute(query, params)
        data = cursor.fetchall()

        # Map results to the expected output format
        results = []
        for row in data:
            # Ensure all fields are mapped correctly
            product = row[0]
            price = row[1]
            location = row[2]
            url = row[3]
            seller_name = row[4]
            average_price = row[5]
            listings_count = row[6]
            reliability_score = row[7] if row[7] is not None else 0.0  # Default reliability score if None

            results.append({
                "Matched Product": product,           # Include the product name
                "Price": price,                       # Current price of the product
                "Location": location,                 # Supplier location
                "URL": url,                           # Supplier/product URL
                "Supplier": seller_name,              # Name of the supplier
                "Average Price": average_price,       # Average price of the product
                "Listings Count": listings_count,     # Number of product listings
                "Reliability Score": reliability_score  # Reliability score of the supplier
            })

        return results

    except Exception as e:
        logging.error(f"Error in recommending suppliers: {e}")
        return []
    
# Supplier recommendation function using SQLite
@app.route('/get_supplier_recommendations', methods=['POST'])
def get_supplier_recommendations():
    try:
        data = request.get_json()
        product_keyword = data.get('product_keyword', '')
        preferred_location = data.get('preferred_location', '')
        limit = data.get('limit', 10)

        conn = connect_db()
        if not conn:
            return jsonify({"error": "Database connection failed."}), 500

        cursor = conn.cursor()

        # Build the query dynamically
        query = "SELECT name, location, price, product, reliability_score, url FROM fb_jiji_merged_tb WHERE product LIKE ?"
        params = ["%" + product_keyword + "%"]

        if preferred_location:
            query += " AND location LIKE ?"
            params.append("%" + preferred_location + "%")

        query += " LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Prepare the output
        response = {
            "results": [
                {
                    "Supplier": row[0],
                    "Location": row[1],
                    "Price": row[2],
                    "Matched Product": row[3],
                    "Reliability Score": row[4],
                    "URL": row[5],
                }
                for row in results
            ]
        }

        conn.close()
        return jsonify(response)

    except Exception as e:
        logging.error("Error fetching supplier recommendations: " + str(e))
        return jsonify({"error": "An error occurred while fetching recommendations."}), 500

# Render the home page
@app.route('/')
def home():
    return render_template('index.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)