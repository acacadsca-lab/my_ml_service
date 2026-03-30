import base64
import json
import os
import shutil
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
from django.conf import settings
from io import BytesIO
import subprocess
from chatapp.custom_gpt import LakshmiNarayananAI
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
import json
import os
from .models import PDFDocument, ChatHistory
import PyPDF2

from g4f.client import Client

bot = LakshmiNarayananAI()


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
        data = json.loads(request.body)
        prompt = data.get("prompt", "")
        if not prompt:
            return JsonResponse({"error": "No prompt provided"}, status=400)
        try:
            result = imagine(ImaginePrompt(prompt))
            img = next(result).img
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return JsonResponse({
                "success": True,
                "image_url":image_base64
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class codegeneratorView(View):
    def get(self,request):
        context={}
        return render(request,'codegen.html',context)
    def post(self,request):
        context={}
        if request.method == "POST":
            data = json.loads(request.body)
            contents = data.get("prompt", [])
            if not contents:
                return JsonResponse({"reply": "No message received"}, status=400)
            response=bot.chat(contents)
            context['reply']=response
        return JsonResponse(context)
    



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


from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import tempfile
import shutil
import os
import subprocess
from pathlib import Path

@method_decorator(csrf_exempt, name='dispatch')
class VoiceCloneView(View):
    
    ALLOWED_EXTENSIONS = ['.wav', '.mp3', '.ogg', '.flac', '.m4a']
    MAX_FILE_SIZE = 10 * 1024 * 1024
    MIN_AUDIO_DURATION = 6
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_root = Path(__file__).resolve().parent.parent
        self.tts_env_path = self.project_root / 'tts_env'
        self.tts_python = self.tts_env_path / 'bin' / 'python'
        self.tts_processor = self.project_root / 'chatapp' / 'tts_processor.py'
        self.setup_script = self.project_root / 'scripts' / 'setup_tts_env.sh'
    
    def ensure_tts_env(self):
        """Ensure TTS environment exists, create if not"""
        if not self.tts_env_path.exists():
            print("🔧 TTS environment not found. Creating...")
            
            if not self.setup_script.exists():
                return False, "Setup script not found"
            
            try:
                result = subprocess.run(
                    ['bash', str(self.setup_script)],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes max
                )
                
                if result.returncode == 0:
                    print("✅ TTS environment created successfully")
                    print(result.stdout)
                    return True, None
                else:
                    print(f"❌ Setup failed: {result.stderr}")
                    return False, result.stderr
                    
            except subprocess.TimeoutExpired:
                return False, "Setup timeout (>5 minutes)"
            except Exception as e:
                return False, str(e)
        else:
            print("✅ TTS environment already exists")
            return True, None
    
    def run_tts_subprocess(self, text, speaker_wav, output_path, language='en'):
        """Run TTS in separate environment via subprocess"""
        try:
            # Build command
            cmd = [
                str(self.tts_python),
                str(self.tts_processor),
                text,
                speaker_wav,
                output_path,
                language
            ]
            
            print(f"🚀 Running TTS subprocess...")
            print(f"   Command: {' '.join(cmd[:2])} ...")
            
            # Run subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes max
                cwd=str(self.project_root)
            )
            
            # Print output
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            return result.returncode == 0, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "TTS generation timeout (>2 minutes)"
        except Exception as e:
            return False, str(e)
    
    def get(self, request):
        """Render voice clone page"""
        # Check if TTS env exists
        tts_available = self.tts_env_path.exists() and self.tts_python.exists()
        
        return render(request, 'voiceclone.html', {
            'tts_available': tts_available,
            'tts_env_path': str(self.tts_env_path) if tts_available else None
        })
    
    def post(self, request):
        """Handle voice cloning request"""
        temp_dir = None
        
        try:
            # Step 1: Ensure TTS environment exists
            print("\n" + "="*60)
            print("🎤 Voice Clone Request Started")
            print("="*60)
            
            env_ok, env_error = self.ensure_tts_env()
            if not env_ok:
                return JsonResponse({
                    "success": False,
                    "message": f"TTS environment setup failed: {env_error}"
                }, status=500)
            
            # Step 2: Validate inputs
            audio_file = request.FILES.get("audio")
            text = request.POST.get("text", "").strip()
            language = request.POST.get("language", "en")
            
            if not audio_file:
                return JsonResponse({
                    "success": False,
                    "message": "Audio file is required"
                }, status=400)
            
            if not text:
                return JsonResponse({
                    "success": False,
                    "message": "Text is required"
                }, status=400)
            
            if len(text) > 5000:
                return JsonResponse({
                    "success": False,
                    "message": "Text too long (max 5000 characters)"
                }, status=400)
            
            if audio_file.size > self.MAX_FILE_SIZE:
                return JsonResponse({
                    "success": False,
                    "message": f"File too large. Max: {self.MAX_FILE_SIZE // (1024*1024)}MB"
                }, status=400)
            
            file_ext = os.path.splitext(audio_file.name)[1].lower()
            if file_ext not in self.ALLOWED_EXTENSIONS:
                return JsonResponse({
                    "success": False,
                    "message": f"Invalid format. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
                }, status=400)
            
            print(f"✅ Validation passed")
            print(f"   Text: {text[:100]}...")
            print(f"   Language: {language}")
            print(f"   Audio: {audio_file.name} ({audio_file.size} bytes)")
            
            # Step 3: Prepare temp files
            temp_dir = tempfile.mkdtemp()
            input_path = os.path.join(temp_dir, f"input{file_ext}")
            wav_path = os.path.join(temp_dir, "input.wav")
            output_path = os.path.join(temp_dir, "output.wav")
            
            # Save uploaded file
            print("💾 Saving uploaded audio...")
            with open(input_path, 'wb') as f:
                for chunk in audio_file.chunks():
                    f.write(chunk)
            

            
            print(f"✅ Audio ready: {wav_path}")
            
            # Step 4: Run TTS in subprocess
            print("🚀 Triggering TTS subprocess...")
            success, error = self.run_tts_subprocess(
                text=text,
                speaker_wav=wav_path,
                output_path=output_path,
                language=language
            )
            
            if not success:
                return JsonResponse({
                    "success": False,
                    "message": f"TTS generation failed: {error}"
                }, status=500)
            
            # Step 5: Verify output
            if not os.path.exists(output_path):
                return JsonResponse({
                    "success": False,
                    "message": "TTS failed - no output generated"
                }, status=500)
            
            output_size = os.path.getsize(output_path)
            if output_size < 1000:
                return JsonResponse({
                    "success": False,
                    "message": "Generated audio too small. Check audio sample length (min 6s)."
                }, status=500)
            
            print(f"✅ TTS Success! Output: {output_size} bytes")
            
            # Step 6: Return audio file
            with open(output_path, "rb") as f:
                audio_data = f.read()
            
            response = HttpResponse(audio_data, content_type="audio/wav")
            response["Content-Disposition"] = 'inline; filename="cloned_voice.wav"'
            response["Content-Length"] = str(len(audio_data))
            
            print("✅ Response sent successfully\n")
            return response
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"\n❌ ERROR: {e}")
            print(error_trace)
            
            return JsonResponse({
                "success": False,
                "message": str(e),
                "details": "Check server console for errors"
            }, status=500)
            
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print("🧹 Cleaned up temp files")
                except Exception as e:
                    print(f"⚠️ Cleanup error: {e}")
    
class PDFChatbot:

    def __init__(self):
        from langchain_community.embeddings import HuggingFaceEmbeddings
        self.client = Client()
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = None
        self.pdf_text = ""
        self.chunks = []
    
    def extract_text_from_pdf(self, pdf_path):
        print("📄 Extracting text from PDF...")
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"📚 Total pages: {total_pages}")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    text += page_text + "\n\n"
                    print(f"✅ Processed page {page_num}/{total_pages}")
                
                self.pdf_text = text
                print(f"✅ Extracted {len(text)} characters")
                return text
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def create_chunks(self, text, chunk_size=1000, chunk_overlap=200):
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        print(f"✂️ Splitting into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.chunks = text_splitter.split_text(text)
        print(f"✅ Created {len(self.chunks)} chunks")
        return self.chunks
    
    def create_vector_store(self):
        from langchain_community.vectorstores import FAISS
        print("🔢 Creating vector embeddings...")
        if not self.chunks:
            print("❌ No chunks found.")
            return None
        self.vector_store = FAISS.from_texts(
            texts=self.chunks,
            embedding=self.embeddings
        )
        print("✅ Vector store created!")
        return self.vector_store
    
    def save_vector_store(self, path="faiss_index"):
        if self.vector_store:
            self.vector_store.save_local(path)
            print(f"💾 Saved to {path}")
    
    def load_vector_store(self, path="faiss_index"):
        from langchain_community.vectorstores import FAISS
        try:
            self.vector_store = FAISS.load_local(
                path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"✅ Loaded from {path}")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def find_relevant_chunks(self, query, k=3):
        if not self.vector_store:
            return []
        docs = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
    
    def chat(self, user_question, max_context_length=3000):
        if not self.vector_store:
            return "❌ Please load a PDF first"
        
        print(f"🔍 Searching...")
        relevant_chunks = self.find_relevant_chunks(user_question, k=4)
        context = "\n\n---\n\n".join(relevant_chunks)
        
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."
        
        prompt = f"""
                You are a helpful AI assistant that answers questions based on PDF content.

                **CONTEXT FROM PDF:**
                {context}

                **USER QUESTION:**
                {user_question}

                **INSTRUCTIONS:**
                1. Answer based ONLY on the context
                2. If not found, say "I cannot find this in the PDF"
                3. Be accurate and concise

                **YOUR ANSWER:**
                """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                web_search=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Error: {e}"
    
    def load_pdf(self, pdf_path, save_index=True):
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return False
        self.create_chunks(text)
        self.create_vector_store()
        if save_index:
            self.save_vector_store()
        print("✅ PDF loaded!")
        return True

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
    """POST - Upload and process PDF"""
    if request.FILES.get('pdf'):
        pdf_file = request.FILES['pdf']
        title = request.POST.get('title', pdf_file.name)
        
        # Create document
        doc = PDFDocument.objects.create(
            title=title,
            pdf_file=pdf_file
        )
        
        pdf_path = doc.pdf_file.path
        index_path = f"faiss_index_{doc.id}"
        
        # Process PDF
        bot = PDFChatbot()
        success = bot.load_pdf(pdf_path, save_index=False)
        
        if success:
            bot.save_vector_store(index_path)
            doc.vector_index_path = index_path
            doc.processed = True
            doc.save()
            chatbots[doc.id] = bot
            
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'document_id': doc.id,
                    'message': 'PDF processed successfully!'
                })
            else:
                # Redirect for normal form submission
                return redirect('pdf_detail', doc_id=doc.id)
        else:
            doc.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to process PDF'
                }, status=500)
            else:
                return redirect('pdf_chat_home')
    
    return JsonResponse({'error': 'No PDF file'}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def chat_with_pdf(request):
    """POST - Chat with PDF (AJAX only)"""
    try:
        data = json.loads(request.body)
        doc_id = data.get('document_id')
        question = data.get('question')
        
        if not question:
            return JsonResponse({
                'success': False,
                'error': 'Question is required'
            }, status=400)
        
        # Get document
        doc = PDFDocument.objects.get(id=doc_id)
        
        # Get or load chatbot
        if doc_id not in chatbots:
            bot = PDFChatbot()
            if not bot.load_vector_store(doc.vector_index_path):
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to load PDF index'
                }, status=500)
            chatbots[doc_id] = bot
        else:
            bot = chatbots[doc_id]
        
        # Get answer
        answer = bot.chat(question)
        
        # Save to history
        ChatHistory.objects.create(
            document=doc,
            question=question,
            answer=answer
        )
        
        return JsonResponse({
            'success': True,
            'answer': answer
        })
        
    except PDFDocument.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Document not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
    


from django.http import JsonResponse
from django.views import View
from chatapp.utils import run_audio_script
@method_decorator(csrf_exempt, name='dispatch')

class AudioProcessView(View):
    def get(self, request):        
        return render(request, 'qwenaudio.html')
    
    def post(self, request):
        audio_file = request.FILES.get("audio_path")  # 🔥 IMPORTANT
        text = request.POST.get("text")

        if not audio_file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        # Save file
        file_path = os.path.join(settings.MEDIA_ROOT, audio_file.name)

        result = run_audio_script(file_path)
        with open(file_path, "wb+") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        print("Saved file:", file_path)


        return JsonResponse(result)
            
import os
import subprocess
from django.http import JsonResponse, FileResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

VENV_PATH = "tts_env"
PYTHON_PATH = f"{VENV_PATH}/bin/python"

def setup_env():
    """Set up the virtual environment and install dependencies if not already present."""
    if not os.path.exists(VENV_PATH):
        subprocess.run(["python3", "-m", "venv", VENV_PATH])
        subprocess.run([PYTHON_PATH, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.run([
            PYTHON_PATH, "-m", "pip", "install",
            "torch", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ])

@method_decorator(csrf_exempt, name='dispatch')
class VoiceCloneqwenView(View):
    """
    Class-based view for voice cloning.
    Accepts POST requests with text, ref_text, and audio file.
    """
    def get(self, request):        
        return render(request, 'qwenaudio.html')

    def post(self, request, *args, **kwargs):
        print("--------------------HOLA AMIGO------------------")
        try:
            # Ensure environment is set up
            print("TRY-------------------------")
            setup_env()

            # Extract POST parameters
            text = request.POST.get("text")
            print("Received text:", text)
            ref_text = request.POST.get("ref_text",'Hello, how are you?')
            print("Received ref_text:", ref_text)
            audio_file = request.FILES.get("audio_path")
            print("Received audio file:", audio_file)  

            if not all([text, ref_text, audio_file]):
                return JsonResponse(
                    {"error": "Missing required fields: text, ref_text, audio"},
                    status=400
                )

            # Save uploaded audio temporarily
            audio_path = f"/tmp/{audio_file.name}"
            print("Saving uploaded audio to:", audio_path)
            with open(audio_path, "wb+") as f:
                for chunk in audio_file.chunks():
                    f.write(chunk)

            # Run the TTS subprocess
            result = subprocess.run(
                [
                    PYTHON_PATH,
                    "qwen3.py",
                    audio_path,
                    text,
                    ref_text
                ],
                capture_output=True,
                text=True
            )
            print("Subprocess STDOUT:", result.stdout)
            print("Subprocess STDERR:", result.stderr)

            if result.returncode != 0:
                return JsonResponse({"error": result.stderr}, status=500)

            output_audio_path = result.stdout.strip()
            if not os.path.exists(output_audio_path):
                return JsonResponse({"error": "Output audio file not found"}, status=500)

            # Return the generated audio file
            return FileResponse(open(output_audio_path, "rb"), content_type="audio/wav")

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        



