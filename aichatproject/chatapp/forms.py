from django import forms
from django.contrib.auth.models import User
from .models import BlogPost

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your name',
            'class': 'form-input'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-input'
        })
    )

class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose a username',
            'class': 'form-input'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create password',
            'class': 'form-input'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'form-input'
        })
    )

class StartWritingForm(forms.Form):
    topic = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'What would you like to write about?',
            'class': 'form-input topic-input'
        })
    )

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['content', 'visibility']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': 'Let your thoughts flow...',
                'class': 'blog-textarea',
                'rows': 15
            }),
            'visibility': forms.RadioSelect(attrs={
                'class': 'visibility-radio'
            })
        }