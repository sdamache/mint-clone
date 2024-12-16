import sys
import os
from flask import Flask, request, jsonify
import pandas as pd
from sqlalchemy import create_engine

app = Flask(__name__)

# Database setup
DATABASE_URL = "sqlite:///transactions.db"
engine = create_engine(DATABASE_URL)

# Predefined spending categories and categorization rules
CATEGORIES = {
    "Food": ["grocery", "restaurant", "cafe"],
    "Rent": ["rent"],
    "Utilities": ["electricity", "water", "gas"],
    "Entertainment": ["movie", "concert", "game"],
    "Transportation": ["bus", "train", "taxi"],
    "Healthcare": ["doctor", "pharmacy", "hospital"],
    "Miscellaneous": []
}

def categorize_transaction(description):
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in description.lower():
                return category
    return "Miscellaneous"

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        df['Category'] = df['Description'].apply(categorize_transaction)
        df.to_sql('transactions', engine, if_exists='append', index=False)
        return jsonify({"message": "File uploaded and transactions categorized"}), 200
    return jsonify({"error": "Invalid file format"}), 400

if __name__ == '__main__':
    app.run(debug=True)
