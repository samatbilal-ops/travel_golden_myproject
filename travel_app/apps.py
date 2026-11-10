from django.apps import AppConfig


class TravelAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'travel_app'
    verbose_name = "Туристік қосымша"

    def ready(self):
        from . import signals  # noqa: F401
