from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name  = models.CharField(max_length=120, blank=True)
    avatar_url = models.URLField(blank=True)
    preferred_lang = models.CharField(max_length=10, default='hi-IN')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile({self.user.username})"


class ChatHistory(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats', null=True, blank=True)
    session_key = models.CharField(max_length=80, blank=True)  # for guests
    role        = models.CharField(max_length=10)  # 'user' or 'chloe'
    message     = models.TextField()
    cv_mood     = models.CharField(max_length=40, blank=True)
    cv_color    = models.CharField(max_length=40, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.message[:50]}"
