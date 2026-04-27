from django.urls import path
from memorybot import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('', views.chat_view, name='chat'),
    path('send/', views.send_message_view, name='send_message'),
]