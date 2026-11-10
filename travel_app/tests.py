import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Category, Tour, Booking, Review, Profile, ContactMessage
from .utils import unique_slug


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('boss', password='pass12345', is_staff=True)
        cls.user = User.objects.create_user('ali', password='pass12345', email='ali@example.com')
        cls.other = User.objects.create_user('vali', password='pass12345')
        cls.cat = Category.objects.create(name='Тау', slug='tau')
        cls.tour = Tour.objects.create(
            title='Шымбұлақ туры', description='Тау шаңғысы және демалыс үшін тамаша бағыт.',
            price=Decimal('50000'), duration=3, category=cls.cat, author=cls.staff)


class PagesTests(Base):
    def test_public_pages_ok(self):
        for name in ['index', 'tours', 'about', 'contact', 'login', 'register', 'wishlist']:
            self.assertEqual(self.client.get(reverse(f'travel_app:{name}')).status_code, 200, name)
        self.assertEqual(self.client.get(self.tour_url()).status_code, 200)

    def tour_url(self):
        return reverse('travel_app:tour_detail', args=[self.tour.slug])

    def test_base_has_no_stray_js_text(self):
        html = self.client.get(reverse('travel_app:index')).content.decode()
        body_after_scripts = html.split('</script>')[-1]
        self.assertNotIn('function wlToggle', body_after_scripts)
        self.assertIn('function wlToggle', html)

    def test_pagination_keeps_encoded_query(self):
        for i in range(8):
            Tour.objects.create(title=f'Тест тур {i}', description='x' * 30, price=1,
                                duration=1, category=self.cat, author=self.staff)
        html = self.client.get(reverse('travel_app:tours'), {'q': 'Тест'}).content.decode()
        self.assertIn('page=2&q=%D0%A2%D0%B5%D1%81%D1%82', html)

    def test_views_counter_increments_once_per_get(self):
        self.client.get(self.tour_url())
        self.client.get(self.tour_url())
        self.tour.meta.refresh_from_db()
        self.assertEqual(self.tour.meta.views_count, 2)


class SlugTests(Base):
    def test_cyrillic_title_gets_ascii_slug(self):
        self.assertEqual(self.tour.slug, 'shymbulaq-tury')
        self.assertEqual(unique_slug(Tour, 'Шымбұлақ туры'), 'shymbulaq-tury-1')


class AuthTests(Base):
    def test_register_creates_profile(self):
        r = self.client.post(reverse('travel_app:register'), {
            'username': 'newuser', 'first_name': 'Айдар', 'last_name': 'Серік',
            'email': 'NEW@example.com', 'password1': 'Str0ng!Pass_91', 'password2': 'Str0ng!Pass_91'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Profile.objects.filter(user__username='newuser').exists())

    def test_register_email_case_insensitive_duplicate(self):
        r = self.client.post(reverse('travel_app:register'), {
            'username': 'dup', 'first_name': 'А', 'last_name': 'Б', 'email': 'ALI@example.com',
            'password1': 'Str0ng!Pass_91', 'password2': 'Str0ng!Pass_91'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='dup').exists())

    def test_login_blocks_open_redirect(self):
        r = self.client.post(reverse('travel_app:login') + '?next=https://evil.example/',
                             {'username': 'ali', 'password': 'pass12345'})
        self.assertRedirects(r, reverse('travel_app:index'), fetch_redirect_response=False)

    def test_login_allows_local_next(self):
        r = self.client.post(reverse('travel_app:login') + '?next=/tours/',
                             {'username': 'ali', 'password': 'pass12345'})
        self.assertRedirects(r, '/tours/', fetch_redirect_response=False)

    def test_logout_requires_post(self):
        self.client.login(username='ali', password='pass12345')
        self.assertEqual(self.client.get(reverse('travel_app:logout')).status_code, 405)
        self.assertEqual(self.client.post(reverse('travel_app:logout')).status_code, 302)


class TourCrudTests(Base):
    def test_staff_can_add_tour_with_cyrillic_title(self):
        self.client.login(username='boss', password='pass12345')
        r = self.client.post(reverse('travel_app:add_tour'), {
            'category': self.cat.pk, 'title': 'Алматы саяхаты',
            'description': 'Алматыны аралау және таулы аймақтарға шығу.', 'price': '90000', 'duration': 2})
        self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
        self.assertTrue(Tour.objects.filter(slug='almaty-sayakhaty').exists())

    def test_non_staff_cannot_add(self):
        self.client.login(username='ali', password='pass12345')
        r = self.client.get(reverse('travel_app:add_tour'))
        self.assertRedirects(r, reverse('travel_app:tours'), fetch_redirect_response=False)

    def test_delete_tour_with_bookings_is_blocked(self):
        Booking.objects.create(user=self.user, tour=self.tour, start_date=timezone.localdate(),
                               num_people=1, total_price=1)
        self.client.login(username='boss', password='pass12345')
        r = self.client.post(reverse('travel_app:delete_tour', args=[self.tour.slug]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Tour.objects.filter(pk=self.tour.pk).exists())


class BookingReviewTests(Base):
    def test_booking_total_and_past_date(self):
        self.client.login(username='ali', password='pass12345')
        url = reverse('travel_app:book_tour', args=[self.tour.slug])
        bad = self.client.post(url, {'start_date': '2000-01-01', 'num_people': 2})
        self.assertEqual(bad.status_code, 200)
        future = (timezone.localdate() + datetime.timedelta(days=5)).isoformat()
        ok = self.client.post(url, {'start_date': future, 'num_people': 3})
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(Booking.objects.get().total_price, Decimal('150000'))

    def test_book_page_script_rendered_once(self):
        self.client.login(username='ali', password='pass12345')
        html = self.client.get(reverse('travel_app:book_tour', args=[self.tour.slug])).content.decode()
        self.assertEqual(html.count("getElementById('id_num_people')"), 1)

    def test_review_rating_validated(self):
        self.client.login(username='ali', password='pass12345')
        url = reverse('travel_app:tour_detail', args=[self.tour.slug])
        self.client.post(url, {'rating': 9, 'comment': 'Керемет тур!'})
        self.assertEqual(Review.objects.count(), 0)
        self.client.post(url, {'rating': 5, 'comment': 'Керемет тур!'})
        self.assertEqual(Review.objects.count(), 1)


class WishlistTests(Base):
    def test_toggle_requires_post_and_works(self):
        url = reverse('travel_app:wishlist_toggle', args=[self.tour.slug])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).json(), {'added': True, 'count': 1})
        self.assertIn(self.tour.slug, self.client.get(reverse('travel_app:index')).context['wishlist_slugs'])
        self.assertEqual(self.client.post(url).json(), {'added': False, 'count': 0})

    def test_toggle_enforces_csrf(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        r = c.post(reverse('travel_app:wishlist_toggle', args=[self.tour.slug]))
        self.assertEqual(r.status_code, 403)


class ContactTests(Base):
    def test_contact_form_saves_message(self):
        r = self.client.post(reverse('travel_app:contact'), {
            'name': 'Дана', 'email': 'd@example.com', 'subject': 'Сұрақ',
            'message': 'Тур бағасы туралы сұрағым бар.'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)


class ApiPermissionTests(Base):
    def setUp(self):
        self.api = APIClient()

    def test_anonymous_cannot_write_or_delete(self):
        self.assertEqual(self.api.get('/api/vs/tours/').status_code, 200)
        self.assertIn(self.api.delete(f'/api/vs/tours/{self.tour.pk}/').status_code, (401, 403))
        self.assertIn(self.api.post('/api/av/category/', {'name': 'x', 'slug': 'x'}).status_code, (401, 403))
        self.assertIn(self.api.get('/api/vs/bookings/').status_code, (401, 403))
        self.assertIn(self.api.get('/api/vs/profiles/').status_code, (401, 403))

    def test_regular_user_cannot_edit_tours(self):
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.put(f'/api/av/tour/{self.tour.pk}/', {}, format='json').status_code, 403)
        self.assertEqual(self.api.delete(f'/api/vs/tours/{self.tour.pk}/').status_code, 403)

    def test_booking_user_and_price_are_server_side_and_private(self):
        self.api.force_authenticate(self.user)
        future = (timezone.localdate() + datetime.timedelta(days=3)).isoformat()
        r = self.api.post('/api/vs/bookings/', {
            'tour': self.tour.pk, 'start_date': future, 'num_people': 2,
            'user': self.other.pk, 'total_price': '1', 'status': 'confirmed'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        b = Booking.objects.get()
        self.assertEqual((b.user, b.total_price, b.status), (self.user, Decimal('100000'), 'pending'))
        # басқа пайдаланушы көрмейді
        self.api.force_authenticate(self.other)
        self.assertEqual(len(self.api.get('/api/vs/bookings/').json()), 0)
        self.assertEqual(self.api.get(f'/api/av/booking/{b.pk}/').status_code, 404)

    def test_review_owner_only_and_rating_range(self):
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.post('/api/vs/reviews/', {'tour': self.tour.pk, 'rating': 11,
                                                             'comment': 'abc'}, format='json').status_code, 400)
        r = self.api.post('/api/vs/reviews/', {'tour': self.tour.pk, 'rating': 4, 'comment': 'жақсы'}, format='json')
        self.assertEqual(r.status_code, 201)
        pk = r.json()['id']
        self.api.force_authenticate(self.other)
        self.assertEqual(self.api.delete(f'/api/vs/reviews/{pk}/').status_code, 403)

    def test_staff_can_create_tour_via_api(self):
        self.api.force_authenticate(self.staff)
        r = self.api.post('/api/vs/tours/', {'title': 'Жаңа API тур', 'description': 'сипаттама ' * 5,
                                             'price': '1000', 'duration': 2, 'category': self.cat.pk}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['slug'], 'zhana-api-tur')
        self.assertEqual(r.json()['author_username'], 'boss')


class CountriesViewTests(Base):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def _mock(self, payload, status=200):
        from unittest import mock
        resp = mock.Mock(status_code=status)
        resp.json.return_value = payload
        resp.raise_for_status.return_value = None
        return mock.patch('travel_app.views.requests.get', return_value=resp)

    def test_dict_response_does_not_crash(self):
        with self._mock({'status': 400, 'message': 'Bad request'}):
            r = self.client.get(reverse('travel_app:countries'))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['error_msg'])

    def test_valid_response_and_cache(self):
        data = [{'name': {'common': 'Japan'}, 'capital': ['Tokyo'], 'population': 1,
                 'flags': {'png': 'x'}, 'languages': {'jpn': 'Japanese'}, 'area': 5.0}]
        with self._mock(data) as m:
            r = self.client.get(reverse('travel_app:countries'))
            self.client.get(reverse('travel_app:countries'))
        self.assertEqual(r.context['countries'][0]['name'], 'Japan')
        self.assertEqual(m.call_count, 1)  # екінші сұраныс кэштен
