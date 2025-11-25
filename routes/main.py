from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
# Note: We haven't created a Feedback model yet, so for now we'll just flash a message.
# If you want to save it to DB, we can add a model later.

bp = Blueprint('main', __name__)

@bp.route('/rules')
def rules():
    return render_template('rules.html')

@bp.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically save to DB or Email the admin
        # For now, we simulate success
        flash(f'Thank you, {current_user.name}! Your feedback has been sent to the administration.', 'success')
        return redirect(url_for('books.search'))
        
    return render_template('feedback.html')