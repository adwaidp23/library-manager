from app import create_app
from extensions import db, bcrypt
from models import User, Book, BookCopy, BorrowedBooks, Review, Feedback, Reservation
from datetime import datetime, timedelta

app = create_app()

def seed_database():
    with app.app_context():
        print("🌱 Clearing old data...")
        db.drop_all()
        db.create_all()

        print("👤 Creating Users...")
        # 1. Admin User
        admin_pass = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(name='Super Admin', email='admin@library.com', 
                     password_hash=admin_pass, role='admin', phone=9876543210, library_id='LIB-ADM-01')
        
        # 2. Member: John Doe (Has borrowed books - Cannot be deleted)
        user1_pass = bcrypt.generate_password_hash('password').decode('utf-8')
        user1 = User(name='John Doe', email='john@gmail.com', 
                     password_hash=user1_pass, role='member', phone=1234567890, library_id='LIB-USR-01')
        
        # 3. Member: Jane Smith (Has OVERDUE books - Cannot be deleted)
        user2_pass = bcrypt.generate_password_hash('password').decode('utf-8')
        user2 = User(name='Jane Smith', email='jane@gmail.com', 
                     password_hash=user2_pass, role='member', phone=1122334455, library_id='LIB-USR-02')

        # 4. NEW: Member: Bob (No books - SAFE TO DELETE)
        user3_pass = bcrypt.generate_password_hash('password').decode('utf-8')
        user3 = User(name='Bob NoBooks', email='bob@gmail.com', 
                     password_hash=user3_pass, role='member', phone=5555555555, library_id='LIB-USR-03')

        db.session.add_all([admin, user1, user2, user3])
        db.session.commit()

        print("📚 Creating Books...")
        # Book 1: Sci-Fi (Available)
        b1 = Book(title='Dune', author='Frank Herbert', isbn='9780441013593', 
                  genre='Sci-Fi', total_copies=3, available_copies=2,
                  description='A mythic and emotionally charged hero’s journey.',
                  cover_image='default.jpg')
        
        # Book 2: Sci-Fi (Recommendation for Dune)
        b2 = Book(title='Ender\'s Game', author='Orson Scott Card', isbn='9780812550702', 
                  genre='Sci-Fi', total_copies=2, available_copies=2,
                  description='The war with the Buggers has been raging for a hundred years.',
                  cover_image='default.jpg')

        # Book 3: Tech (OUT OF STOCK - For Reservation)
        b3 = Book(title='The Pragmatic Programmer', author='Andrew Hunt', isbn='9780201616224', 
                  genre='Tech', total_copies=1, available_copies=0, 
                  description='From journeyman to master.',
                  cover_image='default.jpg')

        db.session.add_all([b1, b2, b3])
        db.session.commit()

        print("📦 Stocking Shelves...")
        # Copies
        c1_1 = BookCopy(book_id=b1.book_id, status='borrowed')
        c1_2 = BookCopy(book_id=b1.book_id, status='available')
        c1_3 = BookCopy(book_id=b1.book_id, status='available')
        c2_1 = BookCopy(book_id=b2.book_id, status='available')
        c2_2 = BookCopy(book_id=b2.book_id, status='available')
        c3_1 = BookCopy(book_id=b3.book_id, status='borrowed')

        db.session.add_all([c1_1, c1_2, c1_3, c2_1, c2_2, c3_1])
        db.session.commit()

        print("📖 Creating Loan History...")
        # John borrows Dune (Active)
        loan1 = BorrowedBooks(user_id=user1.user_id, copy_id=c1_1.copy_id,
                              borrow_date=datetime.utcnow() - timedelta(days=2),
                              due_date=datetime.utcnow() + timedelta(days=12))

        # Jane borrows Pragmatic Programmer (OVERDUE)
        loan2 = BorrowedBooks(user_id=user2.user_id, copy_id=c3_1.copy_id,
                              borrow_date=datetime.utcnow() - timedelta(days=20),
                              due_date=datetime.utcnow() - timedelta(days=6))

        db.session.add_all([loan1, loan2])
        db.session.commit()

        print("⭐ Adding Reviews & Feedback...")
        rev1 = Review(user_id=user1.user_id, book_id=b1.book_id, rating=5, 
                      review_text="Absolute masterpiece. The spice must flow!")
        
        fb1 = Feedback(user_id=user2.user_id, subject='Bug Report', 
                       message='I cannot reset my password. Please help.')

        db.session.add_all([rev1, fb1])
        db.session.commit()

        print("✅ Database Seeded Successfully!")
        print("   - Admin: admin@library.com / admin123")
        print("   - Member (Has Loans): john@gmail.com / password")
        print("   - Member (Deletable): bob@gmail.com / password")

if __name__ == '__main__':
    seed_database()