from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from .models import ApplicationTracker
from apps.security import safe_external_https_url
from apps.audit.models import AuditLog
from apps.audit.services import log_audit_event

@login_required
def applications_list(request):
    query = ApplicationTracker.objects.filter(
        user=request.user
    ).select_related('scheme').order_by('-updated_at')
    applications = Paginator(query, 25).get_page(request.GET.get('page'))
    context = {'applications': applications, 'page_title': _('My Applications')}
    return render(request, 'applications/list.html', context)

@login_required
def application_detail(request, pk):
    app = get_object_or_404(ApplicationTracker.objects.select_related('scheme'), pk=pk, user=request.user)
    context = {
        'application': app,
        'official_url': safe_external_https_url(app.scheme.official_url),
        'page_title': app.scheme.name,
    }
    return render(request, 'applications/detail.html', context)

@login_required
@require_POST
def add_application(request, scheme_slug):
    from apps.schemes.models import Scheme
    scheme = get_object_or_404(Scheme, slug=scheme_slug)
    app, created = ApplicationTracker.objects.get_or_create(user=request.user, scheme=scheme)
    return redirect('applications:detail', pk=app.pk)

@login_required
@require_POST
def update_status(request, pk):
    app = get_object_or_404(ApplicationTracker, pk=pk, user=request.user)
    new_status = request.POST.get('status', app.status)
    if new_status in dict(ApplicationTracker.STATUS_CHOICES) and new_status != app.status:
        previous_status = app.status
        app.status = new_status
        app.save(update_fields=['status', 'updated_at'])
        log_audit_event(
            AuditLog.EVENT_APPLICATION_STATUS_CHANGED,
            request=request,
            user=request.user,
            metadata={
                'application_id': str(app.pk),
                'scheme_id': str(app.scheme_id),
                'previous_status': previous_status,
                'new_status': new_status,
            },
        )
    return redirect('applications:detail', pk=pk)
