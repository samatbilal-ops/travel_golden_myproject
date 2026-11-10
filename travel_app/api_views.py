from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404

from .models import Category, Tour, TourMeta, Booking, Review, Profile
from .serializers import (
    CategorySerializer, TourSerializer, TourMetaSerializer,
    BookingSerializer, ReviewSerializer, ProfileSerializer
)
from .permissions import IsStaffOrReadOnly, IsOwnerOrStaff, IsOwnerOrStaffOrReadOnly


# ── Көмекші: «менікі» сүзгісі және сақтау ──────────────────────
def own_queryset(qs, user):
    """Әкімші — бәрін, қарапайым пайдаланушы — тек өзінің жазбаларын көреді."""
    return qs if user.is_staff else qs.filter(user=user)


# ══════════════════════════════════════════════════════════════
# ViewSets (Тапсырма 3 — ModelViewSet)
# ══════════════════════════════════════════════════════════════
class CategoryViewSet(viewsets.ModelViewSet):
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]


class TourViewSet(viewsets.ModelViewSet):
    queryset           = Tour.objects.select_related('category', 'author').all()
    serializer_class   = TourSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({'detail': 'Турға брондаулар бар, жоюға болмайды.'},
                            status=status.HTTP_409_CONFLICT)


class TourMetaViewSet(viewsets.ModelViewSet):
    queryset           = TourMeta.objects.all()
    serializer_class   = TourMetaSerializer
    permission_classes = [IsStaffOrReadOnly]


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class   = BookingSerializer
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        return own_queryset(Booking.objects.select_related('user', 'tour'), self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset           = Review.objects.select_related('user', 'tour').all()
    serializer_class   = ReviewSerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class   = ProfileSerializer
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        return own_queryset(Profile.objects.select_related('user'), self.request.user)

    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise PermissionDenied('Профиль бұрыннан бар.')
        serializer.save(user=self.request.user)


# ══════════════════════════════════════════════════════════════
# APIView (Тапсырма 4) — бір базалық класс, қайталануды болдырмау үшін
# ══════════════════════════════════════════════════════════════
class BaseList(APIView):
    model = None
    serializer_class = None
    permission_classes = [IsStaffOrReadOnly]
    owner_field = None          # 'user' болса — жазба автоматты түрде request.user-ге байланады

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request):
        s = self.serializer_class(self.get_queryset(), many=True)
        return Response(s.data)

    def post(self, request):
        s = self.serializer_class(data=request.data)
        if s.is_valid():
            extra = {self.owner_field: request.user} if self.owner_field else {}
            s.save(**extra)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseDetail(APIView):
    model = None
    serializer_class = None
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self, pk):
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, pk):
        return Response(self.serializer_class(self.get_object(pk)).data)

    def put(self, request, pk):
        s = self.serializer_class(self.get_object(pk), data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        s = self.serializer_class(self.get_object(pk), data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            self.get_object(pk).delete()
        except ProtectedError:
            return Response({'detail': 'Байланысты жазбалар бар, жоюға болмайды.'},
                            status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryList(BaseList):
    model, serializer_class = Category, CategorySerializer

class CategoryDetail(BaseDetail):
    model, serializer_class = Category, CategorySerializer


class TourList(BaseList):
    model, serializer_class = Tour, TourSerializer
    owner_field = 'author'

class TourDetail(BaseDetail):
    model, serializer_class = Tour, TourSerializer


class BookingList(BaseList):
    model, serializer_class = Booking, BookingSerializer
    permission_classes = [IsOwnerOrStaff]
    owner_field = 'user'

    def get_queryset(self):
        return own_queryset(Booking.objects.select_related('user', 'tour'), self.request.user)

class BookingDetail(BaseDetail):
    model, serializer_class = Booking, BookingSerializer
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        return own_queryset(Booking.objects.select_related('user', 'tour'), self.request.user)


class ReviewList(BaseList):
    model, serializer_class = Review, ReviewSerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]
    owner_field = 'user'

class ReviewDetail(BaseDetail):
    model, serializer_class = Review, ReviewSerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]


class ProfileList(BaseList):
    model, serializer_class = Profile, ProfileSerializer
    permission_classes = [IsOwnerOrStaff]
    owner_field = 'user'

    def get_queryset(self):
        return own_queryset(Profile.objects.select_related('user'), self.request.user)

    def post(self, request):
        if Profile.objects.filter(user=request.user).exists():
            return Response({'detail': 'Профиль бұрыннан бар.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().post(request)

class ProfileDetail(BaseDetail):
    model, serializer_class = Profile, ProfileSerializer
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        return own_queryset(Profile.objects.select_related('user'), self.request.user)
