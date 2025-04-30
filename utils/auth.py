from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Define User model globally
def create_user_model(db):
    class User(UserMixin, db.Model):
        __tablename__ = 'user'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(50), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(128), nullable=False)
        date_joined = db.Column(db.DateTime, default=datetime.utcnow)
        predictions = db.relationship('Prediction', backref='user', lazy=True)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

    return User

# Define Prediction model globally
def create_prediction_model(db):
    class Prediction(db.Model):
        __tablename__ = 'prediction'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        image_path = db.Column(db.String(255))
        video_path = db.Column(db.String(255))
        predicted_sign = db.Column(db.String(50), nullable=False)
        confidence = db.Column(db.Float, nullable=False)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)

        def __repr__(self):
            return f"<Prediction {self.id}: {self.predicted_sign} ({self.confidence:.2f}%)>"

    return Prediction

# Initialize and configure Flask-Login
def init_login_manager(app, db, User):
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login user loader function
        Args:
            user_id: The user ID to load
        Returns:
            User object or None if not found
        """
        return User.query.get(int(user_id))

# Validate user registration
def validate_registration(username, email, password, confirm_password):
    if password != confirm_password:
        return False, "Passwords do not match"

    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return False, "Username must be 3-20 characters and contain only letters, numbers, and underscores"

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, "Please enter a valid email address"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"

    return True, ""

# Register a new user
def register_user(db, User, username, email, password):
    try:
        if User.query.filter_by(username=username).first():
            return False, "Username already taken"
        if User.query.filter_by(email=email).first():
            return False, "Email already registered"

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return True, "Registration successful"

    except Exception as e:
        db.session.rollback()
        return False, f"Registration failed: {str(e)}"

# Save prediction
def save_prediction(db, Prediction, user_id, predicted_sign, confidence, image_path=None, video_path=None):
    try:
        prediction = Prediction(
            user_id=user_id,
            predicted_sign=predicted_sign,
            confidence=confidence,
            image_path=image_path,
            video_path=video_path
        )
        db.session.add(prediction)
        db.session.commit()
        return prediction
    except Exception as e:
        db.session.rollback()
        print(f"Error saving prediction: {str(e)}")
        return None

# Get user predictions
def get_user_predictions(Prediction, user_id, limit=10):
    return Prediction.query.filter_by(user_id=user_id).order_by(Prediction.timestamp.desc()).limit(limit).all()
