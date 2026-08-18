from django.db import models
from ckeditor.fields import RichTextField

# Create your models here.
class Case(models.Model):

    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        WORKING = "working", "Working"
        COMPLETED = "completed", "Completed"


    name = models.CharField(max_length=100)
    description = RichTextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    assigned_to = models.ManyToManyField("user.Person", related_name="cases", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name