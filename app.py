import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import numpy as np
from PIL import Image
import tensorflow as tf
from datetime import datetime

# Flask Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# DB & Login Setup
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Load Model
model = tf.keras.models.load_model('isl_model.keras')

# Dynamically load class labels from folder names
DATASET_PATH = "D:/PROJECTS/isl/Indian"   # <-- Replace with your dataset folder path (used during training)
class_labels = sorted([folder for folder in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, folder))])
label_map = {label: label for label in class_labels}  # Mapping is direct: 'A' -> 'A', 'B' -> 'B', etc.



# DB Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    predictions = db.relationship('Prediction', backref='user', lazy=True)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    predicted_class = db.Column(db.String(10), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password != confirm:
            flash("Passwords do not match!")
            return redirect(url_for('signup'))
        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash("Email already registered!")
            return redirect(url_for('signup'))
        new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash("Account created! Login now.")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.timestamp.desc()).limit(5).all()
    return render_template('dashboard.html', predictions=predictions)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        # Preprocess image
        img = Image.open(path).convert("RGB").resize((64, 64))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Predict
        predictions = model.predict(img_array)
        predicted_index = np.argmax(predictions[0])
        predicted_class = class_labels[predicted_index]
        confidence = float(predictions[0][predicted_index])

        # Save to DB
        record = Prediction(filename=filename, predicted_class=predicted_class, confidence=confidence, user_id=current_user.id)
        db.session.add(record)
        db.session.commit()

        return jsonify({
            'predicted_class': predicted_class,
            'confidence': confidence,
            'file_path': url_for('static', filename=f'uploads/{filename}')
        })

    return jsonify({'error': 'Invalid file type'})

@app.route('/predict_sequence', methods=['POST'])
@login_required
def predict_sequence():
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'})

    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No selected files'})

    predictions = []
    word = ""

    for file in sorted(files, key=lambda x: x.filename):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Preprocess image
            img = Image.open(filepath).convert("RGB").resize((64, 64))
            img_array = np.array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            # Predict
            preds = model.predict(img_array)
            predicted_index = np.argmax(preds[0])
            predicted_class = class_labels[predicted_index]
            confidence = float(preds[0][predicted_index]) * 100
            word += predicted_class

            # Save each prediction
            prediction_record = Prediction(
                filename=filename,
                predicted_class=predicted_class,
                confidence=confidence,
                user_id=current_user.id
            )
            db.session.add(prediction_record)
            predictions.append({
                'filename': filename,
                'predicted_class': predicted_class,
                'confidence': round(confidence, 2),
                'file_path': url_for('static', filename=f'uploads/{filename}')
            })

    db.session.commit()

    return jsonify({
        'final_word': word,
        'predictions': predictions
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)