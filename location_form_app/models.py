from django.db import models


class LocationSubmission(models.Model):
    email = models.EmailField(unique=True)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=False, blank=True)
    timezone_name = models.CharField(max_length=100, null=True, blank=True)
    local_time = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.location}"
