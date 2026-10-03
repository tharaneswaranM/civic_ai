from django.urls import path
from . import views
app_name = 'schemes'
urlpatterns = [
    path('', views.scheme_list, name='list'),
    path('<slug:slug>/', views.scheme_detail, name='detail'),
    path('<slug:slug>/save/', views.save_scheme, name='save'),
]
