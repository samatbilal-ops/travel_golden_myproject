import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Tour, Category, Booking, Review, TourMeta
from .forms import RegisterForm, LoginForm, BookingForm, TourAddForm, ReviewForm, ContactForm


# ══════════════════════════════════════════════════════
# Тіркелу
# ══════════════════════════════════════════════════════
def register_view(request):
    if request.user.is_authenticated:
        return redirect('travel_app:tours')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f"Қош келдіңіз, {user.first_name or user.username}!")
                return redirect('travel_app:tours')
            except IntegrityError:
                messages.error(request, "Бұл пайдаланушы аты бұрыннан бар. Басқа ат таңдаңыз.")
        else:
            messages.error(request, "Форманы дұрыс толтырыңыз.")
    else:
        form = RegisterForm()
    return render(request, 'travel_app/register.html', {'form': form})


# ══════════════════════════════════════════════════════
# Кіру
# ══════════════════════════════════════════════════════
def login_view(request):
    if request.user.is_authenticated:
        return redirect('travel_app:index')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Қош келдіңіз, {user.first_name or user.username}!")
            next_url = request.POST.get('next') or request.GET.get('next') or ''
            if next_url and url_has_allowed_host_and_scheme(
                    next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('travel_app:index')
        else:
            messages.error(request, "Логин немесе құпия сөз қате.")
    else:
        form = LoginForm()
    return render(request, 'travel_app/login.html', {'form': form})


# ══════════════════════════════════════════════════════
# Шығу
# ══════════════════════════════════════════════════════
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Жүйеден шықтыңыз.")
    return redirect('travel_app:login')


# ══════════════════════════════════════════════════════
# Басты бет
# ══════════════════════════════════════════════════════
def index_view(request):
    featured_tours = Tour.objects.filter(is_featured=True).select_related('category', 'author').order_by('-created_at')[:6]
    if not featured_tours:
        featured_tours = Tour.objects.all().select_related('category', 'author').order_by('-created_at')[:6]
    categories = Category.objects.all()
    total_tours = Tour.objects.count()
    total_bookings = Booking.objects.count()
    return render(request, 'travel_app/index.html', {
        'tours': featured_tours,
        'categories': categories,
        'total_tours': total_tours,
        'total_bookings': total_bookings,
    })


# ══════════════════════════════════════════════════════
# Турлар тізімі
# ══════════════════════════════════════════════════════
def tours_view(request):
    tours_qs = Tour.objects.select_related('category', 'author').all()

    search_query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '-created_at')

    if search_query:
        tours_qs = tours_qs.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    if selected_category:
        tours_qs = tours_qs.filter(category__slug=selected_category)

    sort_options = {
        '-created_at': 'Жаңасы бірінші',
        'price':       'Бағасы (өсу)',
        '-price':      'Бағасы (кему)',
        'duration':    'Ұзақтығы',
        'title':       'Атауы (А-Я)',
    }
    if sort_by in sort_options:
        tours_qs = tours_qs.order_by(sort_by)

    paginator = Paginator(tours_qs, 6)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    qs_params = request.GET.copy()
    qs_params.pop('page', None)
    categories = Category.objects.all()
    return render(request, 'travel_app/tours.html', {
        'querystring': qs_params.urlencode(),
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
        'sort_by': sort_by,
        'sort_options': sort_options,
    })


# ══════════════════════════════════════════════════════
# Тур толық беті
# ══════════════════════════════════════════════════════
def tour_detail_view(request, slug):
    tour = get_object_or_404(Tour, slug=slug)
    meta, _ = TourMeta.objects.get_or_create(tour=tour)
    if request.method == 'GET':
        TourMeta.objects.filter(pk=meta.pk).update(views_count=F('views_count') + 1)
        meta.refresh_from_db()

    reviews = Review.objects.filter(tour=tour).select_related('user')
    related_tours = Tour.objects.filter(category=tour.category).exclude(pk=tour.pk)[:3]
    review_form = ReviewForm()

    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.tour = tour
            review.user = request.user
            review.save()
            messages.success(request, "Пікіріңіз қосылды!")
            return redirect('travel_app:tour_detail', slug=slug)

    return render(request, 'travel_app/tour_detail.html', {
        'tour': tour,
        'meta': meta,
        'reviews': reviews,
        'review_form': review_form,
        'related_tours': related_tours,
        'avg_rating': tour.average_rating(),
        'detail_rows': [],
    })


# ══════════════════════════════════════════════════════
# Брондау
# ══════════════════════════════════════════════════════
@login_required
def book_tour_view(request, slug):
    tour = get_object_or_404(Tour, slug=slug)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.tour = tour
            booking.total_price = tour.price * booking.num_people
            booking.save()
            messages.success(request, f"«{tour.title}» туры сәтті бронданды!")
            return redirect('travel_app:profile')
    else:
        form = BookingForm()
    return render(request, 'travel_app/book_tour.html', {'form': form, 'tour': tour})


# ══════════════════════════════════════════════════════
# Тур қосу
# ══════════════════════════════════════════════════════
@login_required
def add_tour_view(request):
    if not request.user.is_staff:
        messages.error(request, "Тур қосу тек әкімші арқылы мүмкін.")
        return redirect('travel_app:tours')
    if request.method == 'POST':
        form = TourAddForm(request.POST, request.FILES)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.author = request.user
            tour.save()  # slug Tour.save() ішінде автоматты жасалады
            TourMeta.objects.get_or_create(tour=tour)
            messages.success(request, f"«{tour.title}» туры қосылды!")
            return redirect('travel_app:tour_detail', slug=tour.slug)
    else:
        form = TourAddForm()
    return render(request, 'travel_app/add_tour.html', {'form': form})


# ══════════════════════════════════════════════════════
# Тур өңдеу
# ══════════════════════════════════════════════════════
@login_required
def update_tour_view(request, slug):
    tour = get_object_or_404(Tour, slug=slug)
    if not request.user.is_staff:
        messages.error(request, "Рұқсатыңыз жоқ.")
        return redirect('travel_app:tour_detail', slug=slug)
    if request.method == 'POST':
        form = TourAddForm(request.POST, request.FILES, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, "Тур жаңартылды!")
            return redirect('travel_app:tour_detail', slug=tour.slug)
    else:
        form = TourAddForm(instance=tour)
    return render(request, 'travel_app/add_tour.html', {'form': form, 'tour': tour, 'is_edit': True})


# ══════════════════════════════════════════════════════
# Тур жою
# ══════════════════════════════════════════════════════
@login_required
def delete_tour_view(request, slug):
    tour = get_object_or_404(Tour, slug=slug)
    if not request.user.is_staff:
        messages.error(request, "Рұқсатыңыз жоқ.")
        return redirect('travel_app:tour_detail', slug=slug)
    if request.method == 'POST':
        try:
            tour.delete()
        except ProtectedError:
            messages.error(request, "Бұл турға брондаулар бар, сондықтан жоюға болмайды.")
            return redirect('travel_app:tour_detail', slug=slug)
        messages.success(request, "Тур жойылды.")
        return redirect('travel_app:tours')
    return render(request, 'travel_app/delete_tour.html', {'tour': tour})


# ══════════════════════════════════════════════════════
# Профиль
# ══════════════════════════════════════════════════════
@login_required
def profile_view(request):
    bookings_qs = Booking.objects.filter(user=request.user).select_related('tour').order_by('-booking_date')
    paginator = Paginator(bookings_qs, 5)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    return render(request, 'travel_app/profile.html', {'page_obj': page_obj})


# ══════════════════════════════════════════════════════
# Елдер (RestCountries API)
# ══════════════════════════════════════════════════════
def countries_api_view(request):
    REGIONS = ['asia', 'europe', 'africa', 'americas', 'oceania']
    region = request.GET.get('region', 'asia')
    if region not in REGIONS:
        region = 'asia'
    cache_key = f'countries_{region}'
    countries = cache.get(cache_key)
    error_msg = None

    if countries is None:
        countries = []
        try:
            resp = requests.get(
                f'https://restcountries.com/v3.1/region/{region}',
                params={'fields': 'name,capital,population,flags,languages,area'},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            # API қате жағдайда тізімнің орнына {"status":..., "message":...} қайтаруы мүмкін
            if not isinstance(data, list):
                raise ValueError('Күтпеген API жауабы')
            for c in data[:24]:
                if not isinstance(c, dict):
                    continue
                capital = c.get('capital') or ['—']
                countries.append({
                    'name':       (c.get('name') or {}).get('common', '—'),
                    'capital':    capital[0] if capital else '—',
                    'population': f"{c.get('population') or 0:,}",
                    'flag':       (c.get('flags') or {}).get('png', ''),
                    'languages':  ', '.join((c.get('languages') or {}).values()) or '—',
                    'area':       f"{c.get('area') or 0:,.0f} км²",
                })
            countries.sort(key=lambda x: x['name'])
            if countries:
                cache.set(cache_key, countries, 60 * 60)   # 1 сағатқа кэштеу
            else:
                error_msg = "Бұл аймақ бойынша деректер табылмады."
        except (requests.RequestException, ValueError, TypeError, KeyError):
            countries = []
            error_msg = "Елдер деректерін жүктеу мүмкін болмады. Кейінірек қайталап көріңіз."
    return render(request, 'travel_app/countries.html', {
        'countries': countries,
        'region': region,
        'regions': REGIONS,
        'error_msg': error_msg,
    })


# ══════════════════════════════════════════════════════
# Байланыс
# ══════════════════════════════════════════════════════
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Хабарламаңыз жіберілді! Жақын арада хабарласамыз.")
            return redirect('travel_app:contact')
    else:
        form = ContactForm()
    return render(request, 'travel_app/contact.html', {'contact_items': [], 'form': form})


# ══════════════════════════════════════════════════════
# Біз туралы
# ══════════════════════════════════════════════════════
def about_view(request):
    return render(request, 'travel_app/about.html', {'stat_items': [], 'team': []})


# ══════════════════════════════════════════════════════
# Таңдаулылар (Wishlist) — session-based
# ══════════════════════════════════════════════════════
def wishlist_view(request):
    wishlist_ids = request.session.get('wishlist', [])
    wishlist_tours = Tour.objects.filter(pk__in=wishlist_ids).select_related('category')
    return render(request, 'travel_app/wishlist.html', {'wishlist_tours': wishlist_tours})


@require_POST
def wishlist_toggle_view(request, slug):
    tour = get_object_or_404(Tour, slug=slug)
    wishlist = request.session.get('wishlist', [])
    if tour.pk in wishlist:
        wishlist.remove(tour.pk)
        added = False
    else:
        wishlist.append(tour.pk)
        added = True
    request.session['wishlist'] = wishlist
    request.session.modified = True
    return JsonResponse({'added': added, 'count': len(wishlist)})
