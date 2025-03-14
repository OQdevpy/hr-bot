# Generated by Django 4.2.20 on 2025-03-08 03:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_time', models.DateTimeField(auto_now_add=True)),
                ('telegram_id', models.BigIntegerField()),
                ('telegram_username', models.CharField(blank=True, max_length=255, null=True)),
                ('full_name', models.CharField(max_length=255)),
                ('phone_number', models.CharField(max_length=20)),
                ('about', models.TextField()),
                ('resume_file_name', models.CharField(max_length=255)),
                ('resume_path', models.CharField(max_length=500)),
            ],
        ),
    ]
