from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Person(models.Model):

    class PersonType(models.TextChoices):
        EMPLOYEE = "employee", "Employee"
        MANAGER = "manager", "Manager"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    person_type = models.CharField(max_length=10, choices=PersonType.choices)
    email = models.EmailField(blank=True, null=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"