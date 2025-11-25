from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from extensions import db
from models import Book, BookCopy, BorrowedBooks

api = Blueprint('api', __name__)

# ---------------------------------------------------
# 1. GET ALL BOOKS (JSON)
# ---------------------------------------------------
@api.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    
    # We must convert the Database Objects into a Python List/Dictionary
    output = []
    for book in books:
        book_data = {
            'id': book.book_id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'genre': book.genre,
            'available': book.available_copies,
            'cover_image': book.cover_image
        }
        output.append(book_data)
    
    return jsonify({'count': len(output), 'books': output})

# ---------------------------------------------------
# 2. GET SINGLE BOOK DETAIL
# ---------------------------------------------------
@api.route('/books/<int:book_id>', methods=['GET'])
def get_book_detail(book_id):
    book = Book.query.get(book_id)
    
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    book_data = {
        'id': book.book_id,
        'title': book.title,
        'author': book.author,
        'description': book.description,
        'status': 'Available' if book.available_copies > 0 else 'Out of Stock'
    }
    
    return jsonify(book_data)

# ---------------------------------------------------
# 3. BORROW BOOK (API Action)
# ---------------------------------------------------
@api.route('/borrow', methods=['POST'])
@login_required  # Requires session cookie
def borrow_book_api():
    # APIs expect JSON data, not Form data
    data = request.get_json()
    book_id = data.get('book_id')
    
    if not book_id:
        return jsonify({'error': 'Missing book_id'}), 400

    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    available_copy = BookCopy.query.filter_by(book_id=book_id, status='available').first()
    
    if available_copy:
        due_date = datetime.utcnow() + timedelta(days=14)
        
        borrow_record = BorrowedBooks(
            user_id=current_user.user_id,
            copy_id=available_copy.copy_id,
            borrow_date=datetime.utcnow(),
            due_date=due_date
        )
        
        available_copy.status = 'borrowed'
        book.available_copies -= 1
        
        db.session.add(borrow_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Successfully borrowed!',
            'book': book.title,
            'due_date': due_date.strftime('%Y-%m-%d')
        }), 200
    else:
        return jsonify({'error': 'No copies available'}), 400