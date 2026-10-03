from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

@login_required
def assistant_home(request):
    context = {'page_title': _('Ask Civic AI')}
    return render(request, 'assistant/assistant.html', context)

@login_required
def chat_view(request):
    return assistant_home(request)
