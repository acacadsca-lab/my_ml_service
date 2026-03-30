from django.contrib import admin
from django.urls import path
from chatapp.views import AudioProcessView, ImagegenView, IndexView, VoiceCloneqwenView, chat_with_pdf, codegeneratorView, VoiceCloneView, delete_document, get_chat_history, pdf_chat_home, pdf_detail, upload_pdf
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', IndexView.as_view(),name="index"),
    path('ai_image_gen/', ImagegenView.as_view(),name="ai_image_gen"),
    path('code_generator/', codegeneratorView.as_view(),name="code_generator"),
    path('voice_clone/', VoiceCloneView.as_view(),name="voice_clone"),
    path('qwen_clone/', VoiceCloneqwenView.as_view(), name='qwen_clone'),
    path('chatbot/', codegeneratorView.as_view(),name="chatbot"),


    path('pdf_chat/', pdf_chat_home, name='pdf_chat_home'),
    path('pdf/<int:doc_id>/', pdf_detail, name='pdf_detail'),
    
    # POST - API endpoints
    path('api/upload/', upload_pdf, name='upload_pdf'),
    path('api/chat/', chat_with_pdf, name='chat_pdf'),
    path('api/delete/<int:doc_id>/', delete_document, name='delete_document'),
    
    # GET - API endpoints
    path('api/history/<int:doc_id>/', get_chat_history, name='chat_history'),
    path("process_audio/", AudioProcessView.as_view(), name='process_audio'),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)