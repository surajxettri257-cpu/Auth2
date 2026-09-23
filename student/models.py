from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_no = models.PositiveBigIntegerField(unique=True)
    batch = models.PositiveBigIntegerField()
    faculty = models.CharField(max_length=88)
    address = models.CharField(max_length=255)
    phoneNo = models.PositiveBigIntegerField()
    isActive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id, "-", self.name