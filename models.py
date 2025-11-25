from datetime import datetime
from extensions import db, bcrypt # Assuming bcrypt is initialized in extensions.py
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.BigInteger)
    library_id = db.Column(db.String(15), unique=True) # e.g., LIB-2024-001
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'member', 'it_admin', name='user_roles'), nullable=False, default='member')
    status = db.Column(db.Enum('active', 'inactive', name='user_statuses'), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    reviews = db.relationship('Review', backref='user', lazy=True)
    borrowed_books = db.relationship('BorrowedBooks', backref='user', lazy=True)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

class Book(db.Model):
    __tablename__ = 'books'
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    genre = db.Column(db.String(40))
    isbn = db.Column(db.String(13), unique=True)
    cover_image = db.Column(db.String(150), nullable=False, default='default.jpg')
    qr_code = db.Column(db.String(60))
    total_copies = db.Column(db.SmallInteger, default=0)
    available_copies = db.Column(db.SmallInteger, default=0)
    description = db.Column(db.Text)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    copies = db.relationship('BookCopy', backref='book', lazy=True)
    reviews = db.relationship('Review', backref='book', lazy=True)
    reservations = db.relationship('Reservation', backref='book', lazy=True)

    def __repr__(self):
        return f"<Book {self.title}>"

class BookCopy(db.Model):
    __tablename__ = 'book_copies'
    copy_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    status = db.Column(db.Enum('available', 'borrowed', 'reserved', 'lost', name='copy_statuses'), default='available', nullable=False)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)

    borrowed_history = db.relationship('BorrowedBooks', backref='copy', lazy=True)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    reservation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('pending', 'approved', 'cancelled', 'completed', name='res_statuses'), default='pending', nullable=False)
    queue_position = db.Column(db.Integer, nullable=False, default=1)

class BorrowedBooks(db.Model):
    __tablename__ = 'borrowed_books'
    borrow_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    copy_id = db.Column(db.Integer, db.ForeignKey('book_copies.copy_id'), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    fine_amount = db.Column(db.Float, default=0.0)

class Review(db.Model):
    __tablename__ = 'reviews'
    review_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    rating = db.Column(db.SmallInteger, nullable=False)
    review_text = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)
# Add this at the end of models.py

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Link to User so we know who sent it
    user = db.relationship('User', backref='feedbacks')