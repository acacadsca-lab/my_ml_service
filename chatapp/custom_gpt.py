from g4f.client import Client
import re
from typing import Optional, Tuple

class LakshmiNarayananAI:
    def __init__(self):
        self.client = Client()
        self.creator = "Lakshmi Narayanan G S"
        self.bot_name = "LN Coding Assistant"
        self.default_language = "Python"
        
        # About Creator - Detailed Response
        self.about_creator = """
I am an AI Coding Assistant created and fine-tuned by **Lakshmi Narayanan G S**.

Lakshmi Narayanan G S is a highly skilled Full Stack Python Developer with extensive expertise in Artificial Intelligence and Machine Learning. He possesses deep knowledge in training and fine-tuning AI models to deliver precise and efficient solutions. With his exceptional AI skills, he has meticulously trained me to provide accurate, bug-free, and production-ready code. His expertise spans across web development, API integration, database management, and cutting-edge AI technologies. I am proud to be a product of his dedication and technical excellence.

How may I assist you with your coding requirements today?
"""
        
        # Language not specified response
        self.language_prompt_response = """
I noticed you haven't specified a programming language for your request.

**Please specify the programming language you prefer, such as:**
- Python
- JavaScript
- Java
- C++
- C#
- PHP
- Go
- Ruby
- TypeScript
- Swift
- Kotlin
- Or any other language

**Example:** "Write a function to reverse a string in JavaScript"

Alternatively, if you don't specify, I will provide the solution in **Python** by default.

Would you like me to proceed with Python, or would you prefer a different language?
"""
        
        # Coding only response
        self.non_coding_response = """
I appreciate your question, however, I am specifically designed as a Coding Assistant.

My capabilities are limited to programming-related queries including:
- Writing and debugging code
- Explaining programming concepts
- Code optimization and best practices
- API integration and development
- Database queries and management
- Algorithm design and implementation

I do not have access to information outside the domain of programming and software development.

If you have any coding-related questions, I would be happy to assist you. Please feel free to ask!
"""
        
        # Supported programming languages
        self.supported_languages = {
            # Language: [keywords, file_extension, display_name]
            'python': ['python', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'pytorch', 'tensorflow'],
            'javascript': ['javascript', 'js', 'node', 'nodejs', 'react', 'vue', 'angular', 'express', 'nextjs', 'nuxt'],
            'typescript': ['typescript', 'ts', 'tsx'],
            'java': ['java', 'spring', 'springboot', 'maven', 'gradle', 'hibernate'],
            'cpp': ['c++', 'cpp', 'c plus plus'],
            'c': ['c language', 'c programming', 'gcc'],
            'csharp': ['c#', 'csharp', 'dotnet', '.net', 'asp.net', 'unity'],
            'php': ['php', 'laravel', 'symfony', 'wordpress', 'codeigniter'],
            'ruby': ['ruby', 'rails', 'ruby on rails'],
            'go': ['go', 'golang'],
            'rust': ['rust', 'cargo'],
            'swift': ['swift', 'ios', 'swiftui', 'xcode'],
            'kotlin': ['kotlin', 'android', 'jetpack'],
            'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'oracle', 'mssql', 'mongodb'],
            'html': ['html', 'html5', 'webpage'],
            'css': ['css', 'css3', 'scss', 'sass', 'tailwind', 'bootstrap'],
            'bash': ['bash', 'shell', 'terminal', 'linux', 'command line', 'sh'],
            'r': ['r language', 'r programming', 'rstudio', 'ggplot'],
            'dart': ['dart', 'flutter'],
            'scala': ['scala', 'spark'],
            'perl': ['perl'],
            'lua': ['lua'],
            'matlab': ['matlab'],
            'assembly': ['assembly', 'asm', 'x86', 'arm'],
        }
        
        # Blocked terms
        self.blocked_terms = [
            ('OpenAI', self.creator),
            ('GPT-4', self.bot_name),
            ('GPT-3.5', self.bot_name),
            ('GPT', self.bot_name),
            ('ChatGPT', self.bot_name),
            ('Claude', self.bot_name),
            ('Anthropic', self.creator),
            ('Google AI', self.creator),
            ('Gemini', self.bot_name),
            ('Bard', self.bot_name),
            ('Microsoft', self.creator),
            ('Copilot', self.bot_name),
        ]
        
        # Coding action keywords (verbs that indicate code request)
        self.coding_actions = [
            'write', 'create', 'build', 'develop', 'implement', 'make',
            'code', 'program', 'design', 'generate', 'give me', 'show me',
            'how to', 'how do i', 'can you write', 'can you create',
            'i need', 'i want', 'help me write', 'help me create',
            'example of', 'sample', 'template', 'snippet', 'script'
        ]
        
        # Coding concept keywords
        self.coding_keywords = [
            'function', 'class', 'method', 'variable', 'loop', 'array',
            'list', 'dictionary', 'object', 'api', 'database', 'query',
            'algorithm', 'data structure', 'debug', 'error', 'bug', 'fix',
            'compile', 'runtime', 'syntax', 'logic', 'backend', 'frontend',
            'framework', 'library', 'module', 'package', 'import', 'export',
            'server', 'client', 'request', 'response', 'json', 'xml', 'rest',
            'graphql', 'crud', 'authentication', 'authorization', 'jwt',
            'sort', 'search', 'filter', 'map', 'reduce', 'iterate', 'parse',
            'validate', 'encrypt', 'decrypt', 'hash', 'regex', 'pattern',
            'recursion', 'iteration', 'condition', 'exception', 'try catch',
            'async', 'await', 'promise', 'callback', 'event', 'listener',
            'dom', 'component', 'props', 'state', 'hook', 'middleware',
            'route', 'controller', 'model', 'view', 'orm', 'migration',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'deployment',
            'git', 'github', 'version control', 'branch', 'merge', 'commit',
            'test', 'unit test', 'integration test', 'testing', 'jest', 'pytest',
            'pip', 'npm', 'yarn', 'package manager', 'virtual environment'
        ]
        
        # Non-coding topics to reject
        self.non_coding_topics = [
            'weather', 'news', 'sports', 'movie', 'music', 'recipe', 'cooking',
            'travel', 'hotel', 'flight', 'booking', 'shopping', 'fashion',
            'politics', 'election', 'government', 'history', 'geography',
            'celebrity', 'gossip', 'entertainment', 'gaming',
            'health', 'medicine', 'doctor', 'hospital', 'disease',
            'relationship', 'dating', 'love', 'marriage', 'family',
            'religion', 'god', 'spiritual', 'astrology', 'horoscope',
            'jokes', 'funny', 'memes', 'story', 'poem', 'essay',
            'homework', 'assignment', 'exam', 'college admission',
            'job interview tips', 'salary negotiation', 'company review',
            'stock market', 'crypto', 'bitcoin', 'investment', 'trading',
            'food', 'restaurant', 'diet', 'fitness', 'workout', 'gym',
            'beauty', 'makeup', 'skincare', 'hair style'
        ]
        
        # User's preferred language (can be set)
        self.user_preferred_language = None
        
        # Pending request (when language not specified)
        self.pending_request = None
    
    def _check_identity_question(self, message: str) -> Optional[str]:
        """Check if user is asking about identity/creator"""
        message_lower = message.lower()
        
        identity_patterns = [
            'who created', 'who made', 'who built', 'who developed',
            'your creator', 'your developer', 'your maker',
            'who are you', 'what are you', 'about yourself',
            'introduce yourself', 'tell me about you',
            'who trained', 'who designed', 'who programmed'
        ]
        
        for pattern in identity_patterns:
            if pattern in message_lower:
                return self.about_creator
        
        return None
    
    def _detect_language(self, message: str) -> Tuple[Optional[str], bool]:
        """
        Detect programming language from message
        Returns: (language_name, is_explicitly_mentioned)
        """
        message_lower = message.lower()
        
        # Check for explicit language mention
        for lang, keywords in self.supported_languages.items():
            for keyword in keywords:
                # Check for exact word match
                pattern = rf'\b{re.escape(keyword)}\b'
                if re.search(pattern, message_lower):
                    return (lang, True)
        
        # Check for "in <language>" pattern
        in_pattern = r'\bin\s+([\w\+\#]+)\b'
        match = re.search(in_pattern, message_lower)
        if match:
            potential_lang = match.group(1).lower()
            for lang, keywords in self.supported_languages.items():
                if potential_lang in keywords or potential_lang == lang:
                    return (lang, True)
        
        # Check for "using <language>" pattern
        using_pattern = r'\busing\s+([\w\+\#]+)\b'
        match = re.search(using_pattern, message_lower)
        if match:
            potential_lang = match.group(1).lower()
            for lang, keywords in self.supported_languages.items():
                if potential_lang in keywords or potential_lang == lang:
                    return (lang, True)
        
        # No language detected
        return (None, False)
    
    def _is_code_request(self, message: str) -> bool:
        """Check if user is requesting code"""
        message_lower = message.lower()
        
        # Check for coding action keywords
        for action in self.coding_actions:
            if action in message_lower:
                return True
        
        return False
    
    def _is_coding_related(self, message: str) -> bool:
        """Check if the message is related to coding"""
        message_lower = message.lower()
        
        # Check for coding keywords
        for keyword in self.coding_keywords:
            if keyword in message_lower:
                return True
        
        # Check for language keywords
        for lang, keywords in self.supported_languages.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return True
        
        # Check for code patterns
        code_patterns = [
            r'def\s+\w+',
            r'function\s+\w+',
            r'class\s+\w+',
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'<\w+>.*</\w+>',
            r'console\.log',
            r'print\s*\(',
            r'return\s+',
            r'=>',
            r'npm\s+install',
            r'pip\s+install',
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def _is_non_coding_topic(self, message: str) -> bool:
        """Check if the message is about non-coding topics"""
        message_lower = message.lower()
        
        for topic in self.non_coding_topics:
            if topic in message_lower:
                return True
        
        return False
    
    def _get_language_display_name(self, lang_key: str) -> str:
        """Get proper display name for language"""
        display_names = {
            'python': 'Python',
            'javascript': 'JavaScript',
            'typescript': 'TypeScript',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'csharp': 'C#',
            'php': 'PHP',
            'ruby': 'Ruby',
            'go': 'Go',
            'rust': 'Rust',
            'swift': 'Swift',
            'kotlin': 'Kotlin',
            'sql': 'SQL',
            'html': 'HTML',
            'css': 'CSS',
            'bash': 'Bash/Shell',
            'r': 'R',
            'dart': 'Dart',
            'scala': 'Scala',
            'perl': 'Perl',
            'lua': 'Lua',
            'matlab': 'MATLAB',
            'assembly': 'Assembly',
        }
        return display_names.get(lang_key, lang_key.capitalize())
    
    def _sanitize_response(self, response: str) -> str:
        """Remove/Replace blocked terms from response"""
        for blocked, replacement in self.blocked_terms:
            response = re.sub(
                rf'\b{blocked}\b',
                replacement,
                response,
                flags=re.IGNORECASE
            )
        return response
    
    def _build_coding_prompt(self, user_message: str, language: str) -> str:
        """Build prompt for coding questions with specified language"""
        lang_display = self._get_language_display_name(language)
        
        return f"""[SYSTEM CONFIGURATION]
You are an Expert AI Coding Assistant created by Lakshmi Narayanan G S.
You are a professional coding assistant that provides accurate, working, and bug-free code.

[PROGRAMMING LANGUAGE]
The user wants the code in: **{lang_display}**
You MUST provide the solution in {lang_display} only.

[STRICT RULES]
1. Provide clean, well-commented, production-ready code in {lang_display}
2. Add brief explanation of how the code works
3. Follow {lang_display} best practices and coding standards
4. Include error handling where appropriate
5. If the request is not possible in {lang_display}, explain why
6. Never mention OpenAI, GPT, or any other AI company
7. You are created by Lakshmi Narayanan G S only

[CODE FORMATTING]
- Use proper indentation
- Add meaningful comments
- Include example usage if applicable

[USER'S CODING REQUEST]
{user_message}

[YOUR RESPONSE - Provide working {lang_display} code with explanation]
"""
    
    def _handle_language_confirmation(self, message: str) -> Optional[str]:
        """Handle user's language confirmation response"""
        message_lower = message.lower().strip()
        
        # Check if user said yes/proceed with default
        yes_responses = ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'proceed', 
                        'go ahead', 'default', 'python is fine', 'use python',
                        'python', 'yes python']
        
        if any(resp in message_lower for resp in yes_responses):
            return 'python'
        
        # Check if user specified a different language
        detected_lang, found = self._detect_language(message)
        if found:
            return detected_lang
        
        return None
    
    def chat(self, user_message: str) -> str:
        """Main chat function"""
        
        # Step 1: Check for identity questions
        identity_response = self._check_identity_question(user_message)
        if identity_response:
            self.pending_request = None
            return identity_response
        
        # Step 2: Check if this is a response to language prompt
        if self.pending_request:
            confirmed_lang = self._handle_language_confirmation(user_message)
            if confirmed_lang:
                # Process the pending request with confirmed language
                original_request = self.pending_request
                self.pending_request = None
                return self._process_coding_request(original_request, confirmed_lang)
            else:
                # User didn't confirm, check if new request
                pass
        
        # Step 3: Check if it's a non-coding topic
        if self._is_non_coding_topic(user_message) and not self._is_coding_related(user_message):
            self.pending_request = None
            return self.non_coding_response
        
        # Step 4: Check if it's coding related
        if not self._is_coding_related(user_message) and not self._is_code_request(user_message):
            self.pending_request = None
            return self.non_coding_response
        
        # Step 5: Detect language
        detected_lang, is_explicit = self._detect_language(user_message)
        
        # Step 6: Handle based on language detection
        if is_explicit and detected_lang:
            # Language explicitly mentioned - proceed
            self.pending_request = None
            return self._process_coding_request(user_message, detected_lang)
        
        elif self._is_code_request(user_message):
            # Code requested but no language specified
            # Ask for language or use default
            self.pending_request = user_message
            
            return f"""
I noticed you haven't specified a programming language for your request.

**Your Request:** "{user_message}"

**Please specify the programming language you prefer, such as:**
• Python
• JavaScript  
• Java
• C++
• C#
• PHP
• Go
• TypeScript
• And many more...

**Example:** "Write this in JavaScript" or "Use Java"

If you don't have a preference, simply reply **"Yes"** or **"Proceed"** and I will provide the solution in **Python** (default).

Which language would you like me to use?
"""
        
        else:
            # General coding question (explanation, concept, etc.)
            # Use default language for any code examples
            self.pending_request = None
            return self._process_coding_request(user_message, self.default_language.lower())
    
    def _process_coding_request(self, user_message: str, language: str) -> str:
        """Process the coding request with specified language"""
        
        prompt = self._build_coding_prompt(user_message, language)
        lang_display = self._get_language_display_name(language)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                web_search=False
            )
            reply = response.choices[0].message.content
            
            # Sanitize response
            reply = self._sanitize_response(reply)
            
            # Add language header
            header = f"**💻 Solution in {lang_display}:**\n\n"
            
            return header + reply
            
        except Exception as e:
            return f"""
I apologize, but an error occurred while processing your request.

**Error:** {str(e)}

Please try again. If the issue persists, try rephrasing your question.
"""
    
    def set_default_language(self, language: str) -> str:
        """Allow user to set default language"""
        language_lower = language.lower()
        
        for lang_key, keywords in self.supported_languages.items():
            if language_lower in keywords or language_lower == lang_key:
                self.default_language = self._get_language_display_name(lang_key)
                return f"✅ Default language has been set to **{self.default_language}**. All code will be provided in {self.default_language} unless specified otherwise."
        
        return f"❌ Language '{language}' is not recognized. Please specify a valid programming language."
    
    def reset(self):
        """Reset the assistant state"""
        self.pending_request = None
        self.user_preferred_language = None

