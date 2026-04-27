from django.contrib import admin

from memorybot.models import ChatSession
from memorybot.models import ChatMessage
from memorybot.models import BotMemory

admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(BotMemory)