from app import create_app
from extensions import db
from models import Book, BookCopy

app = create_app()

# We need the app context to access the database
with app.app_context():
    print("Checking library inventory...")
    books = Book.query.all()
    fixed_count = 0

    for book in books:
        # Check how many actual physical copies exist in the database
        actual_copies = BookCopy.query.filter_by(book_id=book.book_id).count()
        
        # Calculate how many are missing compared to what the Book says
        missing_copies = book.total_copies - actual_copies
        
        if missing_copies > 0:
            print(f"  -> Found mismatch! Restocking {missing_copies} copies for '{book.title}'...")
            for _ in range(missing_copies):
                # Create the missing physical copy
                new_copy = BookCopy(book_id=book.book_id, status='available')
                db.session.add(new_copy)
            fixed_count += 1
    
    if fixed_count > 0:
        db.session.commit()
        print("Success! All missing copies have been added to the shelves.")
    else:
        print("Inventory is already perfect. No changes needed.")