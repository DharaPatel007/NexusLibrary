from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta, date

class LibraryItem(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    publication_date = models.DateField()

    class Meta:
        abstract = True

class EBook(LibraryItem):
    file_url = models.URLField()
    file_size = models.IntegerField()  # in MB

    def __str__(self):
        return self.title

class PrintedBook(LibraryItem):
    isbn = models.CharField(max_length=13)
    copies_available = models.IntegerField()

    def __str__(self):
        return self.title

class ResearchPaper(LibraryItem):
    doi = models.CharField(max_length=100)
    access_level = models.CharField(max_length=50)

    def __str__(self):
        return self.title

class Audiobook(LibraryItem):
    duration = models.DurationField()
    narrator = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=[
        ('Student', 'Student'),
        ('Researcher', 'Researcher'),
        ('Faculty', 'Faculty'),
        ('Guest', 'Guest'),
    ])

    class Meta:
        abstract = True

    def get_borrowing_duration(self):
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class StudentProfile(UserProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')

    def get_borrowing_duration(self):
        return 15  # days

class ResearcherProfile(UserProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='researcherprofile')

    def get_borrowing_duration(self):
        return 30  # days

class FacultyProfile(UserProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='facultyprofile')

    def get_borrowing_duration(self):
        return 20  # days

class GuestProfile(UserProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guestprofile')

    def get_borrowing_duration(self):
        return 7  # days

class BorrowingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    borrow_date = models.DateField(default=date.today)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def get_item(self):
        # Force recompute the GenericForeignKey
        if self.content_type and self.object_id:
            return self.content_type.get_object_for_this_type(id=self.object_id)
        return None

    def save(self, *args, **kwargs):
        if not self.due_date:
            user_type = "Unknown"
            for profile_model in [StudentProfile, ResearcherProfile, FacultyProfile, GuestProfile]:
                try:
                    profile = profile_model.objects.get(user=self.user)
                    user_type = profile.user_type
                    break
                except profile_model.DoesNotExist:
                    continue

            if user_type == "Unknown":
                profile = StudentProfile(user=self.user, user_type='Student')
                profile.save()
            else:
                profile = None
                for profile_model in [StudentProfile, ResearcherProfile, FacultyProfile, GuestProfile]:
                    try:
                        profile = profile_model.objects.get(user=self.user)
                        break
                    except profile_model.DoesNotExist:
                        continue

            duration = profile.get_borrowing_duration()
            self.due_date = self.borrow_date + timedelta(days=duration)

        super().save(*args, **kwargs)

    def __str__(self):
        item = self.get_item()
        return f"{self.user.username} borrowed {item.title if item else 'Unknown Item'}"
    
class BookReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    printed_book = models.ForeignKey(PrintedBook, on_delete=models.CASCADE)
    reservation_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'printed_book', 'is_active')

    def __str__(self):
        return f"Reservation for {self.printed_book.title} by {self.user.username}"# Added models 
