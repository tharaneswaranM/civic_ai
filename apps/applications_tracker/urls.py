from django.urls import path
from . import views
app_name = 'applications'
urlpatterns = [
    path('', views.applications_list, name='list'),
    path('<uuid:pk>/', views.application_detail, name='detail'),
    path('add/<str:scheme_slug>/', views.add_application, name='add'),
    path('<uuid:pk>/update/', views.update_status, name='update_status'),
]
