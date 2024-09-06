from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from .models import EBook, PrintedBook, ResearchPaper, Audiobook, BorrowingHistory
from .models import StudentProfile, ResearcherProfile, FacultyProfile, GuestProfile
from .services import LibraryService, BookExplorerService
from .forms import CustomSignupForm
from django.utils import timezone
from datetime import timedelta

service = LibraryService()
book_explorer_service = BookExplorerService()

def signup(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = CustomSignupForm()
    return render(request, 'library/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'library/login.html')

@login_required
def user_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect('login')
    return redirect('home')

@login_required
def home(request):
    user = request.user
    user_type = service.get_user_type(user)
    print(f"User: {user.username}, User Type: {user_type}")

    # Recommendations: Based on user's borrowing history (genres they've borrowed) or user type
    book_models = [EBook, PrintedBook, Audiobook]  # Exclude ResearchPaper
    recommendations = []

    user_borrowings = BorrowingHistory.objects.filter(user=user)
    user_genres = set()
    for borrowing in user_borrowings:
        item = borrowing.get_item()
        if item and hasattr(item, 'genre'):
            user_genres.add(item.genre)

    if user_genres:
        for model in book_models:
            items = model.objects.filter(genre__in=user_genres).exclude(
                id__in=[b.object_id for b in user_borrowings if b.content_type.model == model.__name__.lower()]
            )[:5]  
            for item in items:
                print(f"Recommendation: {item.title} (ID: {item.id}), Genre: {item.genre}, Type: {item.__class__.__name__}")
            recommendations.extend(items)
    else:
        genre_preferences = {
            'Student': ['Fiction', 'Technology', 'Science'],
            'Faculty': ['Non-Fiction', "History", 'Science'],
            'Researcher': ['Science', 'Technology'],
            'Guest': ['Fiction', 'History'],
        }
        preferred_genres = genre_preferences.get(user_type, ['Fiction', 'Technology'])
        for model in book_models:
            items = model.objects.filter(genre__in=preferred_genres)[:5]  
            for item in items:
                print(f"Recommendation (Fallback): {item.title} (ID: {item.id}), Genre: {item.genre}, Type: {item.__class__.__name__}")
            recommendations.extend(items)

    import random
    recommendations = recommendations[:10] 
    random.shuffle(recommendations)
    recommendations = recommendations[:5]

    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    trending_borrowings = BorrowingHistory.objects.filter(borrow_date__gte=thirty_days_ago)
    book_counts = {}
    for borrowing in trending_borrowings:
        item = borrowing.get_item()
        if item and item.__class__ in book_models:  
            item_key = (item.__class__.__name__, item.id)
            book_counts[item_key] = book_counts.get(item_key, 0) + 1

    trending_items = sorted(
        book_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]  
    trending = []
    for (item_type, item_id), count in trending_items:
        model = next(m for m in book_models if m.__name__ == item_type)
        try:
            item = model.objects.get(id=item_id)
            print(f"Trending: {item.title} (ID: {item.id}), Borrow Count: {count}, Type: {item_type}")
            trending.append(item)
        except model.DoesNotExist:
            continue

    if not trending:
        all_borrowings = BorrowingHistory.objects.all()
        book_counts = {}
        for borrowing in all_borrowings:
            item = borrowing.get_item()
            if item and item.__class__ in book_models:
                item_key = (item.__class__.__name__, item.id)
                book_counts[item_key] = book_counts.get(item_key, 0) + 1
        trending_items = sorted(
            book_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for (item_type, item_id), count in trending_items:
            model = next(m for m in book_models if m.__name__ == item_type)
            try:
                item = model.objects.get(id=item_id)
                print(f"Trending (Fallback): {item.title} (ID: {item.id}), Borrow Count: {count}, Type: {item_type}")
                trending.append(item)
            except model.DoesNotExist:
                continue

    research_papers = ResearchPaper.objects.all()[:5]  
    for paper in research_papers:
        print(f"Research Paper: {paper.title} (ID: {paper.id}), Access Level: {paper.access_level}")

    all_borrowings = BorrowingHistory.objects.all()
    book_counts = {}
    for borrowing in all_borrowings:
        item = borrowing.get_item()
        if item:
            title = item.title
            book_counts[title] = book_counts.get(title, 0) + 1
    most_borrowed = sorted(
        [{'title': title, 'total': count} for title, count in book_counts.items()],
        key=lambda x: x['total'],
        reverse=True
    )[:5]

    # Popular Genres (for Analytics section)
    genre_counts = {}
    for borrowing in all_borrowings:
        item = borrowing.get_item()
        if item:
            genre = item.genre
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    popular_genres = sorted(
        [{'genre': genre, 'total': count} for genre, count in genre_counts.items()],
        key=lambda x: x['total'],
        reverse=True
    )[:5]

    return render(request, 'library/home.html', {
        'recommendations': recommendations,
        'trending': trending,
        'research_papers': research_papers,
        'most_borrowed': most_borrowed,
        'popular_genres': popular_genres,
        'user_type': user_type,
    })

@login_required
def profile(request):
    user_type = service.get_user_type(request.user)
    return render(request, 'library/profile.html', {
        'user_type': user_type,
    })

@login_required
def history(request):
    borrowing_history = BorrowingHistory.objects.filter(user=request.user)
    return render(request, 'library/history.html', {
        'borrowing_history': borrowing_history,
    })

@login_required
def search_items(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'keyword')
    results = []

    user_type = service.get_user_type(request.user)
    print(f"User: {request.user.username}, User Type: {user_type}")

    if query:
        models = [EBook, PrintedBook, Audiobook]
        if user_type != 'Guest':
            models.append(ResearchPaper)
        for model in models:
            items = model.objects.all()
            if search_type == 'keyword':
                items = items.filter(
                    Q(title__icontains=query) |
                    Q(author__icontains=query) |
                    Q(genre__icontains=query)
                )
            elif search_type == 'genre':
                items = items.filter(genre__icontains=query)
            elif search_type == 'author':
                items = items.filter(author__icontains=query)
            results.extend(items)

    return render(request, 'library/search_results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'user_type': user_type,
    })

@login_required
def explore(request):
    user = request.user
    user_type = service.get_user_type(user)
    print(f"User: {user.username}, User Type: {user_type}")

    genres = book_explorer_service.get_all_genres()

    selected_genre = request.GET.get('genre', None)
    books = []
    if selected_genre:
        books = book_explorer_service.get_books_by_genre(selected_genre, user)
        print(f"Explore - Genre: {selected_genre}, Found {len(books)} books")

    return render(request, 'library/explore.html', {
        'genres': genres,
        'selected_genre': selected_genre,
        'books': books,
        'user_type': user_type,
    })

@login_required
@require_POST
def borrow_item(request, item_type, item_id):
    user_type = service.get_user_type(request.user)

    if user_type == 'Guest':
        messages.error(request, "Guests are not allowed to borrow items.")
        return redirect('home')

    item = None
    model_map = {
        'ebook': EBook,
        'printedbook': PrintedBook,
        'audiobook': Audiobook,
    }
    model = model_map.get(item_type)
    if model:
        try:
            item = model.objects.get(id=item_id)
            print(f"Attempting to borrow item: {item.title} (ID: {item_id}, Type: {item_type})")
        except model.DoesNotExist:
            messages.error(request, "Item not found.")
            return redirect('home')
    else:
        messages.error(request, "Invalid item type.")
        return redirect('home')

    try:
        success, message = service.borrow_item(request.user, item)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    except ValueError as e:
        messages.error(request, str(e))
    genre = request.GET.get('genre', '')
    return redirect('explore' + (f'?genre={genre}' if genre else ''))

@login_required
def request_item(request, item_id):
    user_type = service.get_user_type(request.user)
    print(f"User: {request.user.username}, User Type: {user_type}")

    if user_type not in ['Faculty', 'Researcher']:
        messages.error(request, f"As a {user_type}, you cannot access research papers.")
        return redirect('home')

    item = ResearchPaper.objects.filter(id=item_id).first()
    if not item:
        messages.error(request, "Research paper not found.")
        return redirect('home')
    messages.success(request, f"Access request for '{item.title}' has been submitted.")
    return redirect('home')

@login_required
@require_POST
def return_item(request, item_type, item_id):
    item = None
    model_map = {
        'ebook': EBook,
        'printedbook': PrintedBook,
        'audiobook': Audiobook,
    }
    model = model_map.get(item_type)
    if model:
        try:
            item = model.objects.get(id=item_id)
            print(f"Attempting to return item: {item.title} (ID: {item_id}, Type: {item_type})")
        except model.DoesNotExist:
            messages.error(request, "Item not found.")
            return redirect('history')
    else:
        messages.error(request, "Invalid item type.")
        return redirect('history')

    try:
        success, message = service.return_item(request.user, item)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('history')

@login_required
def reserve_book(request, item_id):
    user = request.user
    printed_book = get_object_or_404(PrintedBook, id=item_id)

    if request.method == 'POST':
        success, message = service.reserve_book(user, printed_book)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        genre = request.GET.get('genre', '')
        return redirect('explore' + (f'?genre={genre}' if genre else ''))

    return redirect('home')