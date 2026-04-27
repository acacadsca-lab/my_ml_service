from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class PDFDocument(models.Model):
    title = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to='pdfs/')
    vector_index_path = models.CharField(max_length=500, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title


class ChatSession(models.Model):
    """Universal chat session for both chatbot and code generator"""
    
    SESSION_TYPES = (
        ('chatbot', 'General Chatbot'),
        ('code_generator', 'Code Generator'),
        ('pdf_chat', 'PDF Chat'),
    )
    
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_sessions')
    
    # Session Type - KEY DIFFERENTIATOR
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='chatbot', db_index=True)
    
    # Session Info
    title = models.CharField(max_length=255, default="New Chat", blank=True)
    
    # For PDF Chat
    pdf_document = models.ForeignKey(
        PDFDocument, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='chat_sessions'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # For anonymous users
    anonymous_session_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    # Metadata
    total_messages = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0, null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
        indexes = [
            models.Index(fields=['session_type', 'user']),
            models.Index(fields=['session_type', 'anonymous_session_key']),
            models.Index(fields=['is_active', 'session_type']),
        ]
    
    def __str__(self):
        type_display = self.get_session_type_display()
        if self.title:
            return f"[{type_display}] {self.title}"
        return f"[{type_display}] Session {str(self.session_id)[:8]}"
    
    def get_message_count(self):
        return self.messages.count()
    
    def get_first_user_message(self):
        """Get first user message to use as session title"""
        first_msg = self.messages.filter(message_type='user').first()
        if first_msg:
            return first_msg.content[:50] + ('...' if len(first_msg.content) > 50 else '')
        return None
    
    def update_title_from_first_message(self):
        """Auto-generate title from first user message"""
        if not self.title or self.title == "New Chat":
            first_message = self.get_first_user_message()
            if first_message:
                self.title = first_message
                self.save(update_fields=['title'])
    
    def is_chatbot(self):
        return self.session_type == 'chatbot'
    
    def is_code_generator(self):
        return self.session_type == 'code_generator'
    
    def is_pdf_chat(self):
        return self.session_type == 'pdf_chat'


class ChatMessage(models.Model):
    """Universal message model for all chat types"""
    
    MESSAGE_TYPES = (
        ('user', 'User'),
        ('bot', 'Bot'),
        ('system', 'System'),
    )
    
    id = models.AutoField(primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    
    # Message Content
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Performance Metrics
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in seconds")
    tokens_used = models.IntegerField(default=0, null=True, blank=True)
    
    # Code Generator Specific Fields
    detected_language = models.CharField(max_length=50, null=True, blank=True)
    is_code_request = models.BooleanField(default=False)
    
    # Error Tracking
    error_occurred = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    
    # PDF Chat Specific
    pdf_page_references = models.JSONField(null=True, blank=True, help_text="Page numbers referenced from PDF")
    confidence_score = models.FloatField(null=True, blank=True, help_text="Confidence score for PDF answers")
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['message_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"[{self.session.get_session_type_display()}] {self.message_type}: {self.content[:50]}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update session's total messages count
        self.session.total_messages = self.session.messages.count()
        self.session.save(update_fields=['total_messages', 'updated_at'])


class UserPreferences(models.Model):
    """Store user chatbot preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_preferences')
    
    # General Chatbot Settings
    model_choice = models.CharField(max_length=50, default='gpt-4')
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2000)
    
    # Code Generator Settings
    default_programming_language = models.CharField(max_length=50, default='python')
    code_theme = models.CharField(
        max_length=20, 
        default='dark', 
        choices=[('dark', 'Dark'), ('light', 'Light')]
    )
    
    # UI Preferences
    theme = models.CharField(
        max_length=20, 
        default='dark', 
        choices=[('dark', 'Dark'), ('light', 'Light'), ('auto', 'Auto')]
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Anonymous user support
    anonymous_session_key = models.CharField(max_length=255, null=True, blank=True, unique=True)
    
    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
    
    def __str__(self):
        if self.user:
            return f"Preferences for {self.user.username}"
        return f"Anonymous Preferences - {self.anonymous_session_key}"


class CodeSnippet(models.Model):
    """Store code snippets generated during code generator chat"""
    
    id = models.AutoField(primary_key=True)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='code_snippets')
    
    # Code Details
    language = models.CharField(max_length=50)
    code = models.TextField()
    
    # Metadata
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    # User Actions
    is_bookmarked = models.BooleanField(default=False)
    is_copied = models.BooleanField(default=False)
    copy_count = models.IntegerField(default=0)
    
    # ✅ FIXED: Removed default=timezone.now()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Code Snippet'
        verbose_name_plural = 'Code Snippets'
    
    def __str__(self):
        return f"{self.language} - {self.title or 'Untitled'}"
    
    def increment_copy_count(self):
        self.copy_count += 1
        self.is_copied = True
        self.save(update_fields=['copy_count', 'is_copied'])


class ChatHistory(models.Model):
    """Legacy model - will be migrated to ChatSession/ChatMessage"""
    document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    
    # ✅ FIXED: Removed default=timezone.now()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat History (Legacy)'
        verbose_name_plural = 'Chat Histories (Legacy)'
    
    def __str__(self):
        return f"Q: {self.question[:50]}"
    

class BlogPost(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    topic = models.CharField(max_length=200)
    content = models.TextField()
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.topic
    
    def get_preview(self):
        """First 2 lines of content"""
        lines = self.content.split('\n')[:2]
        preview = ' '.join(lines)
        if len(preview) > 150:
            return preview[:150] + '...'
        return preview
    
    def get_reading_time(self):
        """Estimate reading time"""
        word_count = len(self.content.split())
        minutes = word_count // 200
        return max(1, minutes)