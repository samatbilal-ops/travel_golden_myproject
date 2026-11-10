from .models import Tour


def wishlist(request):
    """Таңдаулыларға қосылған турлардың slug тізімі (♥ күйін көрсету үшін)."""
    ids = request.session.get('wishlist', []) if hasattr(request, 'session') else []
    slugs = list(Tour.objects.filter(pk__in=ids).values_list('slug', flat=True)) if ids else []
    return {'wishlist_slugs': slugs}
