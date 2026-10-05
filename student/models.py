from django.db import models
from core.storage_backend import mediaStorage
# Create your models here.

def media_storage_path(instance, filename):
    return f"students/{instance.symbolNo}/{filename}"


class Student(models.Model):
    name = models.CharField(max_length=100)
    symbolNo = models.PositiveIntegerField(unique=True)
    batch = models.PositiveIntegerField()
    faculty = models.CharField(max_length=88)
    address = models.CharField(max_length=255)
    phoneNo = models.PositiveIntegerField()
    isActive = models.BooleanField(default=True)
    profile = models.ImageField(upload_to=media_storage_path, storage=mediaStorage, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.name}"