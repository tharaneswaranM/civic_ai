import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Scheme, SchemeCategory, SavedScheme, UserSchemeMatch, SchemeTranslation
from apps.security import safe_external_https_url
from apps.audit.services import log_audit_event
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

def scheme_list(request):
    category_slug = request.GET.get('category', '')
    state_filter = request.GET.get('state', '')
    search = request.GET.get('q', '')
    is_eligible_filter = request.GET.get('eligible', '') == '1'

    schemes = Scheme.objects.filter(status=Scheme.STATUS_ACTIVE).select_related('state', 'department', 'current_version').order_by('-is_featured', '-created_at')

    if search:
        schemes = schemes.filter(name__icontains=search)
    if state_filter:
        schemes = schemes.filter(state__slug=state_filter)
    if category_slug:
        schemes = schemes.filter(categories__slug=category_slug)

    if request.user.is_authenticated and is_eligible_filter:
        eligible_ids = UserSchemeMatch.objects.filter(
            user=request.user,
            result=UserSchemeMatch.RESULT_ELIGIBLE,
        ).values_list('scheme_id', flat=True)
        schemes = schemes.filter(id__in=eligible_ids)

    language = getattr(request, 'LANGUAGE_CODE', 'en')
    scheme_rows = list(schemes[:50])
    scheme_ids = [scheme.id for scheme in scheme_rows]
    matches_map = {}
    saved_ids = set()
    if request.user.is_authenticated and scheme_ids:
        matches_map = {
            match.scheme_id: match
            for match in UserSchemeMatch.objects.filter(
                user=request.user,
                scheme_id__in=scheme_ids,
            )
        }
        saved_ids = set(
            SavedScheme.objects.filter(
                user=request.user,
                scheme_id__in=scheme_ids,
            ).values_list('scheme_id', flat=True)
        )
    translations = {}
    if language != 'en':
        version_ids = [scheme.current_version_id for scheme in scheme_rows if scheme.current_version_id]
        translations = {
            item.scheme_version_id: item
            for item in SchemeTranslation.objects.filter(
                scheme_version_id__in=version_ids,
                language__code=language,
                reviewed=True,
            )
        }

    # Attach match, reviewed localized text, and saved flags.
    scheme_items = []
    for s in scheme_rows:
        s.user_match = matches_map.get(s.id)
        s.is_saved_by_user = s.id in saved_ids
        s.display_name = s.name
        s.display_description = s.get_description()
        s.display_benefit = s.get_benefit()
        s.display_how_to_apply = s.current_version.how_to_apply if s.current_version else ''
        localized = translations.get(s.current_version_id)
        if localized:
            s.display_name = localized.name or s.name
            s.display_description = localized.description or s.get_description()
            s.display_benefit = localized.benefit_summary or s.get_benefit()
            s.display_how_to_apply = localized.how_to_apply or s.display_how_to_apply
        scheme_items.append(s)

    categories = SchemeCategory.objects.filter(is_active=True, parent=None).order_by('display_order')

    title = _('My Schemes') if is_eligible_filter else _('Explore Schemes')
    context = {
        'schemes': scheme_items,
        'categories': categories,
        'current_category': category_slug,
        'current_state': state_filter,
        'is_eligible_filter': is_eligible_filter,
        'search': search,
        'page_title': title,
    }
    return render(request, 'schemes/scheme_list.html', context)

def scheme_detail(request, slug):
    scheme = get_object_or_404(
        Scheme.objects.select_related('state', 'department', 'current_version'),
        slug=slug,
        status=Scheme.STATUS_ACTIVE
    )
    language = getattr(request, 'LANGUAGE_CODE', 'en')
    localized = None
    if language != 'en' and scheme.current_version_id:
        localized = SchemeTranslation.objects.filter(
            scheme_version_id=scheme.current_version_id,
            language__code=language,
            reviewed=True,
        ).first()
    scheme.is_saved_by_user = (
        request.user.is_authenticated
        and SavedScheme.objects.filter(user=request.user, scheme=scheme).exists()
    )
    display_name = localized.name if localized and localized.name else scheme.name
    display_description = localized.description if localized and localized.description else scheme.get_description()
    display_benefit = localized.benefit_summary if localized and localized.benefit_summary else scheme.get_benefit()
    display_how_to_apply = localized.how_to_apply if localized and localized.how_to_apply else (scheme.current_version.how_to_apply if scheme.current_version else '')
    eligibility_result = None
    if request.user.is_authenticated:
        match = UserSchemeMatch.objects.filter(user=request.user, scheme=scheme).first()
        eligibility_result = match
    context = {
        'scheme': scheme,
        'version': scheme.current_version,
        'eligibility_result': eligibility_result,
        'display_name': display_name,
        'display_description': display_description,
        'display_benefit': display_benefit,
        'display_how_to_apply': display_how_to_apply,
        'official_url': safe_external_https_url(scheme.official_url),
        'page_title': display_name,
    }
    return render(request, 'schemes/scheme_detail.html', context)

@login_required
@require_POST
def save_scheme(request, slug):
    scheme = get_object_or_404(Scheme, slug=slug, status=Scheme.STATUS_ACTIVE)
    action = request.POST.get('action', 'save')
    if action == 'remove':
        SavedScheme.objects.filter(user=request.user, scheme=scheme).delete()
        messages.info(request, _('Scheme removed from saved.'))
    else:
        saved_scheme, created = SavedScheme.objects.get_or_create(user=request.user, scheme=scheme)
        if not created:
            return redirect('schemes:detail', slug=slug)
        log_audit_event(
            AuditLog.EVENT_SCHEME_SAVED,
            request=request,
            user=request.user,
            metadata={'scheme_id': str(scheme.id), 'scheme_name': scheme.name}
        )
        messages.success(request, _('Scheme saved!'))
    return redirect('schemes:detail', slug=slug)
