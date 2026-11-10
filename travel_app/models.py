from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User

from .utils import unique_slug


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Атауы")
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, verbose_name="Сипаттама")
    icon = models.CharField(max_length=50, blank=True, default="fa-globe",
                            verbose_name="Font Awesome иконка")

    class Meta:
        verbose_name = "Санат"
        verbose_name_plural = "Санаттар"
        ordering = ['name']

    def __str__(self):
        return self.name


class Tour(models.Model):
    title       = models.CharField(max_length=200, verbose_name="Атауы")
    slug        = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(verbose_name="Сипаттама")
    price       = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Бағасы",
                                      validators=[MinValueValidator(0)])
    duration    = models.PositiveIntegerField(verbose_name="Ұзақтығы (күн)",
                                              validators=[MinValueValidator(1)])
    image       = models.ImageField(upload_to='tours/', blank=True, verbose_name="Сурет")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    category    = models.ForeignKey(Category, on_delete=models.CASCADE,
                                    related_name='tours', verbose_name="Санат")
    author      = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    is_featured = models.BooleanField(default=False, verbose_name="Ерекше тур")

    class Meta:
        verbose_name = "Тур"
        verbose_name_plural = "Турлар"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Tour, self.title, exclude_pk=self.pk)
        super().save(*args, **kwargs)

    def average_rating(self):
        avg = self.review_set.aggregate(avg=Avg('rating'))['avg']
        return round(avg, 1) if avg else 0


class TourMeta(models.Model):
    """
    2.2.4 — Мета-модель (Tour моделін кеңейту үшін)
    Турдың қосымша сипаттамаларын сақтайды.
    """
    tour         = models.OneToOneField(Tour, on_delete=models.CASCADE,
                                        related_name='meta', verbose_name="Тур")
    difficulty   = models.CharField(
        max_length=20,
        choices=[('easy', 'Оңай'), ('medium', 'Орта'), ('hard', 'Қиын')],
        default='easy', verbose_name="Күрделілік")
    max_capacity = models.PositiveIntegerField(default=20, verbose_name="Максималды орын")
    includes     = models.TextField(blank=True, verbose_name="Бағасына кіреді")
    excludes     = models.TextField(blank=True, verbose_name="Бағасына кірмейді")
    min_age      = models.PositiveIntegerField(default=0, verbose_name="Минималды жас")
    language     = models.CharField(max_length=50, default="Қазақша, Орысша",
                                    verbose_name="Гид тілі")
    views_count  = models.PositiveIntegerField(default=0, verbose_name="Қаралым саны")

    class Meta:
        verbose_name = "Тур мета-деректері"
        verbose_name_plural = "Тур мета-деректері"

    def __str__(self):
        return f"{self.tour.title} — мета"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Күтілуде'),
        ('confirmed', 'Расталды'),
        ('cancelled', 'Бас тартылды'),
    ]
    booking_date = models.DateTimeField(auto_now_add=True)
    start_date   = models.DateField(verbose_name="Басталу күні")
    num_people   = models.PositiveIntegerField(verbose_name="Адам саны",
                                               validators=[MinValueValidator(1)])
    total_price  = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Жалпы баға")
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                    default='pending', verbose_name="Күйі")
    notes        = models.TextField(blank=True, verbose_name="Ескертулер")
    user         = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пайдаланушы")
    # PROTECT: турды жойғанда клиенттердің брондаулары үнсіз жоғалып кетпейді
    tour         = models.ForeignKey(Tour, on_delete=models.PROTECT, verbose_name="Тур")

    class Meta:
        verbose_name = "Брондау"
        verbose_name_plural = "Брондаулар"
        ordering = ['-booking_date']

    def __str__(self):
        return f"{self.user.username} — {self.tour.title}"


class Review(models.Model):
    rating  = models.IntegerField(verbose_name="Баға",
                                  validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(verbose_name="Пікір")
    created_at = models.DateTimeField(auto_now_add=True)
    tour    = models.ForeignKey(Tour, on_delete=models.CASCADE, verbose_name="Тур")
    user    = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пайдаланушы")

    class Meta:
        verbose_name = "Пікір"
        verbose_name_plural = "Пікірлер"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.tour.title} ({self.rating}/5)"


class Profile(models.Model):
    phone  = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    bio    = models.TextField(blank=True, verbose_name="Өзі туралы")
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name="Аватар")
    user   = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пайдаланушы")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профильдер"

    def __str__(self):
        return self.user.username


class ContactMessage(models.Model):
    name       = models.CharField(max_length=100, verbose_name="Аты")
    email      = models.EmailField(verbose_name="Email")
    subject    = models.CharField(max_length=200, blank=True, verbose_name="Тақырып")
    message    = models.TextField(verbose_name="Хабарлама")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False, verbose_name="Оқылды")

    class Meta:
        verbose_name = "Байланыс хабарламасы"
        verbose_name_plural = "Байланыс хабарламалары"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.subject or 'тақырыпсыз'}"
