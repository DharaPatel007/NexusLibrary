from django.contrib.contenttypes.models import ContentType
from library.models import (
    BorrowingHistory, EBook, PrintedBook, Audiobook, ResearchPaper,
    StudentProfile, ResearcherProfile, FacultyProfile, GuestProfile,
    BookReservation
)
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta

class LibraryService:
    def get_user_borrowing_limit(self, user):
        user_type = "Unknown"
        for profile_model in [StudentProfile, ResearcherProfile, FacultyProfile, GuestProfile]:
            try:
                profile = profile_model.objects.get(user=user)
                user_type = profile.user_type
                break
            except profile_model.DoesNotExist:
                continue
        borrowing_limits = {
            'Student': 2,
            'Faculty': 5,
            'Researcher': 5,
            'Guest': 0,
        }
        return borrowing_limits.get(user_type, 0)

    def get_user_type(self, user):
        for profile_model in [StudentProfile, ResearcherProfile, FacultyProfile, GuestProfile]:
            try:
                profile = profile_model.objects.get(user=user)
                return profile.user_type
            except profile_model.DoesNotExist:
                continue
        return "Unknown"

    def can_user_borrow(self, user):
        if not user.is_authenticated:
            return False
        active_borrowings = BorrowingHistory.objects.filter(user=user, return_date__isnull=True).count()
        borrowing_limit = self.get_user_borrowing_limit(user)
        return active_borrowings < borrowing_limit

    def borrow_item(self, user, item):
        if not self.can_user_borrow(user):
            return False, "Borrowing limit reached or user not allowed to borrow."
        
        content_type = ContentType.objects.get_for_model(item)
        if BorrowingHistory.objects.filter(
            user=user,
            content_type=content_type,
            object_id=item.id,
            return_date__isnull=True
        ).exists():
            return False, "Item already borrowed by this user."

        if isinstance(item, PrintedBook):
            if item.copies_available <= 0:
                return False, "No copies available."
            item.copies_available -= 1
            item.save()

        BorrowingHistory.objects.create(
            user=user,
            content_type=content_type,
            object_id=item.id,
        )
        return True, "Item borrowed successfully."

    def return_item(self, user, item, return_date=None):
        content_type = ContentType.objects.get_for_model(item)
        try:
            borrowing = BorrowingHistory.objects.get(
                user=user,
                content_type=content_type,
                object_id=item.id,
                return_date__isnull=True
            )
        except BorrowingHistory.DoesNotExist:
            return False, "Borrowing record not found."

        if return_date is None:
            return_date = datetime.now().date()
        borrowing.return_date = return_date
        borrowing.fine = self.calculate_fine(borrowing, return_date)
        borrowing.save()

        if isinstance(item, PrintedBook):
            item.copies_available += 1
            item.save()
            # Check for reservations and notify users if any
            self.notify_reservation_users(item)

        return True, "Item returned successfully."

    def calculate_fine(self, borrowing, return_date):
        item = borrowing.get_item()
        print(f"Item Type: {item.__class__.__name__ if item else 'Unknown'}")
        if not item or not isinstance(item, (PrintedBook, ResearchPaper)):
            print("No fine: Item is not a PrintedBook or ResearchPaper.")
            return 0.00
        due_date = borrowing.due_date
        if return_date > due_date:
            days_overdue = (return_date - due_date).days
            fine_per_day = 1.00
            fine = days_overdue * fine_per_day
            return fine
        return 0.00

    def reserve_book(self, user, printed_book):
        if not user.is_authenticated:
            return False, "User must be authenticated to reserve a book."
        
        if printed_book.copies_available > 0:
            return False, "Cannot reserve: Copies are available for borrowing."
        
        # Check if user already has an active reservation for this book
        if BookReservation.objects.filter(user=user, printed_book=printed_book, is_active=True).exists():
            return False, "You already have an active reservation for this book."
        
        # Create a new reservation
        BookReservation.objects.create(user=user, printed_book=printed_book)
        return True, "Book reserved successfully. You will be notified when a copy is available."

    def notify_reservation_users(self, printed_book):
        reservations = BookReservation.objects.filter(
            printed_book=printed_book,
            is_active=True,
            notified=False
        ).order_by('reservation_date')  
        
        if reservations.exists() and printed_book.copies_available > 0:
            reservation = reservations.first()
            user = reservation.user
            try:
                send_mail(
                    subject=f"Book Available: {printed_book.title}",
                    message=f"Dear {user.username},\n\nThe book '{printed_book.title}' is now available for borrowing at Nexus Library. Please visit the library to borrow it within 3 days, or your reservation will be canceled.\n\nBest regards,\nNexus Library Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                reservation.notified = True
                reservation.save()
               
            except Exception as e:
                print(f"Failed to send email to {user.email}: {e}")

class BookExplorerService(LibraryService):
    def __init__(self):
        super().__init__()
        self.book_models = [EBook, PrintedBook, Audiobook]  

    def get_all_genres(self):
        genres = set()
        for model in self.book_models:
            model_genres = model.objects.values_list('genre', flat=True).distinct()
            print(f"Genres for {model.__name__}: {list(model_genres)}")
            genres.update(model_genres)
        genres.add("Research Papers")
        print(f"All genres: {genres}")
        return sorted(list(genres))

    def get_books_by_genre(self, genre, user=None):
        if genre == "Research Papers":
            papers = ResearchPaper.objects.all()
            print(f"Research Papers: {list(papers.values('id', 'title', 'genre'))}")
            return list(papers)

        books = []
        borrowed_ids = set()

        if user:
            user_borrowings = BorrowingHistory.objects.filter(user=user)
            for borrowing in user_borrowings:
                if borrowing.content_type.model in [m.__name__.lower() for m in self.book_models]:
                    borrowed_ids.add(borrowing.object_id)
            print(f"Borrowed IDs for user {user.username}: {borrowed_ids}")

        # Fetch books from each model that match the genre
        for model in self.book_models:
            # Use case-insensitive matching for genre
            query = model.objects.filter(genre__iexact=genre)
            print(f"Books in {model.__name__} for genre '{genre}' (before exclusion): {list(query.values('id', 'title', 'genre'))}")
            if borrowed_ids:
                query = query.exclude(id__in=borrowed_ids)
            books.extend(query)
            print(f"Books in {model.__name__} for genre '{genre}' (after exclusion): {list(query.values('id', 'title', 'genre'))}")

        print(f"Total books found for genre '{genre}': {len(books)}")
        return books