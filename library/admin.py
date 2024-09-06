from django.contrib import admin
from .models import EBook, PrintedBook, ResearchPaper, Audiobook, BorrowingHistory, StudentProfile, ResearcherProfile, FacultyProfile, GuestProfile

@admin.register(EBook)
class EBookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'publication_date', 'file_url', 'file_size')
    search_fields = ('title', 'author', 'genre')
    list_filter = ('genre', 'publication_date')

@admin.register(PrintedBook)
class PrintedBookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'publication_date', 'isbn', 'copies_available')
    search_fields = ('title', 'author', 'genre', 'isbn')
    list_filter = ('genre', 'publication_date')

@admin.register(ResearchPaper)
class ResearchPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'publication_date', 'doi', 'access_level')
    search_fields = ('title', 'author', 'genre', 'doi')
    list_filter = ('genre', 'publication_date', 'access_level')

@admin.register(Audiobook)
class AudiobookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'publication_date', 'duration', 'narrator')
    search_fields = ('title', 'author', 'genre', 'narrator')
    list_filter = ('genre', 'publication_date')

@admin.register(BorrowingHistory)
class BorrowingHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_title', 'borrow_date', 'due_date', 'return_date', 'fine')
    search_fields = ('user__username',)
    list_filter = ('borrow_date', 'due_date', 'return_date')

    def item_title(self, obj):
        return obj.item.title if obj.item else "N/A"
    item_title.short_description = "Item Title"

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type')
    search_fields = ('user__username',)

@admin.register(ResearcherProfile)
class ResearcherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type')
    search_fields = ('user__username',)

@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type')
    search_fields = ('user__username',)

@admin.register(GuestProfile)
class GuestProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type')
    search_fields = ('user__username',)