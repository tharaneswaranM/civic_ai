from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from .models import DocumentChecklist

@login_required
def documents_overview(request):
    query = DocumentChecklist.objects.filter(
        user=request.user
    ).select_related('scheme').order_by('scheme__name')
    checklist = Paginator(query, 25).get_page(request.GET.get('page'))
    context = {'checklist': checklist, 'page_title': _('My Documents')}
    return render(request, 'documents/overview.html', context)
