import sys
import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, g, current_app
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, DateTime, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text as sa_text
from time import time
from flask_cors import CORS
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS

# Request tracking middleware
@app.before_request
def start_timer():
    g.start = time()

@app.after_request
def log_request(response):
    if request.path != '/health':  # Skip logging health checks
        now = time()
        duration = round(now - g.start, 2)
        logger.info(
            f'Request: {request.method} {request.path} - '
            f'Status: {response.status_code} - '
            f'Duration: {duration}s - '
            f'IP: {request.remote_addr}'
        )
    return response

# Database setup
DATABASE_URL = "postgresql://postgres:postgres@db:5432/mintclone"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define transactions table
transactions_table = Table(
    'transactions',
    metadata,
    Column('Date', String),
    Column('Description', String),
    Column('Amount', Float),
    Column('Category', String),
    Column('uploaded_at', DateTime)
)

# Initialize the database
def init_db():
    """Initialize the database"""
    try:
        metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

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
    try:
        if 'file' not in request.files:
            logger.warning('No file part in request')
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning('No selected file')
            return jsonify({"error": "No selected file"}), 400
            
        if file and file.filename.endswith('.csv'):
            logger.info(f'Processing file: {file.filename}')
            df = pd.read_csv(file)
            
            # Add debug logging
            logger.debug(f'CSV columns: {df.columns.tolist()}')
            
            # Validate required columns
            required_columns = ['Date', 'Description', 'Debit', 'Credit']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return jsonify({
                    "error": f"Missing required columns: {', '.join(missing_columns)}",
                    "available_columns": df.columns.tolist()
                }), 400

            # Calculate Amount from Debit and Credit
            df['Amount'] = df.apply(lambda row: row['Credit'] - row['Debit'], axis=1)
            
            # Ensure proper column names
            df = df.rename(columns={
                'Description': 'Description',
                'Date': 'Date',
                'Amount': 'Amount'
            })
            
            df['Category'] = df['Description'].apply(categorize_transaction)
            df['uploaded_at'] = datetime.now()
            
            rows_processed = len(df)
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Insert records using SQLAlchemy Core
            with engine.begin() as connection:
                for record in records:
                    connection.execute(
                        transactions_table.insert(),
                        record
                    )
            
            logger.info(f'Successfully processed {rows_processed} transactions')
            response_data = {
                "message": "File uploaded and transactions categorized",
                "rows_processed": rows_processed,
                "transactions": records
            }
            logger.debug(f'Sending response: {response_data}')
            return jsonify(response_data), 200
            
    except Exception as e:
        logger.error(f'Error processing upload: {str(e)}\n{traceback.format_exc()}')
        return jsonify({"error": str(e)}), 500

@app.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        with engine.connect() as connection:
            result = connection.execute(text('SELECT * FROM transactions ORDER BY "Date" DESC'))
            transactions = [dict(row._mapping) for row in result]
            logger.info(f'Retrieved {len(transactions)} transactions')
            return jsonify({"transactions": transactions}), 200
    except Exception as e:
        logger.error(f'Error fetching transactions: {str(e)}', exc_info=True)
        return jsonify({"error": "Failed to fetch transactions"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5001)
