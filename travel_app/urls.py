from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import (
    CategoryViewSet, TourViewSet, TourMetaViewSet, BookingViewSet,
    ReviewViewSet, ProfileViewSet,
    CategoryList, CategoryDetail,
    TourList, TourDetail,
    BookingList, BookingDetail,
    ReviewList, ReviewDetail,
    ProfileList, ProfileDetail,
)

app_name = 'travel_app'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet,  basename='vs-category')
router.register(r'tours',      TourViewSet,      basename='vs-tour')
router.register(r'tourmeta',   TourMetaViewSet,  basename='vs-tourmeta')
router.register(r'bookings',   BookingViewSet,   basename='vs-booking')
router.register(r'reviews',    ReviewViewSet,    basename='vs-review')
router.register(r'profiles',   ProfileViewSet,   basename='vs-profile')

apiview_urlpatterns = [
    path('category/',          CategoryList.as_view()),
    path('category/<int:pk>/', CategoryDetail.as_view()),
    path('tour/',              TourList.as_view()),
    path('tour/<int:pk>/',     TourDetail.as_view()),
    path('booking/',           BookingList.as_view()),
    path('booking/<int:pk>/',  BookingDetail.as_view()),
    path('review/',            ReviewList.as_view()),
    path('review/<int:pk>/',   ReviewDetail.as_view()),
    path('profile/',           ProfileList.as_view()),
    path('profile/<int:pk>/',  ProfileDetail.as_view()),
]

urlpatterns = [
    # Auth
    path('register/', views.register_view,  name='register'),
    path('login/',    views.login_view,     name='login'),
    path('logout/',   views.logout_view,    name='logout'),

    # Pages
    path('',                          views.index_view,          name='index'),
    path('about/',                    views.about_view,          name='about'),
    path('contact/',                  views.contact_view,        name='contact'),
    path('countries/',                views.countries_api_view,  name='countries'),
    path('profile/',                  views.profile_view,        name='profile'),
    path('wishlist/',                 views.wishlist_view,       name='wishlist'),
    path('wishlist/toggle/<slug:slug>/', views.wishlist_toggle_view, name='wishlist_toggle'),

    # Tours
    path('tours/',                    views.tours_view,          name='tours'),
    path('tours/add/',                views.add_tour_view,       name='add_tour'),
    path('tours/<slug:slug>/',        views.tour_detail_view,    name='tour_detail'),
    path('tours/<slug:slug>/book/',   views.book_tour_view,      name='book_tour'),
    path('tours/<slug:slug>/edit/',   views.update_tour_view,    name='update_tour'),
    path('tours/<slug:slug>/delete/', views.delete_tour_view,    name='delete_tour'),

    # REST API
    path('api/vs/', include(router.urls)),
    path('api/av/', include(apiview_urlpatterns)),
]
