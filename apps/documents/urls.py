from django.urls import path
from . import views
app_name = 'documents'
urlpatterns = [
    path('', views.documents_overview, name='overview'),
]
