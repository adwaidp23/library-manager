from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import User, Book, BorrowedBooks, Feedback

bp = Blueprint('admin', __name__)

# ==========================================
# 1. ADMIN DASHBOARD (Stats, Loans, Feedback)
# ==========================================
@bp.route('/dashboard')
@login_required
def dashboard():
    # Security Check
    if current_user.role != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('books.search'))
    
    # A. Gather Quick Stats
    total_users = User.query.count()
    total_books = Book.query.count()
    
    # B. Fetch Active Loans (Where return_date is None)
    active_loans = BorrowedBooks.query.filter_by(return_date=None).all()
    active_loans_count = len(active_loans)
    
    # C. Fetch Feedback (Newest first)
    all_feedback = Feedback.query.order_by(Feedback.date.desc()).all()
    
    # Pass 'now' to template to calculate Overdue status
    return render_template('admin_dashboard.html', 
                         users_count=total_users,
                         books_count=total_books,
                         loans_count=active_loans_count,
                         loans=active_loans,
                         feedbacks=all_feedback,
                         now=datetime.utcnow().date())

# ==========================================
# 2. USER MANAGEMENT (List, Promote, Delete)
# ==========================================
@bp.route('/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('books.search'))
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@bp.route('/user/promote/<int:user_id>')
@login_required
def promote_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('books.search'))
    
    user = User.query.get_or_404(user_id)
    
    # Toggle Role
    if user.role == 'member':
        user.role = 'admin'
        flash(f'{user.name} promoted to Admin.', 'success')
    else:
        user.role = 'member'
        flash(f'{user.name} demoted to Member.', 'info')
        
    db.session.commit()
    return redirect(url_for('admin.manage_users'))

@bp.route('/user/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('books.search'))
    
    user = User.query.get_or_404(user_id)
    
    # Safety Check 1: Cannot delete self
    if user.user_id == current_user.user_id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for('admin.manage_users'))
        
    # Safety Check 2: Cannot delete if they have unreturned books
    active_loans = BorrowedBooks.query.filter_by(user_id=user.user_id, return_date=None).count()
    if active_loans > 0:
        flash(f"Cannot delete {user.name}. They must return {active_loans} books first.", "warning")
        return redirect(url_for('admin.manage_users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.name} deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))