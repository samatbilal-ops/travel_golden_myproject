from django.utils import timezone
from rest_framework import serializers

from .models import Category, Tour, TourMeta, Booking, Review, Profile


class CategorySerializer(serializers.ModelSerializer):
    tour_count = serializers.IntegerField(source='tours.count', read_only=True)

    class Meta:
        model  = Category
        fields = '__all__'


class TourMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TourMeta
        fields = '__all__'


class TourSerializer(serializers.ModelSerializer):
    category_name   = serializers.CharField(source='category.name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    avg_rating      = serializers.SerializerMethodField()
    meta            = TourMetaSerializer(read_only=True)

    class Meta:
        model  = Tour
        fields = '__all__'
        read_only_fields = ('slug', 'author', 'created_at', 'updated_at')

    def get_avg_rating(self, obj):
        return obj.average_rating()


class BookingSerializer(serializers.ModelSerializer):
    username   = serializers.CharField(source='user.username', read_only=True)
    tour_title = serializers.CharField(source='tour.title',   read_only=True)

    class Meta:
        model  = Booking
        fields = '__all__'
        # Пайдаланушы, баға және күй клиенттен қабылданбайды — серверде анықталады
        read_only_fields = ('user', 'total_price', 'status', 'booking_date')

    def validate_start_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Басталу күні бүгіннен кем болмауы керек.")
        return value

    def validate_num_people(self, value):
        if not 1 <= value <= 50:
            raise serializers.ValidationError("Адам саны 1-ден 50-ге дейін болуы керек.")
        return value

    def create(self, validated_data):
        tour = validated_data['tour']
        validated_data['total_price'] = tour.price * validated_data['num_people']
        return super().create(validated_data)

    def update(self, instance, validated_data):
        tour = validated_data.get('tour', instance.tour)
        people = validated_data.get('num_people', instance.num_people)
        validated_data['total_price'] = tour.price * people
        return super().update(instance, validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    username   = serializers.CharField(source='user.username', read_only=True)
    tour_title = serializers.CharField(source='tour.title',   read_only=True)

    class Meta:
        model  = Review
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Баға 1-ден 5-ке дейін болуы керек.")
        return value


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model  = Profile
        fields = '__all__'
        read_only_fields = ('user',)
