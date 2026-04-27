import random
from .models import BotMemory, ChatMessage

class SimpleChatbot:
    def __init__(self, user, session):
        self.user = user
        self.session = session
        # User memory get pannunga (or create pannunga)
        self.memory, created = BotMemory.objects.get_or_create(user=user)
    
    def get_response(self, user_message):
        """User message ku response generate pannudum"""
        message_lower = user_message.lower()
        
        # 1. Greeting Check
        if self.is_greeting(message_lower):
            return self.handle_greeting()
        
        # 2. Name Learning
        if 'my name is' in message_lower:
            return self.learn_name(user_message)
        
        # 3. Interest Learning
        if 'i like' in message_lower or 'i love' in message_lower:
            return self.learn_interest(user_message)
        
        # 4. Memory Test
        if 'what do you know about me' in message_lower or 'do you remember me' in message_lower:
            return self.recall_memory()
        
        # 5. Question Check
        if '?' in user_message:
            return self.handle_question(user_message)
        
        # 6. Default Response
        return self.default_response()
    
    def is_greeting(self, text):
        """Greeting ah nu check pannudum"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good evening']
        return any(greeting in text for greeting in greetings)
    
    def handle_greeting(self):
        """Greeting ku response"""
        if self.memory.user_name:
            return f"Hello {self.memory.user_name}! Nice to see you again! 😊"
        else:
            return "Hello! I'm your smart assistant. What's your name?"
    
    def learn_name(self, message):
        """Name ah learn pannudum"""
        # "My name is Raj" → "Raj" extract pannudum
        name = message.split('my name is')[-1].strip().split()[0]
        name = name.capitalize()
        
        # Memory la save pannunga
        self.memory.user_name = name
        self.memory.save()
        
        return f"Nice to meet you, {name}! I'll remember that. 😊"
    
    def learn_interest(self, message):
        """Interest ah learn pannudum"""
        message_lower = message.lower()
        
        if 'i like' in message_lower:
            interest = message_lower.split('i like')[-1].strip()
        else:
            interest = message_lower.split('i love')[-1].strip()
        
        # Existing interests ku add pannunga
        current_interests = self.memory.interests
        if current_interests:
            self.memory.interests = current_interests + ', ' + interest
        else:
            self.memory.interests = interest
        self.memory.save()
        
        return f"Great! I've noted that you like {interest}. 📝"
    
    def recall_memory(self):
        """Memory ah recall pannudum"""
        info = []
        
        if self.memory.user_name:
            info.append(f"Your name is {self.memory.user_name}")
        
        if self.memory.interests:
            info.append(f"You like: {self.memory.interests}")
        
        if info:
            return "Yes, I remember! " + '. '.join(info) + ". 🧠"
        else:
            return "We're just getting to know each other! Tell me about yourself."
    
    def handle_question(self, question):
        """Questions ku response"""
        responses = [
            "That's a good question! What do you think?",
            "Hmm, let me think about that... 🤔",
            "Interesting question! Can you tell me more?",
        ]
        return random.choice(responses)
    
    def default_response(self):
        """Default response"""
        responses = [
            "I see! Tell me more.",
            "That's interesting! Continue...",
            "Hmm, I understand. What else?",
            "Thanks for sharing! 😊",
        ]
        return random.choice(responses)
    
    def get_conversation_context(self):
        """Previous messages get pannudum"""
        recent_messages = ChatMessage.objects.filter(
            session=self.session
        ).order_by('-timestamp')[:5]
        
        context = []
        for msg in reversed(recent_messages):
            context.append({
                'is_bot': msg.is_bot,
                'content': msg.content,
                'time': msg.timestamp.strftime('%H:%M')
            })
        
        return context