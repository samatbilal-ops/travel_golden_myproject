from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Booking, Tour, Review, ContactMessage
from django.utils import timezone


# ══════════════════════════════════════════════════════
# ТАПСЫРМА 1 + 2 — Тіркелу формасы (валидациямен)
# ══════════════════════════════════════════════════════
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.com'}),
    )
    first_name = forms.CharField(
        max_length=50, required=True, label="Аты",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Аты'}),
    )
    last_name = forms.CharField(
        max_length=50, required=True, label="Тегі",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Тегі'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {'username': 'Пайдаланушы аты'}
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].label = 'Құпия сөз'
        self.fields['password2'].label = 'Құпия сөзді растау'
        for f in self.fields.values():
            f.help_text = None

    # ТАПСЫРМА 2 — Валидация
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if len(username) < 3:
            raise forms.ValidationError("Пайдаланушы аты кем дегенде 3 таңбадан тұруы керек.")
        if not username.isalnum():
            raise forms.ValidationError("Пайдаланушы аты тек әріп және санды қамтуы керек.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Бұл пайдаланушы аты бос емес.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Бұл email бұрыннан тіркелген.")
        return email

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if not name.replace(' ', '').isalpha():
            raise forms.ValidationError("Атта тек әріптер болуы керек.")
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if not name.replace(' ', '').isalpha():
            raise forms.ValidationError("Тегінде тек әріптер болуы керек.")
        return name


# ══════════════════════════════════════════════════════
# ТАПСЫРМА 1 — Кіру формасы
# ══════════════════════════════════════════════════════
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Логин'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Құпия сөз'})
        self.fields['username'].label = 'Пайдаланушы аты'
        self.fields['password'].label = 'Құпия сөз'


# ══════════════════════════════════════════════════════
# ТАПСЫРМА 2 — Брондау формасы (валидациямен)
# ══════════════════════════════════════════════════════
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['start_date', 'num_people', 'notes']
        labels = {
            'start_date': 'Басталу күні',
            'num_people': 'Адам саны',
            'notes': 'Қосымша ескертулер',
        }
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'num_people': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].widget.attrs['min'] = timezone.localdate().isoformat()
        self.fields['num_people'].widget.attrs['max'] = 50

    def clean_start_date(self):
        date = self.cleaned_data.get('start_date')
        if date and date < timezone.localdate():
            raise forms.ValidationError("Басталу күні бүгіннен кем болмауы керек.")
        return date

    def clean_num_people(self):
        n = self.cleaned_data.get('num_people')
        if n is not None and n < 1:
            raise forms.ValidationError("Адам саны кем дегенде 1 болуы керек.")
        if n is not None and n > 50:
            raise forms.ValidationError("Адам саны 50-ден аспауы керек.")
        return n


# ══════════════════════════════════════════════════════
# ТАПСЫРМА 2 — Тур қосу формасы (валидациямен)
# ══════════════════════════════════════════════════════
class TourAddForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ['category', 'title', 'description', 'price', 'duration', 'image']
        labels = {
            'category': 'Санат',
            'title': 'Атауы',
            'description': 'Сипаттамасы',
            'price': 'Бағасы (тг)',
            'duration': 'Ұзақтығы (күн)',
            'image': 'Сурет',
        }
        widgets = {
            'category':    forms.Select(attrs={'class': 'form-control'}),
            'title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Мысалы: Алматыға саяхат'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price':       forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'duration':    forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'image':       forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError("Атауы кем дегенде 5 таңбадан тұруы керек.")
        if len(title) > 200:
            raise forms.ValidationError("Атауы 200 таңбадан аспауы керек.")
        return title

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Баға теріс болмауы керек.")
        return price

    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if duration is not None and duration < 1:
            raise forms.ValidationError("Ұзақтығы кем дегенде 1 күн болуы керек.")
        if duration is not None and duration > 365:
            raise forms.ValidationError("Ұзақтығы 365 күннен аспауы керек.")
        return duration

    def clean_description(self):
        desc = self.cleaned_data.get('description', '').strip()
        if len(desc) < 20:
            raise forms.ValidationError("Сипаттама кем дегенде 20 таңбадан тұруы керек.")
        return desc


# ══════════════════════════════════════════════════════
# ТАПСЫРМА 2 — Пікір формасы (валидациямен)
# ══════════════════════════════════════════════════════
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {'rating': 'Баға (1-5)', 'comment': 'Пікір'}
        widgets = {
            'rating':  forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_rating(self):
        r = self.cleaned_data.get('rating')
        if r is not None and not (1 <= r <= 5):
            raise forms.ValidationError("Баға 1-ден 5-ке дейін болуы керек.")
        return r

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if len(comment) < 5:
            raise forms.ValidationError("Пікір кем дегенде 5 таңбадан тұруы керек.")
        return comment


# ══════════════════════════════════════════════════════
# Байланыс формасы
# ══════════════════════════════════════════════════════
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        labels = {'name': 'Атыңыз', 'email': 'Email', 'subject': 'Тақырып', 'message': 'Хабарлама'}
        widgets = {
            'name':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Аты-жөніңіз'}),
            'email':   forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Хабарлама тақырыбы'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5,
                                             'placeholder': 'Сұрағыңызды жазыңыз...'}),
        }

    def clean_message(self):
        msg = self.cleaned_data.get('message', '').strip()
        if len(msg) < 10:
            raise forms.ValidationError("Хабарлама кем дегенде 10 таңбадан тұруы керек.")
        return msg
