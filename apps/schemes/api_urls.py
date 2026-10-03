from django.urls import path
from . import api_views
app_name = 'api_schemes'
urlpatterns = [
    path('', api_views.SchemeListAPIView.as_view(), name='list'),
    path('recommended/', api_views.RecommendedSchemesAPIView.as_view(), name='recommended'),
    path('<str:pk>/', api_views.SchemeDetailAPIView.as_view(), name='detail'),
    path('<str:pk>/eligibility/', api_views.SchemeEligibilityAPIView.as_view(), name='eligibility'),
]
