from django.urls import path
from . import views
app_name = 'assistant'
urlpatterns = [
    path('', views.assistant_home, name='home'),
    path('chat/', views.chat_view, name='chat'),
]
