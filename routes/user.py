from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import BorrowedBooks, BookCopy, Book

# Make sure this matches the variable name you import in app.py
bp = Blueprint('user', __name__)

@bp.route('/profile')
@login_required
def profile():
    # Fetch active loans (where return_date is empty)
    active_loans = BorrowedBooks.query.filter_by(
        user_id=current_user.user_id, 
        return_date=None
    ).all()
    
    return render_template('user_profile.html', loans=active_loans, now=datetime.utcnow().date())

@bp.route('/return/<int:borrow_id>')
@login_required
def return_book(borrow_id):
    loan = BorrowedBooks.query.get_or_404(borrow_id)
    
    # Security check
    if loan.user_id != current_user.user_id:
        flash("You are not authorized to return this book.", "danger")
        return redirect(url_for('user.profile'))
    
    # Logic: Mark returned, free up the copy, increase book count
    loan.return_date = datetime.utcnow()
    
    copy = BookCopy.query.get(loan.copy_id)
    copy.status = 'available'
    
    book = Book.query.get(copy.book_id)
    book.available_copies += 1
    
    db.session.commit()
    
    flash(f"Successfully returned '{book.title}'.", "success")
    return redirect(url_for('user.profile'))