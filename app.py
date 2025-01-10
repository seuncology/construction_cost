# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 23:49:45 2025

@author: emate
"""

from flask import Flask, request, jsonify
from flask import Flask, render_template
from tabulate import tabulate  # For better data presentation

import sqlite3




app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # Replace 'home.html' with your actual HTML file name

@app.route('/calculate', methods=['GET', 'POST'])
def calculate():
    # Logic for calculating costs
    return "Calculation results here."


def connect_db(db_name="fb_jiji_merged.db"):
    try:
        conn = sqlite3.connect(db_name)
        return conn
    except sqlite3.Error as e:
        print(f"Error: {e}")
        return None

# Function 1: Calculate costs based on product quantities (partial matching)
def calculate_costs(conn, product_quantities):
    """
    Calculate the total cost for specified products and quantities using partial matching.
    Save results to the database in a new table.
    """
    cursor = conn.cursor()
    total_cost = 0
    breakdown = []

    # Create a table for calculated costs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calculated_costs (
            Product_Matched TEXT,
            Keyword TEXT,
            Quantity INTEGER,
            Unit_Price REAL,
            Total_Cost REAL,
            Supplier TEXT,
            Location TEXT
        );
    """)

    for product_keyword, quantity in product_quantities.items():
        cursor.execute(
            "SELECT MIN(Price) AS cheapest_price, seller_name, Location, Product "
            "FROM fb_jiji_merged_tb WHERE Product LIKE ?;",
            (f"%{product_keyword}%",)
        )
        data = cursor.fetchone()
        if data and data[0]:
            cost = data[0] * quantity
            total_cost += cost
            breakdown.append({
                "Product (Matched)": data[3],
                "Keyword": product_keyword,
                "Quantity": quantity,
                "Unit Price": data[0],
                "Total Cost": cost,
                "Supplier": data[1],
                "Location": data[2]
            })
            # Insert the result into the database
            cursor.execute("""
                INSERT INTO calculated_costs (Product_Matched, Keyword, Quantity, Unit_Price, Total_Cost, Supplier, Location)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (data[3], product_keyword, quantity, data[0], cost, data[1], data[2]))
        else:
            breakdown.append({
                "Product (Matched)": "N/A",
                "Keyword": product_keyword,
                "Quantity": quantity,
                "Unit Price": "N/A",
                "Total Cost": "N/A",
                "Supplier": "N/A",
                "Location": "N/A"
            })

    print("\nCost Calculation Breakdown:")
    print(tabulate(breakdown, headers="keys", tablefmt="pretty"))
    print(f"\nTotal Cost: {total_cost}")

    conn.commit()  # Save changes to the database

# Function 2: Recommend competitive suppliers based on cost and location (partial matching)
def recommend_suppliers(conn, product_keyword, preferred_location=None):
    """
    Recommend competitive suppliers for a product based on partial matching of product name.
    Save results to the database in a new table.
    """
    cursor = conn.cursor()

    # Create a table for recommended suppliers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommended_suppliers (
            Supplier TEXT,
            Location TEXT,
            Price REAL,
            Matched_Product TEXT,
            URL TEXT
        );
    """)

    # Define the basic query to match product names
    query = "SELECT seller_name, Location, Price, Product, URL FROM fb_jiji_merged_tb WHERE Product LIKE ?"
    params = [f"%{product_keyword}%"]

    # Add location filter if provided
    if preferred_location:
        query += " AND Location LIKE ?"
        params.append(f"%{preferred_location}%")

    query += " ORDER BY Price ASC;"  # Sort by price ascending

    cursor.execute(query, params)
    data = cursor.fetchall()

    if data:
        print(f"\nCompetitive Suppliers for products containing '{product_keyword}':")
        print(tabulate(data, headers=["Supplier", "Location", "Price", "Matched Product", "URL"], tablefmt="pretty"))
        # Insert data into the database
        for row in data:
            cursor.execute("""
                INSERT INTO recommended_suppliers (Supplier, Location, Price, Matched_Product, URL)
                VALUES (?, ?, ?, ?, ?);
            """, row)
    else:
        print(f"\nNo suppliers found for products containing '{product_keyword}' in location: {preferred_location if preferred_location else 'any'}.")

    conn.commit()  # Save changes to the database


@app.route('/calculate_costs', methods=['POST'])
def api_calculate_costs():
    data = request.json
    conn = connect_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        # Call the existing calculate_costs function
        calculate_costs(conn, data["product_quantities"])
        return jsonify({"message": "Cost calculations completed. Check database for results."})
    finally:
        conn.close()

@app.route('/recommend_suppliers', methods=['POST'])
def api_recommend_suppliers():
    data = request.json
    conn = connect_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        # Call the existing recommend_suppliers function
        recommend_suppliers(
            conn, data["product_keyword"], data.get("preferred_location", None)
        )
        return jsonify({"message": "Supplier recommendations completed. Check database for results."})
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
