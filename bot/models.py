from django.db import models

class Registration(models.Model):
    registration_time = models.DateTimeField(auto_now_add=True)
    telegram_id = models.BigIntegerField()
    telegram_username = models.CharField(max_length=255, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    about = models.TextField()
    resume_file_name = models.CharField(max_length=255)
    resume_telegram_link = models.URLField(max_length=500)  
    
    def __str__(self):
        return f"{self.full_name} ({self.telegram_id})"