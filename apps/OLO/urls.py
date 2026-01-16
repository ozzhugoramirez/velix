from django.urls import path
from . import views

urlpatterns = [
    # Esta es la ruta que llamará el fetch de JS
    path('chatbot-message/', views.chatbot_message, name='chatbot_message'),
]