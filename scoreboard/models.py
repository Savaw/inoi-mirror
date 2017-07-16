from django.db import models


class Username(models.Model):
    def __str__(self):
        return self.handle

    handle = models.CharField(max_length=100)
