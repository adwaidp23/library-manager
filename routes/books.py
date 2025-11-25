import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models import Book, BookCopy, BorrowedBooks, Review, Reservation

bp = Blueprint('books', __name__)

# Helper for image uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# ---------------------------------------------------
# 1. CATALOG SEARCH
# ---------------------------------------------------
@bp.route('/search')
@login_required
def search():
    query = request.args.get('q')
    
    if query:
        books = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) | 
            (Book.author.ilike(f'%{query}%')) |
            (Book.isbn.ilike(f'%{query}%'))
        ).all()
    else:
        books = Book.query.all()
        
    return render_template('book_search.html', books=books, query=query)

# ---------------------------------------------------
# 2. BOOK DETAILS (The missing route!)
# ---------------------------------------------------
@bp.route('/<int:book_id>')
@login_required
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    
    # 1. Get Reviews
    reviews = Review.query.filter_by(book_id=book_id).order_by(Review.review_date.desc()).all()
    
    # 2. Calculate Expected Availability (if out of stock)
    expected_date = None
    if book.available_copies == 0:
        next_return = db.session.query(func.min(BorrowedBooks.due_date))\
            .join(BookCopy)\
            .filter(BookCopy.book_id == book_id, BorrowedBooks.return_date == None)\
            .scalar()
        if next_return:
            expected_date = next_return

    # 3. --- NEW: AI RECOMMENDATIONS ---
    # Logic: Find books with the same Genre, excluding the current book.
    # We prioritize books that are currently AVAILABLE (>0 copies).
    recommendations = Book.query.filter(
        Book.genre == book.genre,       # Same Genre
        Book.book_id != book.book_id,   # Not the same book
        Book.available_copies > 0       # Must be available (Requirement)
    ).limit(3).all()
    
    # Fallback: If no available books in genre, just show any books in genre
    if not recommendations:
        recommendations = Book.query.filter(
            Book.genre == book.genre,
            Book.book_id != book.book_id
        ).limit(3).all()
    # ----------------------------------

    return render_template('book_details.html', 
                         book=book, 
                         reviews=reviews, 
                         expected_date=expected_date,
                         recommendations=recommendations) # <--- Pass to HTML

# ---------------------------------------------------
# 3. ADD BOOK (Admin Only)
# ---------------------------------------------------
@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if current_user.role != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('books.search'))

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        description = request.form.get('description')
        total_copies = int(request.form.get('total_copies'))
        
        # Image Upload Logic
        file = request.files.get('cover_image')
        filename = 'default.jpg'
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.root_path, 'static/cover_pages', filename)
            file.save(file_path)

        if Book.query.filter_by(isbn=isbn).first():
            flash('Book with this ISBN already exists.', 'warning')
            return redirect(url_for('books.add_book'))
        
        new_book = Book(
            title=title, 
            author=author, 
            isbn=isbn,
            description=description,
            total_copies=total_copies,
            available_copies=total_copies,
            cover_image=filename
        )
        
        db.session.add(new_book)
        db.session.flush()

        # Auto-create physical copies
        for _ in range(total_copies):
            db.session.add(BookCopy(book_id=new_book.book_id, status='available'))
            
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('books.search'))

    return render_template('add_book.html')

# ---------------------------------------------------
# 4. BORROW BOOK
# ---------------------------------------------------
@bp.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
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
        flash(f'You successfully borrowed "{book.title}". Due: {due_date.strftime("%Y-%m-%d")}', 'success')
    else:
        flash('Sorry, no copies are currently available.', 'danger')
        
    return redirect(url_for('books.search'))

# ---------------------------------------------------
# 5. RESERVE BOOK
# ---------------------------------------------------
@bp.route('/reserve/<int:book_id>', methods=['POST'])
@login_required
def reserve_book(book_id):
    book = Book.query.get_or_404(book_id)
    contact_phone = request.form.get('phone') or current_user.phone
    
    new_reservation = Reservation(
        user_id=current_user.user_id,
        book_id=book.book_id,
        status='pending'
    )
    
    if contact_phone:
        current_user.phone = contact_phone
        
    db.session.add(new_reservation)
    db.session.commit()
    
    flash(f'Reservation placed for "{book.title}".', 'success')
    return redirect(url_for('books.book_details', book_id=book_id))

# ---------------------------------------------------
# 6. ADD REVIEW
# ---------------------------------------------------
@bp.route('/review/<int:book_id>', methods=['POST'])
@login_required
def add_review(book_id):
    rating = request.form.get('rating')
    text = request.form.get('review_text')
    
    existing = Review.query.filter_by(user_id=current_user.user_id, book_id=book_id).first()
    if existing:
        flash('You have already reviewed this book.', 'warning')
        return redirect(url_for('books.book_details', book_id=book_id))
    
    new_review = Review(
        user_id=current_user.user_id,
        book_id=book_id,
        rating=int(rating),
        review_text=text
    )
    db.session.add(new_review)
    db.session.commit()
    flash('Review posted successfully!', 'success')
    return redirect(url_for('books.book_details', book_id=book_id))