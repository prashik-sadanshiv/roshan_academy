from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    email       = models.EmailField(unique=True)
    avatar      = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio         = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS =  ['username']

    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email
    
    @property
    def active_subscription(self):
        return self.subscription.filter(
            status='active',
            end_data__gte=timezone.now()
        ).first()
    
    @property
    def is_pro(self):
        return self.active_subscription is not None
    

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('pro', 'Pro - $10/mo'),
        ('elite', 'Elite - $20/mo'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan            = models.CharField(max_length=20, choices=PLAN_CHOICES)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_sub_id   = models.CharField(max_length=200, blank=True)
    start_data      = models.DateTimeField(auto_now_add=True)
    end_date        = models.DateTimeField()
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.plan} ({self.status})'

        

