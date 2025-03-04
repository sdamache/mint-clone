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

def get_allowed_origins():
    # Accept any GitHub Codespace URL and localhost
    return [
        r"^https:\/\/.*\.app\.github\.dev$",  # Any GitHub Codespace URL
        r"^http:\/\/localhost:[0-9]+$"        # Any localhost port
    ]

app = Flask(__name__)
CORS(app, 
     resources={r"/*": {
         "origins": ["https://shiny-couscous-9wgrqgg7qp939pj5-3000.app.github.dev",
                     "https://cuddly-acorn-67q97qg94624p7r-3000.app.github.dev", 
                    "http://localhost:3000",
                    "http://localhost:5001/upload"],
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type"],
         "expose_headers": ["Content-Type"],
         "supports_credentials": True
     }})

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection with retry logic
def get_db_connection(max_retries=5, retry_delay=5):
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/transactions?sslmode=disable')
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
        
        # Replace NaN values in Debit and Credit columns with 0
        df['Debit'] = df['Debit'].fillna(0)
        df['Credit'] = df['Credit'].fillna(0)
        
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
        
        # Replace NaN values with None
        df = df.where(pd.notnull(df), None)
        
        # Replace None values with 0 in Debit and Credit columns
        df['Debit'] = df['Debit'].apply(lambda x: 0 if x is None else x)
        df['Credit'] = df['Credit'].apply(lambda x: 0 if x is None else x)
        
        # Format dates as ISO strings
        df['Date'] = df['Date'].apply(lambda x: x.isoformat() if x is not None else None)
        
        return df, None
    except Exception as e:
        logger.error(f"Error in process_csv_data: {str(e)}", exc_info=True)
        return None, str(e)

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_csv():
    if request.method == 'OPTIONS':
        # Respond to preflight request
        return '', 204
        
    logger.info("Starting file upload process")
    logger.debug("Request Files: %s", request.files)
    
    try:
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        logger.info(f"Received file: {file.filename}")
        
        if not file or file.filename == '':
            logger.warning("No selected file")
            return jsonify({"error": "No selected file"}), 400
            
        if not file.filename.endswith('.csv'):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({"error": "File must be a CSV"}), 400

        # Read CSV with pandas
        logger.info("Reading CSV file")
        df = pd.read_csv(file, encoding='utf-8')
        logger.info(f"Successfully read CSV with shape: {df.shape}")
        
        # Validate headers
        if not validate_csv_headers(df.columns):
            logger.warning(f"Invalid headers found: {df.columns.tolist()}")
            return jsonify({
                "error": f"CSV must contain Date, Description, and Amount columns. Found columns: {', '.join(df.columns.tolist())}"
            }), 400

        # Process CSV data
        logger.info("Processing CSV data")
        processed_df, error = process_csv_data(df)
        if error:
            logger.error(f"CSV processing error: {error}")
            return jsonify({"error": f"Error processing CSV: {error}"}), 400

        # Log the processed data
        logger.info(f"Processed data: {processed_df.to_dict(orient='records')}")

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
            
            response = jsonify({
                "message": "Upload successful",
                "transactions": processed_df.to_dict(orient='records'),
                "stats": stats
            })
            logger.info(f"Response: {response.get_data(as_text=True)}")
            return response, 200
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}", exc_info=True)
            return jsonify({"error": "Error saving to database"}), 500
        finally:
            session.close()
            logger.info("Database session closed")

    except pd.errors.EmptyDataError:
        logger.error("Empty CSV file uploaded")
        return jsonify({"error": "The uploaded CSV file is empty"}), 400
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error: {str(e)}")
        return jsonify({"error": "Unable to parse CSV file. Please check the file format"}), 400
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

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
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
