from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
import uuid
from django.views.decorators.csrf import csrf_exempt
from .models import ChatSession, ChatMessage
from .bot_brain import SimpleChatbot

# View 1: Registration
def register_view(request):
    """New user register panna"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check: Username already irukka?
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already taken!'
            })
        
        # Create new user
        user = User.objects.create_user(username=username, password=password)
        
        # Auto login pannunga
        login(request, user)
        
        return redirect('chat')
    
    return render(request, 'register.html')

# View 2: Login
def login_view(request):
    """Existing user login panna"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('chat')
        else:
            return render(request, 'login.html', {
                'error': 'Invalid username or password!'
            })
    
    return render(request, 'login.html')

# View 3: Main Chat Page
@login_required
def chat_view(request):
    """Chat interface"""
    # Current user oda active session get pannunga
    session = ChatSession.objects.filter(user=request.user).first()
    
    # Session illa na create pannunga
    if not session:
        session = ChatSession.objects.create(
            user=request.user,
            title=f"Chat - {request.user.username}"
        )
    
    # Session la ulla messages get pannunga
    messages = ChatMessage.objects.filter(session=session)
    
    return render(request, 'chat.html', {
        'session': session,
        'messages': messages,
    })

# View 4: Send Message (AJAX)
@login_required
@csrf_exempt
def send_message_view(request):
    """User message save panni, bot response generate pannudum"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        user_message = request.POST.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)
        
        # Session get pannunga
        session = ChatSession.objects.get(id=session_id, user=request.user)
        
        # 1. User message save pannunga
        user_msg = ChatMessage.objects.create(
            session=session,
            is_bot=False,
            content=user_message
        )
        
        # 2. Bot response generate pannunga
        chatbot = SimpleChatbot(request.user, session)
        bot_response = chatbot.get_response(user_message)
        
        # 3. Bot message save pannunga
        bot_msg = ChatMessage.objects.create(
            session=session,
            is_bot=True,
            content=bot_response
        )
        
        # 4. Return JSON response
        return JsonResponse({
            'status': 'success',
            'user_message': {
                'content': user_msg.content,
                'time': user_msg.timestamp.strftime('%H:%M')
            },
            'bot_message': {
                'content': bot_msg.content,
                'time': bot_msg.timestamp.strftime('%H:%M')
            }
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)