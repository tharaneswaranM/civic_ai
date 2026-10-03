"""Civic AI — Notifications API Views"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import Notification
from apps.security import safe_action_url


class NotificationsListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
        data = [{
            'id': str(n.id),
            'type': n.notification_type,
            'title': n.title,
            'body': n.body,
            'is_read': n.is_read,
            'action_url': safe_action_url(n.action_url, request),
            'created_at': n.created_at.isoformat(),
        } for n in notifications]
        return Response({'notifications': data})


class UnreadCountAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})
