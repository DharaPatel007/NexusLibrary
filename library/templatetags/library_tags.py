from django import template
from django.contrib.contenttypes.models import ContentType
from library.models import BorrowingHistory, PrintedBook

register = template.Library()

@register.filter
def get_item_type(item):
    return item.__class__.__name__.lower()

@register.filter
def get_item_type_capitalized(item):
    return item.__class__.__name__

@register.filter
def is_book(item):
    return item.__class__.__name__ in ['EBook', 'PrintedBook', 'Audiobook']

@register.filter
def is_research_paper(item):
    return item.__class__.__name__ == 'ResearchPaper'

@register.filter
def get_item_status(item, user):
    print(f"Debugging get_item_status for item: {item.title} (ID: {item.id}, Type: {item.__class__.__name__}), User: {user.username if user.is_authenticated else 'Anonymous'}")

    try:
        item = item.__class__.objects.get(id=item.id)
        print(f"Refreshed item: {item.title} (ID: {item.id}), Type: {item.__class__.__name__}")
    except item.__class__.DoesNotExist:
        return "Unavailable"

    if not user.is_authenticated:
        return "Unavailable"
    
    content_type = ContentType.objects.get_for_model(item)
    borrowed = BorrowingHistory.objects.filter(
        user=user,
        content_type=content_type,
        object_id=item.id,
        return_date__isnull=True
    ).exists()
    print(f"Borrowed by user: {borrowed}")

    if borrowed:
        return "Borrowed"
    
    item_type = item.__class__.__name__
    if item_type == 'PrintedBook':
        print(f"Item is a PrintedBook. Copies available: {item.copies_available}")
        if item.copies_available <= 0:
            return "Unavailable"
        return "Available"
    elif item_type in ['EBook', 'Audiobook']:
        return "Available"
    
    return "Available"