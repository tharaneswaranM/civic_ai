from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Notification
from apps.security import safe_action_url

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    for notification in notifications:
        notification.safe_action_url = safe_action_url(notification.action_url, request)
    context = {'notifications': notifications, 'page_title': _('Notifications')}
    return render(request, 'notifications/list.html', context)

@login_required
@require_POST
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.read_at = timezone.now()
    n.save(update_fields=['is_read', 'read_at'])
    return redirect('notifications:list')

@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
    return redirect('notifications:list')
