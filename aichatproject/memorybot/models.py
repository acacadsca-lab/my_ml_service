from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Model 1: Chat Session (Oru conversation)
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title

# Model 2: Chat Messages (Individual messages)
class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    is_bot = models.BooleanField(default=False)  
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['timestamp'] 
    
    def __str__(self):
        return f"{'Bot' if self.is_bot else 'User'}: {self.content[:30]}"

class BotMemory(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100, blank=True)
    interests = models.TextField(blank=True) 
    facts = models.TextField(blank=True)
    
    def __str__(self):
        return f"Memory of {self.user.username}"