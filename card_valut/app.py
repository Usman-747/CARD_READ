
def save_card():
    data = request.get_json()
    required_fields = ['name', 'company', 'job_title', 'card_number', 'email', 'phone_number', 'website', 'address']
    # Ensure all required fields are present
    for field in required_fields:
        if field not in data:
            data[field] = None
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS business_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                company TEXT,
                job_title TEXT,
                card_number INTEGER UNIQUE,
                email TEXT,
                phone_number TEXT,
                address TEXT,
                website TEXT,
                raw_text TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO business_cards (name, company, job_title, card_number, email, phone_number, website, address, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('company'),
            data.get('job_title'),
            data.get('card_number'),
            data.get('email'),
            data.get('phone_number'),
            data.get('website'),
            data.get('address'),
            data.get('raw_text')
        ))
        db.commit()
        return jsonify({'success': True, 'message': 'Card saved to database.'})
    except Exception as e:
        print('Save card error:', e)
        return jsonify({'success': False, 'error': str(e)}), 500
from flask import Flask, render_template, request, jsonify, g
import pytesseract
from PIL import Image
import re
import os
import sqlite3

app = Flask(__name__)

@app.route('/save_card', methods=['POST'])

# Database configuration using sqlite3's own methods
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # This will create 'cards.db' in the current working directory
        db = g._database = sqlite3.connect('cards.db')
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Configure allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route renders the only HTML file
@app.route('/')
def index():
    return render_template('index.html')

# OCR endpoint for image uploads
@app.route('/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    
    # Check if file is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        print('Starting OCR processing...')
        img = Image.open(file.stream)
        text = pytesseract.image_to_string(img)
        print('OCR text extracted:', text)


        # Extract information using regex patterns
        patterns = {
            'name': r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',
            'company': r'(?i)(?<=Company:)[\w\s]+',
            'job_title': r'(?i)(?<=Title:)[\w\s]+',
            'card_number': r'\b\d{8,16}\b',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone_number': r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'website': r'(?:http[s]?://)?(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+',
            'address': r'\d+\s+[\w\s.,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)[\w\s.,]*',
        }

        extracted_info = {}
        lines = text.split('\n')

        # Process each line for different types of information
        for line in lines:
            line = line.strip()
            if line:
                for key, pattern in patterns.items():
                    if key not in extracted_info:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            extracted_info[key] = match.group(0)

        # If phone_number not found, try to extract from the whole text
        if not extracted_info.get('phone_number'):
            phone_matches = re.findall(r'(?:\\+?\\d{1,3}[\\s.-]?)?(?:\\(?\\d{2,4}\\)?[\\s.-]?)?\\d{3,4}[\\s.-]?\\d{3,4}', text)
            # Filter out matches that are too short or too long
            phone_matches = [p for p in phone_matches if 7 <= len(re.sub(r'\\D', '', p)) <= 15]
            if phone_matches:
                extracted_info['phone_number'] = phone_matches[0]

        # Ensure all required fields for DB insert are present (use None if missing)
        for field in ['name', 'company', 'job_title', 'card_number', 'email', 'phone_number', 'website', 'address']:
            if field not in extracted_info:
                extracted_info[field] = None

        print('Extracted info:', extracted_info)
        extracted_info['raw_text'] = text

        # Try to save to database, but don't break if it fails
        try:
            print('Connecting to database...')
            db = get_db()
            cursor = db.cursor()
            print('Creating table if not exists...')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS business_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    company TEXT,
                    job_title TEXT,
                    card_number INTEGER UNIQUE,
                    email TEXT,
                    phone_number TEXT,
                    address TEXT,
                    website TEXT,
                    raw_text TEXT
                )
            ''')
            print('Inserting data into table...')
            cursor.execute('''
                INSERT INTO business_cards (name, company, job_title, email, phone_number, website, address, card_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                extracted_info.get('name'),
                extracted_info.get('company'),
                extracted_info.get('job_title'),
                extracted_info.get('email'),
                extracted_info.get('phone_number'),
                extracted_info.get('website'),
                extracted_info.get('address'),
                extracted_info.get('card_number')
            ))
            db.commit()
            print('Data committed to database.')
        except Exception as db_error:
            print('Database error:', db_error)
            extracted_info['db_error'] = str(db_error)

        return jsonify(extracted_info)
    except Exception as e:
        print('General error:', e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)