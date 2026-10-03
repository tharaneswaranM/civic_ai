from django.urls import path
from . import api_views
app_name = 'api_assistant'
urlpatterns = [
    path('chat/', api_views.ChatAPIView.as_view(), name='chat'),
]
