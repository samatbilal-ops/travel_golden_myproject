from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('travel_app', '0002_alter_booking_options_tour_author_and_more'),
    ]

    operations = [
        # Add is_featured to Tour
        migrations.AddField(
            model_name='tour',
            name='is_featured',
            field=models.BooleanField(default=False, verbose_name='Ерекше тур'),
        ),
        # Add icon & description to Category
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.CharField(blank=True, default='fa-globe', max_length=50, verbose_name='Font Awesome иконка'),
        ),
        migrations.AddField(
            model_name='category',
            name='description',
            field=models.TextField(blank=True, verbose_name='Сипаттама'),
        ),
        # Add created_at to Review
        migrations.AddField(
            model_name='review',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        # Add bio & avatar to Profile
        migrations.AddField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True, verbose_name='Өзі туралы'),
        ),
        migrations.AddField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, upload_to='avatars/', verbose_name='Аватар'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='phone',
            field=models.CharField(blank=True, max_length=20, verbose_name='Телефон'),
        ),
        # TourMeta model
        migrations.CreateModel(
            name='TourMeta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('difficulty', models.CharField(
                    choices=[('easy', 'Оңай'), ('medium', 'Орта'), ('hard', 'Қиын')],
                    default='easy', max_length=20, verbose_name='Күрделілік')),
                ('max_capacity', models.PositiveIntegerField(default=20, verbose_name='Максималды орын')),
                ('includes', models.TextField(blank=True, verbose_name='Бағасына кіреді')),
                ('excludes', models.TextField(blank=True, verbose_name='Бағасына кірмейді')),
                ('min_age', models.PositiveIntegerField(default=0, verbose_name='Минималды жас')),
                ('language', models.CharField(default='Қазақша, Орысша', max_length=50, verbose_name='Гид тілі')),
                ('views_count', models.PositiveIntegerField(default=0, verbose_name='Қаралым саны')),
                ('tour', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='meta',
                    to='travel_app.tour',
                    verbose_name='Тур')),
            ],
            options={
                'verbose_name': 'Тур мета-деректері',
                'verbose_name_plural': 'Тур мета-деректері',
            },
        ),
    ]
