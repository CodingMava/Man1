"""
Models for finance app.
This file is separate to avoid AppRegistryNotReady errors during Django app initialization.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    target_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"


class Category(models.Model):
    TYPE_CHOICES = (('income', 'Income'), ('expense', 'Expense'))
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.type})"


class Budget(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default='USD')

    class Meta:
        unique_together = ('owner', 'category', 'currency')

    def __str__(self):
        return f"Budget {self.owner}/{self.category}: {self.amount} {self.currency}"


class Transaction(models.Model):
    TYPE_CHOICES = (('income', 'Income'), ('expense', 'Expense'))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    currency = models.CharField(max_length=8, default='USD')
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type} {self.amount} {self.currency}"
