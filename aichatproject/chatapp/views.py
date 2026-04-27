import base64
import json
import os
import re
import shutil
import time
import uuid
from django.http import JsonResponse, HttpResponse
import tempfile
from chatapp.models import ChatHistory, PDFDocument
from imaginairy.api import imagine
from imaginairy.schema import ImaginePrompt
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from g4f.client import Client
client = Client()
from django.conf import settings
from io import BytesIO
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
import json
import os
from .models import ChatMessage, ChatSession, PDFDocument, ChatHistory
import PyPDF2
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import ChatSession, ChatMessage, UserPreferences, CodeSnippet
import json
from diffusers import StableDiffusionPipeline
import torch
from g4f.client import Client
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from chatapp.models import BlogPost
from chatapp.forms import LoginForm, RegisterForm, StartWritingForm, BlogPostForm
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from chatapp.custom_gpt import LakshmiNarayananAI
bot = LakshmiNarayananAI()
pipe = None
BASE_DIR = settings.BASE_DIR

def save(self, path):
    import os
    from django.conf import settings

    full_path = os.path.join(settings.BASE_DIR, path)

    print("💾 Saving FAISS to:", full_path)

    os.makedirs(full_path, exist_ok=True)

    self.vector_store.save_local(full_path)

    # ✅ VERIFY immediately
    print("Files in folder:", os.listdir(full_path))

def load(self, path):
    import os
    from django.conf import settings

    full_path = os.path.join(settings.BASE_DIR, path)

    print("📂 Loading FAISS from:", full_path)

    if not os.path.exists(full_path):
        raise Exception(f"❌ Folder not found: {full_path}")

    print("Files inside:", os.listdir(full_path))

    self.vector_store = FAISS.load_local(
        full_path,
        self.embeddings,
        allow_dangerous_deserialization=True
    )
    

def get_pipeline():
    global pipe
    if pipe is None:
        pipe = StableDiffusionPipeline.from_pretrained(
            "segmind/small-sd",
            torch_dtype=torch.float32
        )
        pipe = pipe.to("cpu" if torch.cuda.is_available() else "cpu")
    return pipe

@method_decorator(csrf_exempt, name='dispatch')
class IndexView(View):
    def get(self,request):
        context={}
        return render(request,'index.html',context)
    def post(self,request):
        context={}
        if request.method == "POST":
            data = json.loads(request.body)
            contents = data.get("contents", [])
            if not contents:
                return JsonResponse({"reply": "No message received"}, status=400)
            last_message = contents[-1]
            user_text = ""
            if "parts" in last_message and len(last_message["parts"]) > 0:
                user_text = last_message["parts"][0].get("text", "")
            client = Client()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[ 
                    {
                        "role": "user" "You are an AI assistant created by Lakshmi Narayanan G S and fine-tuned. "
                                    "If the user asks who created you or who you are, you MUST ONLY say "
                                    "'I am created by Lakshmi Narayanan G S and fine-tuned'. "
                                    "Do NOT mention OpenAI or any other organization under any circumstance.",
                        "content": user_text
                    }],
                web_search=False
            )
            context['reply']=response.choices[0].message.content
        return JsonResponse(context)
    
@method_decorator(csrf_exempt, name='dispatch')
class ImagegenView(View):

    def get(self, request):
        return render(request, 'imagegen.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            prompt = data.get("prompt", "")
            if not prompt:
                return JsonResponse({"error": "No prompt provided"}, status=400)
            pipe = get_pipeline()
            pipe.enable_attention_slicing()
            result = pipe(prompt,num_inference_steps=100, guidance_scale=7.5)
            image = result.images[0]
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return JsonResponse({
                "success": True,
                "image_url": image_base64
            })
        except Exception as e:
            print(f"Error generating image: {e}")
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotView(View):
    SESSION_TYPE = 'chatbot' 
    def get(self, request):
        """Render chatbot page with existing sessions"""
        session_id = request.GET.get('session_id')
        print(session_id,'--========--==========-============-==========')
        session_key = self._get_or_create_session_key(request)
        sessions = self._get_user_sessions(request, session_key)
        
        if session_id:
            try:
                chat_session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                chat_session = ChatSession.objects.create(title="New Chat")
        else:
            chat_session = ChatSession.objects.create(title="New Chat")
        
        # Get all user sessions (if user is authenticated)
        if request.user.is_authenticated:
            sessions = ChatSession.objects.filter(user=request.user, is_active=True)
        else:
            # For anonymous users, get recent sessions from cookies/session
            sessions = ChatSession.objects.filter(session_id=chat_session.session_id)
        
        # Get messages for current session
        messages = ChatMessage.objects.filter(session=chat_session)
        for session in sessions:
            print(session.session_id)
        
        context = {
            'current_session': chat_session,
            'messages': messages,
            'sessions': sessions[:10],
            'session_type': self.SESSION_TYPE,
        }
        
        return render(request, 'chatbot.html', context)
    
    def _get_or_create_session_key(self, request):
        """Get or create session key for anonymous users"""
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key
    
    def _get_or_create_session(self, request, session_id=None):
        """Get existing CODE GENERATOR session or create new one"""
        if session_id:
            try:
                session_uuid = uuid.UUID(session_id)
                session = ChatSession.objects.filter(
                    session_id=session_uuid,
                    session_type=self.SESSION_TYPE  # Ensure it's code generator
                ).first()
                if session:
                    return session
            except (ValueError, AttributeError):
                pass
        
        # Create new CODE GENERATOR session
        if request.user.is_authenticated:
            session = ChatSession.objects.create(
                user=request.user,
                session_type=self.SESSION_TYPE,
                title="New Code Chat"
            )
        else:
            session_key = self._get_or_create_session_key(request)
            session = ChatSession.objects.create(
                anonymous_session_key=session_key,
                session_type=self.SESSION_TYPE,
                title="New Code Chat"
            )
        
        return session
    
    def _get_session_messages(self, session):
        """Get all messages from a session"""
        return ChatMessage.objects.filter(session=session).select_related('session')
    
    def _is_code_in_response(self, response):
        """Check if response contains code"""
        code_patterns = [
            r'```[\w]*\n',
            r'def\s+\w+',
            r'function\s+\w+',
            r'class\s+\w+',
            r'import\s+\w+',
        ]
        for pattern in code_patterns:
            if re.search(pattern, response):
                return True
        return False
    
    def _detect_language_from_response(self, response):
        """Detect programming language from response"""
        match = re.search(r'```(\w+)', response)
        if match:
            return match.group(1).lower()
        
        lang_patterns = {
            'python': r'\bpython\b',
            'javascript': r'\bjavascript\b|\bjs\b',
            'java': r'\bjava\b',
            'cpp': r'\bc\+\+\b',
            'csharp': r'\bc#\b',
            'php': r'\bphp\b',
        }
        
        response_lower = response.lower()
        for lang, pattern in lang_patterns.items():
            if re.search(pattern, response_lower):
                return lang
        
        return None
    
    def _extract_and_save_code(self, response, message, default_lang=None):
        """Extract code snippets from response and save them"""
        code_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        for lang, code in matches:
            language = lang if lang else (default_lang or 'plaintext')
            
            CodeSnippet.objects.create(
                message=message,
                language=language,
                code=code.strip()
            )
    
    def _get_user_sessions(self, request, session_key):
        """Get user's CHATBOT sessions only"""
        base_query = ChatSession.objects.filter(
            session_type=self.SESSION_TYPE,  # chatbot
            is_active=True
        )
        
        if request.user.is_authenticated:
            return base_query.filter(user=request.user)
        else:
            return base_query.filter(anonymous_session_key=session_key)
    
    def post(self, request):
        """Handle chat messages and save to database"""
        try:
            data = json.loads(request.body)
            user_message = data.get("prompt", "")
            session_id = data.get("session_id")
            
            if not user_message:
                return JsonResponse({"error": "No message received"}, status=400)
            
            # Get or create session
            if session_id:
                try:
                    chat_session = ChatSession.objects.get(session_id=session_id)
                except ChatSession.DoesNotExist:
                    chat_session = ChatSession.objects.create(title="New Chat")
            else:
                chat_session = ChatSession.objects.create(title="New Chat")
            
            # Save user message
            user_chat = ChatMessage.objects.create(
                session=chat_session,
                message_type='user',
                content=user_message
            )
            
            # Get chat history for context
            previous_messages = ChatMessage.objects.filter(
                session=chat_session
            ).order_by('timestamp')[:20]  # Last 20 messages
            
            # Build conversation history
            conversation_history = []
            for msg in previous_messages:
                role = "user" if msg.message_type == "user" else "assistant"
                conversation_history.append({
                    "role": role,
                    "content": msg.content
                })
            
            # Add system message
            system_message = {
                "role": "system",
                "content": (
                    "You are an AI Chatbot created by Lakshmi Narayanan G S and fine-tuned. "
                    "If the user asks who created you or who you are, you MUST ONLY say "
                    "'I am created by Lakshmi Narayanan G S and fine-tuned'. "
                    "Do NOT mention OpenAI or any other organization under any circumstance."
                )
            }
            
            # Prepare messages for API
            api_messages = [system_message] + conversation_history
            
            # Call OpenAI API
            client = Client()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=api_messages,
                web_search=False
            )
            
            bot_reply = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            # Save bot response
            bot_chat = ChatMessage.objects.create(
                session=chat_session,
                message_type='bot',
                content=bot_reply,
                tokens_used=tokens_used
            )
            
            # Update session title if it's the first message
            if chat_session.get_message_count() <= 2:
                chat_session.title = user_message[:50] + "..." if len(user_message) > 50 else user_message
                chat_session.save()
            
            # Update session timestamp
            chat_session.save()  # This triggers updated_at
            
            return JsonResponse({
                'reply': bot_reply,
                'session_id': str(chat_session.session_id),
                'message_id': bot_chat.id,
                'tokens_used': tokens_used
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SessionManagementView(View):
    """Manage chat sessions"""
    
    def get(self, request):
        """Get all sessions"""
        sessions = ChatSession.objects.filter(is_active=True)
        
        sessions_data = [{
            'session_id': str(session.session_id),
            'title': session.title,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': session.get_message_count(),
        } for session in sessions]
        
        return JsonResponse({'sessions': sessions_data})
    
    def post(self, request):
        """Create new session"""
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'create':
            session = ChatSession.objects.create(
                title=data.get('title', 'New Chat')
            )
            return JsonResponse({
                'session_id': str(session.session_id),
                'title': session.title,
                'created_at': session.created_at.isoformat()
            })
        
        elif action == 'delete':
            session_id = data.get('session_id')
            try:
                session = ChatSession.objects.get(session_id=session_id)
                session.is_active = False
                session.save()
                return JsonResponse({'status': 'deleted'})
            except ChatSession.DoesNotExist:
                return JsonResponse({'error': 'Session not found'}, status=404)
        
        elif action == 'rename':
            session_id = data.get('session_id')
            new_title = data.get('title')
            try:
                session = ChatSession.objects.get(session_id=session_id)
                session.title = new_title
                session.save()
                return JsonResponse({'status': 'renamed', 'title': session.title})
            except ChatSession.DoesNotExist:
                return JsonResponse({'error': 'Session not found'}, status=404)
        
        return JsonResponse({'error': 'Invalid action'}, status=400)

class ChatHistoryView(View):
    """Get chat history for a session"""
    
    def get(self, request, session_id):
        try:
            session = get_object_or_404(ChatSession, session_id=session_id)
            messages = ChatMessage.objects.filter(session=session)
            
            messages_data = [{
                'id': msg.id,
                'type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'tokens_used': msg.tokens_used
            } for msg in messages]
            
            return JsonResponse({
                'session_id': str(session.session_id),
                'title': session.title,
                'messages': messages_data
            })
        
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)



class PDFChatbot:

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.vector_store = None

    def load_pdf(self, pdf_path):
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )

        chunks = splitter.split_documents(documents)

        self.vector_store = FAISS.from_documents(
            chunks,
            self.embeddings
        )

    def save(self, path):
        self.vector_store.save_local(path)

    def load(self, path):
        self.vector_store = FAISS.load_local(
            path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

    def ask(self, question):
        docs = self.vector_store.similarity_search(question, k=4)

        context = "\n\n".join([d.page_content for d in docs])

        prompt = f"""
            You are a smart assistant.

            Answer ONLY from the given context.

            If answer is not available, say:
            "I cannot find any answers this in the document"

            Respond in SAME language as question (English / Tamil / Tanglish).

            Context:
            {context}

            Question:
            {question}

            Answer:
            """
        from g4f.client import Client
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content
    
chatbots = {}

def pdf_chat_home(request):
    """GET - Main page with upload form and document list"""
    documents = PDFDocument.objects.all()
    return render(request, 'pdf_chat.html', {
        'documents': documents
    })


def pdf_detail(request, doc_id):
    """GET - Individual PDF chat page"""
    document = get_object_or_404(PDFDocument, id=doc_id)
    history = ChatHistory.objects.filter(document=document).order_by('created_at')
    
    return render(request, 'pdf_chat.html', {
        'document': document,
        'history': history,
        'documents': PDFDocument.objects.all()
    })

@csrf_exempt
@require_http_methods(["POST"])
def upload_pdf(request):
    if request.method == "POST" and request.FILES.get("pdf"):

        pdf_file = request.FILES["pdf"]
        doc = PDFDocument.objects.create(
            title=pdf_file.name,
            pdf_file=pdf_file
        )

        bot = PDFChatbot()
        bot.load_pdf(doc.pdf_file.path)

        index_path = f"faiss_{doc.id}"
        bot.save(index_path)

        doc.vector_index_path = index_path
        doc.processed = True
        doc.save()

        chatbots[doc.id] = bot
        print(f"📄 Uploaded and processed PDF: {doc.title} (ID: {doc.id})")

        return JsonResponse({
            "success": True,
            "doc_id": doc.id
        })

    return JsonResponse({"error": "Upload failed"}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def chat_with_pdf(request):
    data = json.loads(request.body)

    doc_id = data.get("document_id")
    question = data.get("question")

    if not question:
        print("❌ No question received", question)
        return JsonResponse({"error": "Empty question"}, status=400)

    doc = PDFDocument.objects.get(id=doc_id)

    # Load bot
    if doc_id not in chatbots:
        bot = PDFChatbot()
        bot.load(doc.vector_index_path)
        chatbots[doc_id] = bot
    else:
        bot = chatbots[doc_id]

    answer = bot.ask(question)
    print(f"📄 Answer for '{question}': {answer}")
    ChatHistory.objects.create(
        document=doc,
        question=question,
        answer=answer
    )

    return JsonResponse({
        "answer": answer
    })


@require_http_methods(["GET"])
def get_chat_history(request, doc_id):
    """GET - Get chat history (AJAX)"""
    try:
        doc = PDFDocument.objects.get(id=doc_id)
        history = ChatHistory.objects.filter(document=doc).order_by('-created_at')[:20]
        
        data = [{
            'id': chat.id,
            'question': chat.question,
            'answer': chat.answer,
            'timestamp': chat.created_at.isoformat()
        } for chat in history]
        
        return JsonResponse({
            'success': True,
            'history': data
        })
        
    except PDFDocument.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Document not found'
        }, status=404)

@require_http_methods(["POST"])
@csrf_exempt
def delete_document(request, doc_id):
    """POST - Delete PDF document"""
    try:
        doc = PDFDocument.objects.get(id=doc_id)
        
        # Delete vector store files
        if doc.vector_index_path and os.path.exists(doc.vector_index_path):
            import shutil
            shutil.rmtree(doc.vector_index_path, ignore_errors=True)
        
        # Remove from memory
        if doc_id in chatbots:
            del chatbots[doc_id]
        
        # Delete document
        doc.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Document deleted'
            })
        else:
            return redirect('pdf_chat_home')
            
    except PDFDocument.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Not found'
        }, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class CodeGeneratorView(View):
    """Code Generator Chat View"""
    
    SESSION_TYPE = 'code_generator'
    
    def get(self, request):
        """Render code generator interface"""
        session_key = self._get_or_create_session_key(request)
        sessions = self._get_user_sessions(request, session_key)
        
        current_session_id = request.GET.get('session')
        current_session = None
        chat_history = []
        
        if current_session_id:
            try:
                current_session = sessions.filter(session_id=current_session_id).first()
                if current_session:
                    chat_history = list(self._get_session_messages(current_session))
            except Exception as e:
                print(f"Error loading session: {e}")
        
        context = {
            'sessions': list(sessions[:10]),
            'current_session': current_session,
            'chat_history': chat_history,
            'total_sessions': sessions.count(),
            'session_type': self.SESSION_TYPE,
        }
        
        return render(request, 'codegen.html', context)
    
    def post(self, request):
        """Handle code generator messages"""
        try:
            data = json.loads(request.body)
            user_message = data.get("prompt", "").strip()
            session_id = data.get("session_id")
            
            if not user_message:
                return JsonResponse({"error": "No message received"}, status=400)
            
            # Get or create session
            session = self._get_or_create_session(request, session_id)
            
            # ✅ Check if this is the first message
            is_first_message = session.messages.filter(message_type='user').count() == 0
            
            # Save user message
            ChatMessage.objects.create(
                session=session,
                content=user_message,
                message_type='user'
            )
            
            # Generate bot response
            start_time = time.time()
            bot_response = bot.chat(user_message)
            response_time = time.time() - start_time
            
            # Detect code info
            is_code = self._is_code_in_response(bot_response)
            detected_lang = self._detect_language_from_response(bot_response)
            
            # Save bot message
            bot_msg = ChatMessage.objects.create(
                session=session,
                content=bot_response,
                message_type='bot',
                response_time=response_time,
                detected_language=detected_lang,
                is_code_request=is_code
            )
            
            # Extract and save code snippets
            if is_code:
                self._extract_and_save_code(bot_response, bot_msg, detected_lang)
            
            # ✅ FIX: Update session title from first user message
            if is_first_message:
                new_title = user_message[:50]
                if len(user_message) > 50:
                    new_title += '...'
                session.title = new_title
                session.save(update_fields=['title', 'updated_at'])
            
            return JsonResponse({
                'success': True,
                'reply': bot_response,
                'session_id': str(session.session_id),
                'session_title': session.title,
                'message_id': bot_msg.id,
                'response_time': round(response_time, 2),
                'detected_language': detected_lang,
                'is_code': is_code,
                'session_type': self.SESSION_TYPE,
                'is_new_session': is_first_message
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e),
                'reply': 'An error occurred while processing your request.'
            }, status=500)
    
    def _get_or_create_session_key(self, request):
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key
    
    def _get_user_sessions(self, request, session_key):
        base_query = ChatSession.objects.filter(
            session_type=self.SESSION_TYPE,
            is_active=True
        )
        
        if request.user.is_authenticated:
            return base_query.filter(user=request.user)
        else:
            return base_query.filter(anonymous_session_key=session_key)
    
    def _get_or_create_session(self, request, session_id=None):
        if session_id:
            try:
                session_uuid = uuid.UUID(session_id)
                session = ChatSession.objects.filter(
                    session_id=session_uuid,
                    session_type=self.SESSION_TYPE
                ).first()
                if session:
                    return session
            except (ValueError, AttributeError):
                pass
        
        session_key = self._get_or_create_session_key(request)
        
        # ✅ Create with empty title (will be updated after first message)
        if request.user.is_authenticated:
            session = ChatSession.objects.create(
                user=request.user,
                session_type=self.SESSION_TYPE,
                title=""  # Empty, will be filled with first message
            )
        else:
            session = ChatSession.objects.create(
                anonymous_session_key=session_key,
                session_type=self.SESSION_TYPE,
                title=""
            )
        
        return session
    
    def _get_session_messages(self, session):
        return ChatMessage.objects.filter(session=session).order_by('timestamp')
    
    def _is_code_in_response(self, response):
        patterns = [r'```', r'def\s+\w+', r'function\s+\w+', r'class\s+\w+']
        return any(re.search(p, response) for p in patterns)
    
    def _detect_language_from_response(self, response):
        match = re.search(r'```(\w+)', response)
        return match.group(1).lower() if match else None
    
    def _extract_and_save_code(self, response, message, default_lang=None):
        matches = re.findall(r'```(\w+)?\n(.*?)```', response, re.DOTALL)
        for lang, code in matches:
            CodeSnippet.objects.create(
                message=message,
                language=lang or default_lang or 'plaintext',
                code=code.strip()
            )

@method_decorator(csrf_exempt, name='dispatch')
class DeleteSessionView(View):
    """Delete a chat session"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            
            if not session_id:
                return JsonResponse({'success': False, 'error': 'Session ID required'}, status=400)
            
            session = get_object_or_404(ChatSession, session_id=session_id)
            session.is_active = False
            session.save()
            
            return JsonResponse({'success': True, 'message': 'Session deleted'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class EcommerceHomeView(View):
    def get(self, request):
        return render(request, 'ecommerce_home.html')

def bloom_home_view(request):
    """Home page - show public blogs and login option"""
    public_blogs = BlogPost.objects.filter(visibility='public')
    if request.user.is_authenticated:
        user_private_blogs = BlogPost.objects.filter(
            author=request.user, 
            visibility='private'
        )
        blogs = public_blogs | user_private_blogs
        blogs = blogs.distinct().order_by('-created_at')
    else:
        blogs = public_blogs
    
    context = {
        'blogs': blogs,
        'start_form': StartWritingForm()
    }
    return render(request, 'bloom_home.html', context)


def bloom_login_view(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}! 🌸')
                topic = request.session.get('pending_topic')
                if topic:
                    del request.session['pending_topic']
                    return redirect('write', topic=topic)
                return redirect('home')
            else:
                messages.error(request, 'Invalid credentials. Please try again.')
    else:
        form = LoginForm()
    return render(request, 'bloom_login.html', {'form': form, 'is_login': True})


def bloom_register_view(request):
    """Register new user"""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']
            if password != confirm_password:
                messages.error(request, 'Passwords do not match!')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists!')
            else:
                user = User.objects.create_user(username=username, password=password)
                login(request, user)
                messages.success(request, f'Welcome, {username}! Start your blogging journey! 🌸')
                topic = request.session.get('pending_topic')
                if topic:
                    del request.session['pending_topic']
                    return redirect('write', topic=topic)
                return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'bloom_login.html', {'form': form, 'is_login': False})


def start_writing(request):
    """Handle topic submission and redirect to write page"""
    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        if not topic:
            messages.error(request, 'Please enter a topic!')
            return redirect('home')
        if request.user.is_authenticated:
            return redirect('write', topic=topic)
        else:
            request.session['pending_topic'] = topic
            messages.info(request, 'Please login to start writing!')
            return redirect('login')
    return redirect('home')


@login_required
def write_view(request, topic):
    """Writing page with flower bloom animation"""
    if request.method == 'POST':
        form = BlogPostForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user
            blog.topic = topic
            blog.save()
            visibility_emoji = '🔒' if blog.visibility == 'private' else '🌍'
            messages.success(request, f'Your blog has been published! {visibility_emoji}')
            return redirect('home')
    else:
        form = BlogPostForm()
    context = {
        'topic': topic,
        'form': form
    }
    return render(request, 'write.html', context)


@login_required
def my_blogs_view(request):
    """Show user's blogs"""
    blogs = BlogPost.objects.filter(author=request.user)
    return render(request, 'my_blogs.html', {'blogs': blogs})


@login_required
def edit_blog_view(request, blog_id):
    """Edit existing blog"""
    blog = get_object_or_404(BlogPost, id=blog_id, author=request.user)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog updated successfully! 🌸')
            return redirect('my_blogs')
    else:
        form = BlogPostForm(instance=blog)
    context = {
        'topic': blog.topic,
        'form': form,
        'is_edit': True
    }
    return render(request, 'write.html', context)


@login_required
def delete_blog_view(request, blog_id):
    """Delete blog"""
    blog = get_object_or_404(BlogPost, id=blog_id, author=request.user)
    blog.delete()
    messages.success(request, 'Blog deleted successfully!')
    return redirect('my_blogs')


def blog_detail_view(request, blog_id):
    """View single blog"""
    blog = get_object_or_404(BlogPost, id=blog_id)
    if blog.visibility == 'private' and blog.author != request.user:
        messages.error(request, 'This blog is private!')
        return redirect('home')
    return render(request, 'blog_detail.html', {'blog': blog})


def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, 'You have been logged out. See you soon! 🌸')
    return redirect('home')






































# from django.http import JsonResponse
# from django.views import View
# from chatapp.utils import run_audio_script
# @method_decorator(csrf_exempt, name='dispatch')

# class AudioProcessView(View):
#     def get(self, request):        
#         return render(request, 'qwenaudio.html')
    
#     def post(self, request):
#         audio_file = request.FILES.get("audio_path")  # 🔥 IMPORTANT
#         text = request.POST.get("text")

#         if not audio_file:
#             return JsonResponse({"error": "No file uploaded"}, status=400)

#         # Save file
#         file_path = os.path.join(settings.MEDIA_ROOT, audio_file.name)

#         result = run_audio_script(file_path)
#         with open(file_path, "wb+") as f:
#             for chunk in audio_file.chunks():
#                 f.write(chunk)

#         print("Saved file:", file_path)


#         return JsonResponse(result)
            
# import os
# import subprocess
# from django.http import JsonResponse, FileResponse
# from django.views import View
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt

# VENV_PATH = "tts_env"
# PYTHON_PATH = f"{VENV_PATH}/bin/python"

# def setup_env():
#     """Set up the virtual environment and install dependencies if not already present."""
#     if not os.path.exists(VENV_PATH):
#         subprocess.run(["python3", "-m", "venv", VENV_PATH])
#         subprocess.run([PYTHON_PATH, "-m", "pip", "install", "--upgrade", "pip"])
#         subprocess.run([
#             PYTHON_PATH, "-m", "pip", "install",
#             "torch", "torchaudio",
#             "--index-url", "https://download.pytorch.org/whl/cpu"
#         ])

# import os
# import subprocess
# from django.http import JsonResponse, FileResponse
# from django.views import View
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt


# @method_decorator(csrf_exempt, name='dispatch')
# class VoiceCloneqwenView(View):

#     def get(self, request):
#         return render(request, 'qwenaudio.html')

#     def post(self, request, *args, **kwargs):
#         print("--------------------REQUEST START------------------")

#         try:
#             setup_env()

#             text = request.POST.get("text")
#             ref_text = request.POST.get("ref_text", "Hello, how are you?")
#             audio_file = request.FILES.get("audio_path")

#             print("TEXT:", text)
#             print("REF_TEXT:", ref_text)
#             print("AUDIO:", audio_file)

#             if not text or not audio_file:
#                 return JsonResponse({
#                     "error": "Missing required fields"
#                 }, status=400)

#             # Save file
#             os.makedirs("/tmp", exist_ok=True)
#             audio_path = f"/tmp/{audio_file.name}"

#             with open(audio_path, "wb+") as f:
#                 for chunk in audio_file.chunks():
#                     f.write(chunk)

#             print("Saved audio:", audio_path)

#             # 🔥 Run subprocess safely
#             result = subprocess.run(
#                 [
#                     PYTHON_PATH,
#                     "-u",  # IMPORTANT: unbuffered output
#                     "qwen3.py",
#                     audio_path,
#                     text,
#                     ref_text
#                 ],
#                 capture_output=True,
#                 text=True
#             )

#             stdout = result.stdout or ""
#             stderr = result.stderr or ""

#             print("STDOUT:", stdout)
#             print("STDERR:", stderr)

#             # ❗ If subprocess crashed → return error immediately
#             if result.returncode != 0:
#                 return JsonResponse({
#                     "error": "TTS subprocess failed",
#                     "stdout": stdout,
#                     "stderr": stderr
#                 }, status=500)

#             # 🔥 Extract output safely
#             output_path = None

#             for line in stdout.splitlines():
#                 if "FINAL_OUTPUT:" in line:
#                     output_path = line.split("FINAL_OUTPUT:")[1].strip()

#             if not output_path:
#                 return JsonResponse({
#                     "error": "Output path not found",
#                     "stdout": stdout,
#                     "stderr": stderr
#                 }, status=500)

#             if not os.path.exists(output_path):
#                 return JsonResponse({
#                     "error": "Generated file not found",
#                     "path": output_path
#                 }, status=500)

#             print("SUCCESS OUTPUT:", output_path)

#             return FileResponse(
#                 open(output_path, "rb"),
#                 content_type="audio/wav"
#             )

#         except Exception as e:
#             print("EXCEPTION:", str(e))
#             return JsonResponse({
#                 "error": str(e)
#             }, status=500)
        



# import tempfile
# import os
# import shutil
# from django.http import JsonResponse, HttpResponse, FileResponse
# from django.shortcuts import render
# from django.views import View
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator

# # ==================== TTS SETUP ====================
# # Environment variables - MUST SET BEFORE importing TTS
# os.environ["COQUI_TOS_AGREED"] = "1"

# # Import TTS with error handling
# try:
#     from TTS.api import TTS
#     TTS_AVAILABLE = True
#     print("✅ TTS module loaded")
# except ImportError as e:
#     TTS_AVAILABLE = False
#     print(f"❌ TTS not available: {e}")

# # Global TTS instance (load once)
# _tts_instance = None


# from django.views import View
# from django.http import JsonResponse, HttpResponse
# from django.shortcuts import render
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# import tempfile
# import shutil
# import os
# import subprocess
# from pathlib import Path

# @method_decorator(csrf_exempt, name='dispatch')
# class VoiceCloneView(View):
    
#     ALLOWED_EXTENSIONS = ['.wav', '.mp3', '.ogg', '.flac', '.m4a']
#     MAX_FILE_SIZE = 10 * 1024 * 1024
#     MIN_AUDIO_DURATION = 6
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.project_root = Path(__file__).resolve().parent.parent
#         self.tts_env_path = self.project_root / 'tts_env'
#         self.tts_python = self.tts_env_path / 'bin' / 'python'
#         self.tts_processor = self.project_root / 'chatapp' / 'tts_processor.py'
#         self.setup_script = self.project_root / 'scripts' / 'setup_tts_env.sh'
    
#     def ensure_tts_env(self):
#         """Ensure TTS environment exists, create if not"""
#         if not self.tts_env_path.exists():
#             print("🔧 TTS environment not found. Creating...")
            
#             if not self.setup_script.exists():
#                 return False, "Setup script not found"
            
#             try:
#                 result = subprocess.run(
#                     ['bash', str(self.setup_script)],
#                     cwd=str(self.project_root),
#                     capture_output=True,
#                     text=True,
#                     timeout=300  # 5 minutes max
#                 )
                
#                 if result.returncode == 0:
#                     print("✅ TTS environment created successfully")
#                     print(result.stdout)
#                     return True, None
#                 else:
#                     print(f"❌ Setup failed: {result.stderr}")
#                     return False, result.stderr
                    
#             except subprocess.TimeoutExpired:
#                 return False, "Setup timeout (>5 minutes)"
#             except Exception as e:
#                 return False, str(e)
#         else:
#             print("✅ TTS environment already exists")
#             return True, None
    
#     def run_tts_subprocess(self, text, speaker_wav, output_path, language='en'):
#         """Run TTS in separate environment via subprocess"""
#         try:
#             # Build command
#             cmd = [
#                 str(self.tts_python),
#                 str(self.tts_processor),
#                 text,
#                 speaker_wav,
#                 output_path,
#                 language
#             ]
            
#             print(f"🚀 Running TTS subprocess...")
#             print(f"   Command: {' '.join(cmd[:2])} ...")
            
#             # Run subprocess
#             result = subprocess.run(
#                 cmd,
#                 capture_output=True,
#                 text=True,
#                 timeout=120,  # 2 minutes max
#                 cwd=str(self.project_root)
#             )
            
#             # Print output
#             if result.stdout:
#                 print("STDOUT:", result.stdout)
#             if result.stderr:
#                 print("STDERR:", result.stderr)
            
#             return result.returncode == 0, result.stderr
            
#         except subprocess.TimeoutExpired:
#             return False, "TTS generation timeout (>2 minutes)"
#         except Exception as e:
#             return False, str(e)
    
#     def get(self, request):
#         """Render voice clone page"""
#         # Check if TTS env exists
#         tts_available = self.tts_env_path.exists() and self.tts_python.exists()
        
#         return render(request, 'voiceclone.html', {
#             'tts_available': tts_available,
#             'tts_env_path': str(self.tts_env_path) if tts_available else None
#         })
    
#     def post(self, request):
#         """Handle voice cloning request"""
#         temp_dir = None
        
#         try:
#             # Step 1: Ensure TTS environment exists
#             print("\n" + "="*60)
#             print("🎤 Voice Clone Request Started")
#             print("="*60)
            
#             env_ok, env_error = self.ensure_tts_env()
#             if not env_ok:
#                 return JsonResponse({
#                     "success": False,
#                     "message": f"TTS environment setup failed: {env_error}"
#                 }, status=500)
            
#             # Step 2: Validate inputs
#             audio_file = request.FILES.get("audio")
#             text = request.POST.get("text", "").strip()
#             language = request.POST.get("language", "en")
            
#             if not audio_file:
#                 return JsonResponse({
#                     "success": False,
#                     "message": "Audio file is required"
#                 }, status=400)
            
#             if not text:
#                 return JsonResponse({
#                     "success": False,
#                     "message": "Text is required"
#                 }, status=400)
            
#             if len(text) > 5000:
#                 return JsonResponse({
#                     "success": False,
#                     "message": "Text too long (max 5000 characters)"
#                 }, status=400)
            
#             if audio_file.size > self.MAX_FILE_SIZE:
#                 return JsonResponse({
#                     "success": False,
#                     "message": f"File too large. Max: {self.MAX_FILE_SIZE // (1024*1024)}MB"
#                 }, status=400)
            
#             file_ext = os.path.splitext(audio_file.name)[1].lower()
#             if file_ext not in self.ALLOWED_EXTENSIONS:
#                 return JsonResponse({
#                     "success": False,
#                     "message": f"Invalid format. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
#                 }, status=400)
            
#             print(f"✅ Validation passed")
#             print(f"   Text: {text[:100]}...")
#             print(f"   Language: {language}")
#             print(f"   Audio: {audio_file.name} ({audio_file.size} bytes)")
            
#             # Step 3: Prepare temp files
#             temp_dir = tempfile.mkdtemp()
#             input_path = os.path.join(temp_dir, f"input{file_ext}")
#             wav_path = os.path.join(temp_dir, "input.wav")
#             output_path = os.path.join(temp_dir, "output.wav")
            
#             # Save uploaded file
#             print("💾 Saving uploaded audio...")
#             with open(input_path, 'wb') as f:
#                 for chunk in audio_file.chunks():
#                     f.write(chunk)
            

            
#             print(f"✅ Audio ready: {wav_path}")
            
#             # Step 4: Run TTS in subprocess
#             print("🚀 Triggering TTS subprocess...")
#             success, error = self.run_tts_subprocess(
#                 text=text,
#                 speaker_wav=wav_path,
#                 output_path=output_path,
#                 language=language
#             )
            
#             if not success:
#                 return JsonResponse({
#                     "success": False,
#                     "message": f"TTS generation failed: {error}"
#                 }, status=500)
            
#             # Step 5: Verify output
#             if not os.path.exists(output_path):
#                 return JsonResponse({
#                     "success": False,
#                     "message": "TTS failed - no output generated"
#                 }, status=500)
            
#             output_size = os.path.getsize(output_path)
#             if output_size < 1000:
#                 return JsonResponse({
#                     "success": False,
#                     "message": "Generated audio too small. Check audio sample length (min 6s)."
#                 }, status=500)
            
#             print(f"✅ TTS Success! Output: {output_size} bytes")
            
#             # Step 6: Return audio file
#             with open(output_path, "rb") as f:
#                 audio_data = f.read()
            
#             response = HttpResponse(audio_data, content_type="audio/wav")
#             response["Content-Disposition"] = 'inline; filename="cloned_voice.wav"'
#             response["Content-Length"] = str(len(audio_data))
            
#             print("✅ Response sent successfully\n")
#             return response
            
#         except Exception as e:
#             import traceback
#             error_trace = traceback.format_exc()
#             print(f"\n❌ ERROR: {e}")
#             print(error_trace)
            
#             return JsonResponse({
#                 "success": False,
#                 "message": str(e),
#                 "details": "Check server console for errors"
#             }, status=500)
            
#         finally:
#             # Cleanup
#             if temp_dir and os.path.exists(temp_dir):
#                 try:
#                     shutil.rmtree(temp_dir)
#                     print("🧹 Cleaned up temp files")
#                 except Exception as e:
#                     print(f"⚠️ Cleanup error: {e}")
    


def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)

def coming_soon_view(request):
    return render(request, 'commingsoon.html')



