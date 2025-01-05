import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import time
from datetime import datetime
from sqlalchemy.exc import OperationalError

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection with retry logic
def get_db_connection(max_retries=5, retry_delay=5):
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/transactions')
    for attempt in range(max_retries):
        try:
            engine = create_engine(DATABASE_URL)
            engine.connect()
            logger.info("Database connection successful")
            return engine
        except OperationalError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise
            logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

# Initialize database connection
engine = get_db_connection()
Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'description': self.description,
            'amount': float(self.amount),
            'category': self.category
        }

# Create tables
def init_db():
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Initialize database tables
init_db()

# Create session factory
Session = sessionmaker(bind=engine)

# Predefined spending categories and categorization rules
CATEGORIES = {
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

def validate_csv_headers(headers):
    logger.info(f"Validating CSV headers: {headers}")
    required_fields = {'Date', 'Description', 'Amount'}
    mappings = {
        'Transaction Date': 'Date',
        'Name': 'Description',
        'Merchant': 'Description',
        'Price': 'Amount',
        'Transaction Amount': 'Amount'
    }
    
    normalized_headers = set()
    for header in headers:
        if header in required_fields:
            normalized_headers.add(header)
        elif header in mappings:
            normalized_headers.add(mappings[header])
    
    result = required_fields.issubset(normalized_headers)
    logger.info(f"Headers validation result: {result}")
    return result

def process_csv_data(df):
    try:
        logger.info(f"Starting CSV processing. Initial columns: {df.columns.tolist()}")
        logger.info(f"Initial data shape: {df.shape}")
        
        # Standardize column names
        column_mappings = {
            'Transaction Date': 'Date',
            'Name': 'Description',
            'Merchant': 'Description',
            'Price': 'Amount',
            'Transaction Amount': 'Amount'
        }
        df = df.rename(columns=column_mappings)
        logger.info(f"Columns after mapping: {df.columns.tolist()}")
        
        # Clean amount values
        logger.info("Cleaning amount values")
        logger.debug(f"Sample of original amounts: {df['Amount'].head()}")
        df['Amount'] = df['Amount'].astype(str).str.replace('$', '').str.replace(',', '')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        logger.debug(f"Sample of cleaned amounts: {df['Amount'].head()}")
        
        # Convert dates
        logger.info("Converting dates")
        logger.debug(f"Sample of original dates: {df['Date'].head()}")
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        logger.debug(f"Sample of converted dates: {df['Date'].head()}")
        
        # Drop rows with invalid data
        initial_rows = len(df)
        df = df.dropna(subset=['Date', 'Amount', 'Description'])
        dropped_rows = initial_rows - len(df)
        logger.info(f"Dropped {dropped_rows} rows with invalid data")
        
        # Add category
        logger.info("Categorizing transactions")
        df['Category'] = df['Description'].apply(categorize_transaction)
        category_counts = df['Category'].value_counts()
        logger.info(f"Category distribution: {category_counts.to_dict()}")
        
        return df, None
    except Exception as e:
        logger.error(f"Error in process_csv_data: {str(e)}", exc_info=True)
        return None, str(e)

@app.route('/upload', methods=['POST'])
def upload_csv():
    logger.info("Starting file upload process")
    
    if 'file' not in request.files:
        logger.warning("No file part in request")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    logger.info(f"Received file: {file.filename}")
    
    if not file.filename.endswith('.csv'):
        logger.warning(f"Invalid file type: {file.filename}")
        return jsonify({"error": "File must be a CSV"}), 400

    try:
        # Read CSV with pandas
        logger.info("Reading CSV file")
        df = pd.read_csv(file)
        logger.info(f"Successfully read CSV with shape: {df.shape}")
        
        # Validate headers
        if not validate_csv_headers(df.columns):
            logger.warning(f"Invalid headers found: {df.columns.tolist()}")
            return jsonify({
                "error": "CSV must contain Date, Description, and Amount columns"
            }), 400

        # Process CSV data
        logger.info("Processing CSV data")
        processed_df, error = process_csv_data(df)
        if error:
            logger.error(f"CSV processing error: {error}")
            return jsonify({"error": f"Error processing CSV: {error}"}), 400

        # Save to database
        session = Session()
        try:
            logger.info("Starting database transaction")
            transaction_count = 0
            for _, row in processed_df.iterrows():
                transaction = Transaction(
                    date=row['Date'],
                    description=row['Description'],
                    amount=float(row['Amount']),
                    category=row['Category']
                )
                session.add(transaction)
                transaction_count += 1
                if transaction_count % 100 == 0:
                    logger.info(f"Processed {transaction_count} transactions")
            
            session.commit()
            logger.info(f"Successfully committed {transaction_count} transactions")
            
            stats = {
                "total_rows": len(processed_df),
                "total_amount": float(processed_df['Amount'].sum())
            }
            logger.info(f"Upload statistics: {stats}")
            
            return jsonify({
                "message": "Upload successful",
                "transactions": processed_df.to_dict(orient='records'),
                "stats": stats
            }), 200
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}", exc_info=True)
            return jsonify({"error": "Error saving to database"}), 500
        finally:
            session.close()
            logger.info("Database session closed")

    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        return jsonify({"error": "Error processing file"}), 500

@app.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        session = Session()
        transactions = session.query(Transaction).all()
        return jsonify({
            "transactions": [t.to_dict() for t in transactions]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
