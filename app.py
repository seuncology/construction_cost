# # -*- coding: utf-8 -*-
# """
# Created on Fri Jan 10 23:49:45 2025

# @author: emate
# """

# from flask import Flask, request, jsonify
# from flask import Flask, render_template
# from tabulate import tabulate  # For better data presentation

# import sqlite3




# app = Flask(__name__)

# @app.route('/')
# def home():
#     return render_template('index.html')  # Replace 'home.html' with your actual HTML file name

# @app.route('/calculate', methods=['GET', 'POST'])
# def calculate():
#     # Logic for calculating costs
#     return "Calculation results here."


# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         return conn
#     except sqlite3.Error as e:
#         print(f"Error: {e}")
#         return None

# # Function 1: Calculate costs based on product quantities (partial matching)
# def calculate_costs(conn, product_quantities):
#     """
#     Calculate the total cost for specified products and quantities using partial matching.
#     Save results to the database in a new table.
#     """
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

#     # Create a table for calculated costs
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS calculated_costs (
#             Product_Matched TEXT,
#             Keyword TEXT,
#             Quantity INTEGER,
#             Unit_Price REAL,
#             Total_Cost REAL,
#             Supplier TEXT,
#             Location TEXT
#         );
#     """)

#     for product_keyword, quantity in product_quantities.items():
#         cursor.execute(
#             "SELECT MIN(Price) AS cheapest_price, seller_name, Location, Product "
#             "FROM fb_jiji_merged_tb WHERE Product LIKE ?;",
#             (f"%{product_keyword}%",)
#         )
#         data = cursor.fetchone()
#         if data and data[0]:
#             cost = data[0] * quantity
#             total_cost += cost
#             breakdown.append({
#                 "Product (Matched)": data[3],
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": data[0],
#                 "Total Cost": cost,
#                 "Supplier": data[1],
#                 "Location": data[2]
#             })
#             # Insert the result into the database
#             cursor.execute("""
#                 INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
#                 VALUES (?, ?, ?, ?, ?, ?, ?);
#             """, (data[3], product_keyword, quantity, data[0], cost, data[1], data[2]))
#         else:
#             breakdown.append({
#                 "Product (Matched)": "N/A",
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": "N/A",
#                 "Total Cost": "N/A",
#                 "Supplier": "N/A",
#                 "Location": "N/A"
#             })

#     print("\nCost Calculation Breakdown:")
#     print(tabulate(breakdown, headers="keys", tablefmt="pretty"))
#     print(f"\nTotal Cost: {total_cost}")

#     conn.commit()  # Save changes to the database

# # Function 2: Recommend competitive suppliers based on cost and location (partial matching)
# def recommend_suppliers(conn, product_keyword, preferred_location=None):
#     """
#     Recommend competitive suppliers for a product based on partial matching of product name.
#     Save results to the database in a new table.
#     """
#     cursor = conn.cursor()

#     # Create a table for recommended suppliers
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS recommended_suppliers (
#             Supplier TEXT,
#             Location TEXT,
#             Price REAL,
#             Matched_Product TEXT,
#             URL TEXT
#         );
#     """)

#     # Define the basic query to match product names
#     query = "SELECT seller_name, Location, Price, Product, URL FROM fb_jiji_merged_tb WHERE Product LIKE ?"
#     params = [f"%{product_keyword}%"]

#     # Add location filter if provided
#     if preferred_location:
#         query += " AND Location LIKE ?"
#         params.append(f"%{preferred_location}%")

#     query += " ORDER BY Price ASC;"  # Sort by price ascending

#     cursor.execute(query, params)
#     data = cursor.fetchall()

#     if data:
#         print(f"\nCompetitive Suppliers for products containing '{product_keyword}':")
#         print(tabulate(data, headers=["Supplier", "Location", "Price", "Matched Product", "URL"], tablefmt="pretty"))
#         # Insert data into the database
#         for row in data:
#             cursor.execute("""
#                 INSERT INTO recommended_suppliers (Supplier, Location, Price, Matched_Product, URL)
#                 VALUES (?, ?, ?, ?, ?);
#             """, row)
#     else:
#         print(f"\nNo suppliers found for products containing '{product_keyword}' in location: {preferred_location if preferred_location else 'any'}.")

#     conn.commit()  # Save changes to the database


# @app.route('/calculate_costs', methods=['POST'])
# def api_calculate_costs():
#     data = request.json
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500
#     try:
#         # Call the existing calculate_costs function
#         calculate_costs(conn, data["product_quantities"])
#         return jsonify({"message": "Cost calculations completed. Check database for results."})
#     finally:
#         conn.close()

# @app.route('/recommend_suppliers', methods=['POST'])
# def api_recommend_suppliers():
#     data = request.json
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500
#     try:
#         # Call the existing recommend_suppliers function
#         recommend_suppliers(
#             conn, data["product_keyword"], data.get("preferred_location", None)
#         )
#         return jsonify({"message": "Supplier recommendations completed. Check database for results."})
#     finally:
#         conn.close()

# if __name__ == '__main__':
#     app.run(debug=True)

# from flask import Flask, request, jsonify, render_template
# from tabulate import tabulate
# import sqlite3

# app = Flask(__name__)

# # Database connection function
# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         return conn
#     except sqlite3.Error as e:
#         print(f"Error: {e}")
#         return None

# # Function to calculate costs
# def calculate_costs(conn, product_list):
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS calculated_costs (
#             Product_Matched TEXT,
#             Keyword TEXT,
#             Quantity INTEGER,
#             Unit_Price REAL,
#             Total_Cost REAL,
#             Supplier TEXT,
#             Location TEXT
#         );
#     """)

#     for item in product_list:
#         product_keyword = item.get('product')
#         quantity = int(item.get('quantity', 0))

#         if not product_keyword or quantity <= 0:
#             continue

#         cursor.execute(
#             "SELECT MIN(Price) AS cheapest_price, seller_name, Location, Product "
#             "FROM fb_jiji_merged_tb WHERE Product LIKE ?;",
#             (f"%{product_keyword}%",)
#         )
#         data = cursor.fetchone()
#         if data and data[0]:
#             cost = data[0] * quantity
#             total_cost += cost
#             breakdown.append({
#                 "Product (Matched)": data[3],
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": data[0],
#                 "Total Cost": cost,
#                 "Supplier": data[1],
#                 "Location": data[2]
#             })
#             cursor.execute("""
#                 INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
#                 VALUES (?, ?, ?, ?, ?, ?, ?);
#             """, (data[3], product_keyword, quantity, data[0], cost, data[1], data[2]))
#         else:
#             breakdown.append({
#                 "Product (Matched)": "N/A",
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": "N/A",
#                 "Total Cost": "N/A",
#                 "Supplier": "N/A",
#                 "Location": "N/A"
#             })

#     conn.commit()
#     return {"total_cost": total_cost, "breakdown": breakdown}

# # API route for cost estimation
# @app.route('/calculate_costs', methods=['POST'])
# def api_calculate_costs():
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         # Parse form data from the front end
#         product_list = []
#         for key in request.form:
#             if key.startswith('product_') and request.form[key]:
#                 index = key.split('_')[1]
#                 product = request.form[key]
#                 quantity = request.form.get(f'quantity_{index}', 0)
#                 product_list.append({"product": product, "quantity": quantity})

#         # Call the calculate_costs function
#         results = calculate_costs(conn, product_list)

#         # Render the results on a response page (or update as needed for your front end)
#         return render_template('results.html', total_cost=results["total_cost"], breakdown=results["breakdown"])
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# # Serve the HTML file
# @app.route('/')
# def home():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)



# from tabulate import tabulate
# from flask import Flask, request, jsonify, render_template
# import sqlite3

# app = Flask(__name__)

# # Database connection function
# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         return conn
#     except sqlite3.Error as e:
#         print(f"Error: {e}")
#         return None

# # Function to calculate costs
# def calculate_costs(conn, product_list):
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS calculated_costs (
#             Product_Matched TEXT,
#             Keyword TEXT,
#             Quantity INTEGER,
#             Unit_Price REAL,
#             Total_Cost REAL,
#             Supplier TEXT,
#             Location TEXT
#         );
#     """)

#     for item in product_list:
#         product_keyword = item.get('product')
#         quantity = int(item.get('quantity', 0))

#         if not product_keyword or quantity <= 0:
#             continue

#         cursor.execute(
#             "SELECT MIN(Price) AS cheapest_price, seller_name, Location, Product "
#             "FROM fb_jiji_merged_tb WHERE Product LIKE ?;",
#             (f"%{product_keyword}%",)
#         )
#         data = cursor.fetchone()
#         if data and data[0]:
#             cost = data[0] * quantity
#             total_cost += cost
#             breakdown.append({
#                 "Product (Matched)": data[3],
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": data[0],
#                 "Total Cost": cost,
#                 "Supplier": data[1],
#                 "Location": data[2]
#             })
#             cursor.execute("""
#                 INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
#                 VALUES (?, ?, ?, ?, ?, ?, ?);
#             """, (data[3], product_keyword, quantity, data[0], cost, data[1], data[2]))
#         else:
#             breakdown.append({
#                 "Product (Matched)": "N/A",
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": "N/A",
#                 "Total Cost": "N/A",
#                 "Supplier": "N/A",
#                 "Location": "N/A"
#             })

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
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# # Function to recommend suppliers
# def recommend_suppliers(conn, product_keyword, preferred_location=None):
#     cursor = conn.cursor()
#     results = []

#     query = "SELECT seller_name, Location, Price, Product, URL FROM fb_jiji_merged_tb WHERE Product LIKE ?"
#     params = [f"%{product_keyword}%"]

#     if preferred_location:
#         query += " AND Location LIKE ?"
#         params.append(f"%{preferred_location}%")

#     query += " ORDER BY Price ASC;"
#     cursor.execute(query, params)
#     data = cursor.fetchall()

#     for row in data:
#         results.append({
#             "Supplier": row[0],
#             "Location": row[1],
#             "Price": row[2],
#             "Matched_Product": row[3],
#             "URL": row[4]
#         })

#     return results

# @app.route('/recommend_suppliers', methods=['POST'])
# def api_recommend_suppliers():
#     data = request.form
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         product_keyword = data.get("product_keyword")
#         preferred_location = data.get("preferred_location")
#         results = recommend_suppliers(conn, product_keyword, preferred_location)
#         return jsonify({"results": results})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# @app.route('/')
# def home():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)

# from tabulate import tabulate
# from flask import Flask, request, jsonify, render_template
# import sqlite3

# app = Flask(__name__)

# # Database connection function
# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         return conn
#     except sqlite3.Error as e:
#         print(f"Error connecting to database: {e}")
#         return None

# # Validate product list against the database
# def validate_product_list(conn, product_list):
#     cursor = conn.cursor()
#     invalid_products = []
#     for product in product_list:
#         cursor.execute("SELECT 1 FROM fb_jiji_merged_tb WHERE LOWER(Product) LIKE LOWER(?) LIMIT 1;", (f"%{product}%",))
#         if not cursor.fetchone():
#             invalid_products.append(product)
#     return invalid_products

# # Function to calculate costs
# def calculate_costs(conn, product_list):
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

#     # Ensure the table exists
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
#             UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
#         );
#     """)

#     for item in product_list:
#         product_keyword = item.get('product')
#         quantity = int(item.get('quantity', 0))

#         if not product_keyword or quantity <= 0:
#             continue

#         cursor.execute("""
#             SELECT MIN(Price) AS cheapest_price, seller_name, Location, Product 
#             FROM fb_jiji_merged_tb 
#             WHERE LOWER(Product) LIKE LOWER(?)
#             GROUP BY Product 
#             ORDER BY cheapest_price ASC 
#             LIMIT 1;
#         """, (f"%{product_keyword}%",))
#         data = cursor.fetchone()

#         if data:
#             cost = data[0] * quantity
#             total_cost += cost
#             breakdown.append({
#                 "Product (Matched)": data[3],
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": data[0],
#                 "Total Cost": cost,
#                 "Supplier": data[1],
#                 "Location": data[2]
#             })
#             cursor.execute("""
#                 INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
#                 VALUES (?, ?, ?, ?, ?, ?, ?);
#             """, (data[3], product_keyword, quantity, data[0], cost, data[1], data[2]))
#         else:
#             breakdown.append({
#                 "Product (Matched)": "Not Found",
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": "N/A",
#                 "Total Cost": "N/A",
#                 "Supplier": "N/A",
#                 "Location": "N/A"
#             })

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

#         invalid_products = validate_product_list(conn, [item['product'] for item in product_list])
#         if invalid_products:
#             return jsonify({
#                 "error": "Some products are invalid",
#                 "invalid_products": invalid_products
#             }), 400

#         results = calculate_costs(conn, product_list)
#         return jsonify(results)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# # Function to recommend suppliers
# def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
#     cursor = conn.cursor()
#     results = []

#     query = """
#         SELECT seller_name, Location, Price, Product, URL 
#         FROM fb_jiji_merged_tb 
#         WHERE LOWER(Product) LIKE LOWER(?)
#     """
#     params = [f"%{product_keyword}%"]

#     if preferred_location:
#         query += " AND LOWER(Location) LIKE LOWER(?)"
#         params.append(f"%{preferred_location}%")

#     query += " ORDER BY Price ASC LIMIT ? OFFSET ?;"
#     params.extend([limit, offset])
#     cursor.execute(query, params)
#     data = cursor.fetchall()

#     for row in data:
#         results.append({
#             "Supplier": row[0],
#             "Location": row[1],
#             "Price": row[2],
#             "Matched_Product": row[3],
#             "URL": row[4]
#         })

#     return results

# @app.route('/recommend_suppliers', methods=['POST'])
# def api_recommend_suppliers():
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         data = request.form
#         product_keyword = data.get("product_keyword")
#         preferred_location = data.get("preferred_location")
#         limit = int(data.get("limit", 10))
#         offset = int(data.get("offset", 0))

#         if not product_keyword:
#             return jsonify({"error": "Product keyword is required"}), 400

#         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
#         return jsonify({"results": results})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# @app.route('/')
# def home():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)


# from flask import Flask, request, jsonify, render_template
# import sqlite3

# app = Flask(__name__)

# # Database connection function
# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         return conn
#     except sqlite3.Error as e:
#         print(f"Error: {e}")
#         return None

# # Function to calculate costs
# def calculate_costs(conn, product_list):
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS calculated_costs (
#             Product_Matched TEXT,
#             Keyword TEXT,
#             Quantity INTEGER,
#             Unit_Price REAL,
#             Total_Cost REAL,
#             Supplier TEXT,
#             Location TEXT
#         );
#     """)

#     for item in product_list:
#         product_keyword = item.get('product')
#         quantity = int(item.get('quantity', 0))

#         if not product_keyword or quantity <= 0:
#             continue

#         cursor.execute(
#             "SELECT MIN(Price) AS cheapest_price, seller_name, Location, Product "
#             "FROM fb_jiji_merged_tb WHERE Product LIKE ?;",
#             (f"%{product_keyword}%",)
#         )
#         data = cursor.fetchone()
#         if data and data[0]:
#             cost = data[0] * quantity
#             total_cost += cost
#             breakdown.append({
#                 "Product (Matched)": data[3],
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": data[0],
#                 "Total Cost": cost,
#                 "Supplier": data[1],
#                 "Location": data[2]
#             })
#             cursor.execute("""
#                 INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
#                 VALUES (?, ?, ?, ?, ?, ?, ?);
#             """, (data[3], product_keyword, quantity, data[0], cost, data[1], data[2]))
#         else:
#             breakdown.append({
#                 "Product (Matched)": "N/A",
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": "N/A",
#                 "Total Cost": "N/A",
#                 "Supplier": "N/A",
#                 "Location": "N/A"
#             })

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
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# # Function to recommend suppliers
# def recommend_suppliers(conn, product_keyword, preferred_location=None):
#     cursor = conn.cursor()
#     results = []

#     query = "SELECT seller_name, Location, Price, Product, URL FROM fb_jiji_merged_tb WHERE Product LIKE ?"
#     params = [f"%{product_keyword}%"]

#     if preferred_location:
#         query += " AND Location LIKE ?"
#         params.append(f"%{preferred_location}%")

#     query += " ORDER BY Price ASC;"
#     cursor.execute(query, params)
#     data = cursor.fetchall()

#     for row in data:
#         results.append({
#             "Supplier": row[0],
#             "Location": row[1],
#             "Price": row[2],
#             "Matched_Product": row[3],
#             "URL": row[4]
#         })

#     return results

# @app.route('/recommend_suppliers', methods=['POST'])
# def api_recommend_suppliers():
#     data = request.form
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         product_keyword = data.get("product_keyword")
#         preferred_location = data.get("preferred_location")
#         results = recommend_suppliers(conn, product_keyword, preferred_location)
#         return jsonify({"results": results})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# @app.route('/')
# def home():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)


# from tabulate import tabulate
# from flask import Flask, request, jsonify, render_template
# import sqlite3

# app = Flask(__name__)

# # Database connection function
# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         return conn
#     except sqlite3.Error as e:
#         print(f"Error connecting to database: {e}")
#         return None

# # Validate product list against the database
# def validate_product_list(conn, product_list):
#     cursor = conn.cursor()
#     invalid_products = []
#     for product in product_list:
#         cursor.execute("SELECT 1 FROM fb_jiji_merged_tb WHERE LOWER(Product) LIKE LOWER(?) LIMIT 1;", (f"%{product}%",))
#         if not cursor.fetchone():
#             invalid_products.append(product)
#     return invalid_products

# # Function to calculate costs
# def calculate_costs(conn, product_list):
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

#     # Ensure the table exists
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
#             UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
#         );
#     """)

#     for item in product_list:
#         product_keyword = item.get('product')
#         quantity = int(item.get('quantity', 0))

#         if not product_keyword or quantity <= 0:
#             continue

#         cursor.execute("""
#             SELECT MIN(Price) AS cheapest_price, seller_name, Location, Product 
#             FROM fb_jiji_merged_tb 
#             WHERE LOWER(Product) LIKE LOWER(?)
#             GROUP BY Product 
#             ORDER BY cheapest_price ASC 
#             LIMIT 1;
#         """, (f"%{product_keyword}%",))
#         data = cursor.fetchone()

#         if data:
#             cost = data[0] * quantity
#             total_cost += cost
#             breakdown.append({
#                 "Product (Matched)": data[3],
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": data[0],
#                 "Total Cost": cost,
#                 "Supplier": data[1],
#                 "Location": data[2]
#             })
#             cursor.execute("""
#                 INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
#                 VALUES (?, ?, ?, ?, ?, ?, ?);
#             """, (data[3], product_keyword, quantity, data[0], cost, data[1], data[2]))
#         else:
#             breakdown.append({
#                 "Product (Matched)": "Not Found",
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": "N/A",
#                 "Total Cost": "N/A",
#                 "Supplier": "N/A",
#                 "Location": "N/A"
#             })

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

#         invalid_products = validate_product_list(conn, [item['product'] for item in product_list])
#         if invalid_products:
#             return jsonify({
#                 "error": "Some products are invalid",
#                 "invalid_products": invalid_products
#             }), 400

#         results = calculate_costs(conn, product_list)
#         return jsonify(results)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# # Function to recommend suppliers
# def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
#     cursor = conn.cursor()
#     results = []

#     query = """
#         SELECT seller_name, Location, Price, Product, URL 
#         FROM fb_jiji_merged_tb 
#         WHERE LOWER(Product) LIKE LOWER(?)
#     """
#     params = [f"%{product_keyword}%"]

#     if preferred_location:
#         query += " AND LOWER(Location) LIKE LOWER(?)"
#         params.append(f"%{preferred_location}%")

#     query += " ORDER BY Price ASC LIMIT ? OFFSET ?;"
#     params.extend([limit, offset])
#     cursor.execute(query, params)
#     data = cursor.fetchall()

#     for row in data:
#         results.append({
#             "Supplier": row[0],
#             "Location": row[1],
#             "Price": row[2],
#             "Matched_Product": row[3],
#             "URL": row[4]
#         })

#     return results

# @app.route('/recommend_suppliers', methods=['POST'])
# def api_recommend_suppliers():
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         data = request.form
#         product_keyword = data.get("product_keyword")
#         preferred_location = data.get("preferred_location")
#         limit = int(data.get("limit", 10))
#         offset = int(data.get("offset", 0))

#         if not product_keyword:
#             return jsonify({"error": "Product keyword is required"}), 400

#         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
#         return jsonify({"results": results})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# @app.route('/')
# def home():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)


# from tabulate import tabulate
# from flask import Flask, request, jsonify, render_template
# import sqlite3
# import logging

# app = Flask(__name__)

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Database connection function
# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         return conn
#     except sqlite3.Error as e:
#         logging.error(f"Error connecting to database: {e}")
#         return None

# # Validate product list against the database
# def validate_product_list(conn, product_list):
#     cursor = conn.cursor()
#     invalid_products = []
#     for product in product_list:
#         cursor.execute("SELECT 1 FROM fb_jiji_merged_tb WHERE LOWER(Product) LIKE LOWER(?) LIMIT 1;", (f"%{product}%",))
#         if not cursor.fetchone():
#             invalid_products.append(product)
#     return invalid_products

# # Function to calculate costs with best price and reliability criteria
# def calculate_costs(conn, product_list):
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

#     # Ensure the table exists
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
#             Reliability_Score INTEGER,
#             UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
#         );
#     """)

#     for item in product_list:
#         product_keyword = item.get('product')
#         quantity = int(item.get('quantity', 0))

#         if not product_keyword or quantity <= 0:
#             continue

#         cursor.execute("""
#             SELECT Product, Price, seller_name, Location, Reliability_Score
#             FROM fb_jiji_merged_tb
#             WHERE LOWER(Product) LIKE LOWER(?)
#             ORDER BY Reliability_Score DESC, Price ASC
#             LIMIT 1;
#         """, (f"%{product_keyword}%",))
#         data = cursor.fetchone()

#         if data:
#             cost = data[1] * quantity
#             total_cost += cost
#             breakdown.append({
#                 "Product (Matched)": data[0],
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": data[1],
#                 "Total Cost": cost,
#                 "Supplier": data[2],
#                 "Location": data[3],
#                 "Reliability Score": data[4]
#             })
#             cursor.execute("""
#                 INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location, Reliability_Score)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?);
#             """, (data[0], product_keyword, quantity, data[1], cost, data[2], data[3], data[4]))
#         else:
#             breakdown.append({
#                 "Product (Matched)": "Not Found",
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": "N/A",
#                 "Total Cost": "N/A",
#                 "Supplier": "N/A",
#                 "Location": "N/A",
#                 "Reliability Score": "N/A"
#             })

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

#         invalid_products = validate_product_list(conn, [item['product'] for item in product_list])
#         if invalid_products:
#             return jsonify({
#                 "error": "Some products are invalid",
#                 "invalid_products": invalid_products
#             }), 400

#         results = calculate_costs(conn, product_list)
#         return jsonify(results)
#     except Exception as e:
#         logging.error(f"Error in cost calculation: {e}")
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# # Function to recommend suppliers based on reliability and price
# def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
#     cursor = conn.cursor()
#     results = []

#     query = """
#         SELECT seller_name, Location, Price, Product, URL, Reliability_Score
#         FROM fb_jiji_merged_tb
#         WHERE LOWER(Product) LIKE LOWER(?)
#     """
#     params = [f"%{product_keyword}%"]

#     if preferred_location:
#         query += " AND LOWER(Location) LIKE LOWER(?)"
#         params.append(f"%{preferred_location}%")

#     query += " ORDER BY Reliability_Score DESC, Price ASC LIMIT ? OFFSET ?;"
#     params.extend([limit, offset])
#     cursor.execute(query, params)
#     data = cursor.fetchall()

#     for row in data:
#         results.append({
#             "Supplier": row[0],
#             "Location": row[1],
#             "Price": row[2],
#             "Matched_Product": row[3],
#             "URL": row[4],
#             "Reliability Score": row[5]
#         })

#     return results

# @app.route('/recommend_suppliers', methods=['POST'])
# def api_recommend_suppliers():
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         data = request.form
#         product_keyword = data.get("product_keyword")
#         preferred_location = data.get("preferred_location")
#         limit = int(data.get("limit", 10))
#         offset = int(data.get("offset", 0))

#         if not product_keyword:
#             return jsonify({"error": "Product keyword is required"}), 400

#         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
#         return jsonify({"results": results})
#     except Exception as e:
#         logging.error(f"Error in recommending suppliers: {e}")
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# @app.route('/')
# def home():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)


# from tabulate import tabulate
# from flask import Flask, request, jsonify, render_template
# import sqlite3
# import logging

# app = Flask(__name__)
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# def connect_db(db_name="fb_jiji_merged.db"):
#     try:
#         conn = sqlite3.connect(db_name)
#         return conn
#     except sqlite3.Error as e:
#         logging.error(f"Error connecting to database: {e}")
#         return None

# def initialize_database(conn):
#     cursor = conn.cursor()
#     cursor.execute("""
#         ALTER TABLE fb_jiji_merged_tb 
#         ADD COLUMN Reliability_Score REAL DEFAULT 0;
#     """)
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS cost_summary (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             total_cost REAL NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#     """)
#     conn.commit()

# def calculate_costs(conn, product_list):
#     cursor = conn.cursor()
#     total_cost = 0
#     breakdown = []

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
#             UNIQUE(Product_Matched, Keyword, Supplier) ON CONFLICT REPLACE
#         );
#     """)

#     for item in product_list:
#         product_keyword = item.get('product')
#         quantity = int(item.get('quantity', 0))

#         if not product_keyword or quantity <= 0:
#             continue

#         cursor.execute("""
#             SELECT Product, MIN(Price), seller_name, Location, Reliability_Score
#             FROM fb_jiji_merged_tb
#             WHERE LOWER(Product) LIKE LOWER(?)
#             ORDER BY Reliability_Score DESC, Price ASC
#             LIMIT 1;
#         """, (f"%{product_keyword}%",))
#         data = cursor.fetchone()

#         if data:
#             cost = data[1] * quantity
#             total_cost += cost
#             breakdown.append({
#                 "Product (Matched)": data[0],
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": data[1],
#                 "Total Cost": cost,
#                 "Supplier": data[2],
#                 "Location": data[3]
#             })
#             cursor.execute("""
#                 INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
#                 VALUES (?, ?, ?, ?, ?, ?, ?);
#             """, (data[0], product_keyword, quantity, data[1], cost, data[2], data[3]))
#         else:
#             breakdown.append({
#                 "Product (Matched)": "Not Found",
#                 "Keyword": product_keyword,
#                 "Quantity": quantity,
#                 "Unit Price": "N/A",
#                 "Total Cost": "N/A",
#                 "Supplier": "N/A",
#                 "Location": "N/A"
#             })

#     cursor.execute("INSERT INTO cost_summary (total_cost) VALUES (?);", (total_cost,))
#     conn.commit()
#     return {"total_cost": total_cost, "breakdown": breakdown}

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
#         logging.error(f"Error in cost calculation: {e}")
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
#     cursor = conn.cursor()
#     results = []

#     query = """
#         SELECT seller_name, Location, Price, Product, URL, Reliability_Score
#         FROM fb_jiji_merged_tb
#         WHERE LOWER(Product) LIKE LOWER(?)
#     """
#     params = [f"%{product_keyword}%"]

#     if preferred_location:
#         query += " AND LOWER(Location) LIKE LOWER(?)"
#         params.append(f"%{preferred_location}%")

#     query += " ORDER BY Reliability_Score DESC, Price ASC LIMIT ? OFFSET ?;"
#     params.extend([limit, offset])
#     cursor.execute(query, params)
#     data = cursor.fetchall()

#     for row in data:
#         results.append({
#             "Supplier": row[0],
#             "Location": row[1],
#             "Price": row[2],
#             "Matched_Product": row[3],
#             "URL": row[4],
#             "Reliability Score": row[5]
#         })

#     return results

# @app.route('/recommend_suppliers', methods=['POST'])
# def api_recommend_suppliers():
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         data = request.form
#         product_keyword = data.get("product_keyword")
#         preferred_location = data.get("preferred_location")
#         limit = int(data.get("limit", 10))
#         offset = int(data.get("offset", 0))

#         if not product_keyword:
#             return jsonify({"error": "Product keyword is required"}), 400

#         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
#         return jsonify({"results": results})
#     except Exception as e:
#         logging.error(f"Error in recommending suppliers: {e}")
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

# @app.route('/')
# def home():
#     return render_template('index.html')

# if __name__ == '__main__':
#     conn = connect_db()
#     if conn:
#         initialize_database(conn)
#         conn.close()
#     app.run(debug=True)


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
#                 SELECT Product, MIN(Price) AS Best_Price, seller_name, Location, Reliability_Score
#                 FROM fb_jiji_merged_tb
#                 WHERE LOWER(Product) LIKE LOWER(?)
#                 GROUP BY Product
#                 ORDER BY Reliability_Score DESC, Best_Price ASC
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
#                     "Supplier": data[2],
#                     "Location": data[3],
#                     "Reliability Score": data[4]
#                 })

#                 # Store results in the database
#                 cursor.execute("""
#                     INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
#                     VALUES (?, ?, ?, ?, ?, ?, ?);
#                 """, (data[0], product_keyword, quantity, data[1], cost, data[2], data[3]))
#             else:
#                 breakdown.append({
#                     "Product (Matched)": "Not Found",
#                     "Keyword": product_keyword,
#                     "Quantity": quantity,
#                     "Unit Price": "N/A",
#                     "Total Cost": "N/A",
#                     "Supplier": "N/A",
#                     "Location": "N/A"
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
# def recommend_suppliers(conn, product_keyword, preferred_location=None, limit=10, offset=0):
#     cursor = conn.cursor()
#     results = []

#     try:
#         query = """
#             SELECT seller_name, Location, Price, Product, Reliability_Score, URL
#             FROM fb_jiji_merged_tb
#             WHERE LOWER(Product) LIKE LOWER(?)
#         """
#         params = [f"%{product_keyword}%"]

#         if preferred_location:
#             query += " AND LOWER(Location) LIKE LOWER(?)"
#             params.append(f"%{preferred_location}%")

#         query += " ORDER BY Reliability_Score DESC, Price ASC LIMIT ? OFFSET ?;"
#         params.extend([limit, offset])

#         cursor.execute(query, params)
#         data = cursor.fetchall()

#         for row in data:
#             results.append({
#                 "Supplier": row[0],
#                 "Location": row[1],
#                 "Price": row[2],
#                 "Matched Product": row[3],
#                 "Reliability Score": row[4],
#                 "URL": row[5]
#             })
#     except Exception as e:
#         logging.error(f"Error in recommending suppliers: {e}")

#     return results

# # API route for supplier recommendations
# @app.route('/recommend_suppliers', methods=['POST'])
# def api_recommend_suppliers():
#     conn = connect_db()
#     if not conn:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         data = request.form
#         product_keyword = data.get("product_keyword")
#         preferred_location = data.get("preferred_location")
#         limit = int(data.get("limit", 10))
#         offset = int(data.get("offset", 0))

#         if not product_keyword:
#             return jsonify({"error": "Product keyword is required"}), 400

#         results = recommend_suppliers(conn, product_keyword, preferred_location, limit, offset)
#         return jsonify({"results": results})
#     except Exception as e:
#         logging.error(f"Error in supplier recommendation: {e}")
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()

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
                SELECT Product, MIN(Price) AS Best_Price, seller_name, Location, Reliability_Score
                FROM fb_jiji_merged_tb
                WHERE LOWER(Product) LIKE LOWER(?)
                GROUP BY Product
                ORDER BY Reliability_Score DESC, Best_Price ASC
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
                    "Supplier": data[2],
                    "Location": data[3],
                    "Reliability Score": data[4]
                })

                # Store results in the database
                cursor.execute("""
                    INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (data[0], product_keyword, quantity, data[1], cost, data[2], data[3]))
            else:
                breakdown.append({
                    "Product (Matched)": "Not Found",
                    "Keyword": product_keyword,
                    "Quantity": quantity,
                    "Unit Price": "N/A",
                    "Total Cost": "N/A",
                    "Supplier": "N/A",
                    "Location": "N/A"
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
            SELECT seller_name, Location, Price, Product, Reliability_Score, URL
            FROM fb_jiji_merged_tb
            WHERE LOWER(Product) LIKE LOWER(?)
        """
        params = [f"%{product_keyword}%"]

        if preferred_location:
            query += " AND LOWER(Location) LIKE LOWER(?)"
            params.append(f"%{preferred_location}%")

        query += " ORDER BY Reliability_Score DESC, Price ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor.execute(query, params)
        data = cursor.fetchall()

        for row in data:
            results.append({
                "Supplier": row[0],
                "Location": row[1],
                "Price": row[2],
                "Matched Product": row[3],
                "Reliability Score": row[4],
                "URL": row[5]
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
