import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aptitude', '0002_aptitudequestion_hr_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='AptitudeTestAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_key', models.CharField(db_index=True, max_length=64)),
                ('questions', models.JSONField(default=list)),
                ('answers', models.JSONField(blank=True, default=dict)),
                ('total_questions', models.PositiveSmallIntegerField(default=50)),
                ('duration_seconds', models.PositiveIntegerField(default=3000)),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_at', models.DateTimeField()),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('score', models.PositiveSmallIntegerField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
    ]
