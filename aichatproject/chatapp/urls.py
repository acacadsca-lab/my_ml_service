from django.contrib import admin
from django.urls import path
from chatapp import views
from chatapp.views import  ChatHistoryView, DeleteSessionView, EcommerceHomeView, ImagegenView, IndexView, SessionManagementView, chat_with_pdf, ChatbotView, CodeGeneratorView,  delete_document, get_chat_history, pdf_chat_home, pdf_detail, upload_pdf
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', IndexView.as_view(),name="index"),
    path('ai_image_gen/', ImagegenView.as_view(),name="ai_image_gen"),
    path('code_generator/', CodeGeneratorView.as_view(),name="code_generator"),
    # path('voice_clone/', VoiceCloneView.as_view(),name="voice_clone"),
    # path('qwen_clone/', VoiceCloneqwenView.as_view(), name='qwen_clone'),  EcommerceHomeView
    path('ecommerce_home/', EcommerceHomeView.as_view(),name="ecommerce_home"),
    path('chatbot/', ChatbotView.as_view(),name="chatbot"),
    path('api/sessions/', SessionManagementView.as_view(), name='session_management'),
    path('api/chat-history/<uuid:session_id>/', ChatHistoryView.as_view(), name='chat_history'),
        path('api/delete_session/', DeleteSessionView.as_view(), name='delete_session'),


    path('pdf_chat/', pdf_chat_home, name='pdf_chat_home'),
    path('pdf/<int:doc_id>/', pdf_detail, name='pdf_detail'),
    
    # POST - API endpoints
    path('api/upload/', upload_pdf, name='upload_pdf'),
    path('api/chat/', chat_with_pdf, name='chat_pdf'),
    path('api/delete/<int:doc_id>/', delete_document, name='delete_document'),
    
    # GET - API endpoints
    path('api/history/<int:doc_id>/', get_chat_history, name='chat_history'),
     path('coming_soon/', views.coming_soon_view, name='coming_soon'),
    # path("process_audio/", AudioProcessView.as_view(), name='process_audio'),

    #Blog URLs
    path('blog/', views.bloom_home_view, name='home'),
    path('blog/login/', views.bloom_login_view, name='login'),
    path('blog/register/', views.bloom_register_view, name='register'),
    path('blog/logout/', views.logout_view, name='logout'),
    path('blog/start-writing/', views.start_writing, name='start_writing'),
    path('blog/write/<str:topic>/', views.write_view, name='write'),
    path('blog/my-blogs/', views.my_blogs_view, name='my_blogs'),
    path('blog/edit/<int:blog_id>/', views.edit_blog_view, name='edit_blog'),
    path('blog/delete/<int:blog_id>/', views.delete_blog_view, name='delete_blog'),
    path('blog/<int:blog_id>/', views.blog_detail_view, name='blog_detail'),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'chatapp.views.page_not_found_view'