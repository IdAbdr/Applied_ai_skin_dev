import os
import random
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Dummy disease list
DISEASES = [
    "Acne",
    "Eczema",
    "Psoriasis",
    "Melanoma",
    "Dermatitis"
]

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------
# DATABASE INIT
# -----------------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS prediction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            disease TEXT,
            probability REAL,
            timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()


# -----------------------
# HELPER FUNCTIONS
# -----------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def mock_prediction():
    disease = random.choice(DISEASES)
    probability = round(random.uniform(0.7, 0.99), 2)
    return disease, probability


# -----------------------
# ROUTES
# -----------------------
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return "No file part", 400

    file = request.files['image']

    if file.filename == '':
        return "No selected file", 400

    if not allowed_file(file.filename):
        return "Invalid file type", 400

    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Mock prediction
    disease, probability = mock_prediction()

    # Save to DB
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        INSERT INTO prediction (filename, disease, probability, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (filename, disease, probability, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

    return redirect(url_for('result', filename=filename, disease=disease, probability=probability))


@app.route('/result')
def result():
    filename = request.args.get('filename')
    disease = request.args.get('disease')
    probability = request.args.get('probability')

    return render_template('result.html',
                           filename=filename,
                           disease=disease,
                           probability=probability)


@app.route('/history')
def history():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('SELECT * FROM prediction ORDER BY id DESC')
    data = c.fetchall()

    conn.close()

    return render_template('history.html', data=data)


# -----------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)