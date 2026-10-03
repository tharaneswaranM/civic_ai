from django.urls import path
from . import api_views
app_name = 'api_notifications'
urlpatterns = [
    path('', api_views.NotificationsListAPIView.as_view(), name='list'),
    path('unread-count/', api_views.UnreadCountAPIView.as_view(), name='unread_count'),
]
