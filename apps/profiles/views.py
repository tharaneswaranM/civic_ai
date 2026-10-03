"""Civic AI — Profiles (Dashboard) Views"""
import logging
import re
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from .models import UserProfile
from apps.schemes.models import UserSchemeMatch, SavedScheme, Scheme
from apps.notifications.models import Notification
from apps.audit.services import log_audit_event
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)
MAX_PROFILE_AGE_YEARS = 120
MAX_PROFILE_DEPENDENTS = 100


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@login_required
def dashboard(request):
    """Main dashboard view."""
    user = request.user
    profile = _get_or_create_profile(user)

    # Get eligibility matches
    matches = UserSchemeMatch.objects.filter(
        user=user,
        result=UserSchemeMatch.RESULT_ELIGIBLE,
    ).select_related('scheme', 'scheme__state').order_by('-evaluated_at')[:6]

    # Stats
    eligible_count = UserSchemeMatch.objects.filter(
        user=user, result=UserSchemeMatch.RESULT_ELIGIBLE
    ).count()
    new_schemes_count = Scheme.objects.filter(is_new=True).count()
    saved_count = SavedScheme.objects.filter(user=user).count()
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()

    # Time-based greeting
    hour = timezone.localtime().hour
    if hour < 12:
        greeting = _('Good Morning')
    elif hour < 17:
        greeting = _('Good Afternoon')
    else:
        greeting = _('Good Evening')

    context = {
        'profile': profile,
        'eligible_matches': matches,
        'eligible_count': eligible_count,
        'new_schemes_count': new_schemes_count,
        'saved_count': saved_count,
        'unread_notifications': unread_notifications,
        'greeting': greeting,
        'completion': profile.completion_percentage,
        'page_title': _('Dashboard'),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile_setup_step(request, step=1):
    """Multi-step profile setup wizard."""
    if step not in range(1, 6):
        return redirect('dashboard:profile_setup_step', step=1)
    user = request.user
    profile = _get_or_create_profile(user)
    total_steps = 5

    if request.method == 'POST':
        success = _save_profile_step(request, profile, step)
        if success:
            profile.update_completion()
            if step < total_steps:
                return redirect('dashboard:profile_setup_step', step=step + 1)
            else:
                user.is_profile_complete = True
                user.save(update_fields=['is_profile_complete'])
                messages.success(request, _('Your profile has been set up! Discovering schemes for you...'))
                # Trigger eligibility run in background (or synchronously for now)
                try:
                    from apps.eligibility.engine import run_eligibility_for_user
                    run_eligibility_for_user(user)
                except Exception as e:
                    logger.error(f"Eligibility run failed: {e}")
                return redirect('dashboard:home')

    from apps.states.models import District
    districts = []
    if profile.state:
        districts = District.objects.filter(state=profile.state, is_active=True)

    context = {
        'step': step,
        'total_steps': total_steps,
        'profile': profile,
        'districts': districts,
        'progress': int((step / total_steps) * 100),
        'page_title': _('Set Up Your Profile'),
        'step_titles': [
            _('Personal Information'),
            _('Location'),
            _('Education & Employment'),
            _('Income & Family'),
            _('Additional Details'),
        ],
    }
    return render(request, f'profiles/setup_step_{step}.html', context)


def _save_profile_step(request, profile, step):
    """Save form data for the current step."""
    try:
        if step not in range(1, 6):
            raise ValidationError(_('This profile step is invalid.'))

        if step == 1:
            profile.user.full_name = request.POST.get('full_name', '').strip()
            dob = request.POST.get('date_of_birth', '').strip()
            if dob:
                try:
                    profile.date_of_birth = date.fromisoformat(dob)
                except ValueError as exc:
                    raise ValidationError(_('Enter a valid date of birth.')) from exc
                today = date.today()
                if profile.date_of_birth > today:
                    raise ValidationError(_('Date of birth cannot be in the future.'))
                calculated_age = today.year - profile.date_of_birth.year - (
                    (today.month, today.day) < (profile.date_of_birth.month, profile.date_of_birth.day)
                )
                if calculated_age > MAX_PROFILE_AGE_YEARS:
                    raise ValidationError(_('Enter a date of birth within a reasonable age range.'))
                profile.age = calculated_age
            profile.gender = request.POST.get('gender', '')
            profile.user.preferred_language = request.POST.get(
                'preferred_language', profile.user.preferred_language or request.LANGUAGE_CODE
            ).strip()

        elif step == 2:
            from apps.states.models import State, District
            state_id = request.POST.get('state', '').strip()
            district_id = request.POST.get('district', '').strip()
            profile.state = None
            profile.district = None
            if state_id:
                try:
                    profile.state = State.objects.get(id=state_id, is_active=True)
                except (State.DoesNotExist, ValidationError, ValueError) as exc:
                    raise ValidationError(_('Choose a valid state.')) from exc
            if district_id:
                try:
                    profile.district = District.objects.get(
                        id=district_id,
                        state=profile.state,
                        is_active=True,
                    )
                except (District.DoesNotExist, ValidationError, ValueError) as exc:
                    raise ValidationError(_('Choose a district in the selected state.')) from exc
            profile.city_village = request.POST.get('city_village', '').strip()
            profile.pin_code = request.POST.get('pin_code', '').strip()
            if profile.pin_code and not re.fullmatch(r'[1-9]\d{5}', profile.pin_code):
                raise ValidationError(_('Enter a valid 6-digit PIN code.'))
            is_rural = request.POST.get('is_rural', '')
            if is_rural in ('true', 'false'):
                profile.is_rural = is_rural == 'true'
            elif is_rural:
                raise ValidationError(_('Choose Rural or Urban.'))

        elif step == 3:
            profile.education_level = request.POST.get('education_level', '')
            profile.employment_status = request.POST.get('employment_status', '')
            profile.occupation = request.POST.get('occupation', '').strip()
            profile.sector = request.POST.get('sector', '').strip()
            is_student = request.POST.get('is_student', '')
            if is_student in ('true', 'false'):
                profile.is_student = is_student == 'true'
            elif is_student:
                raise ValidationError(_('Choose whether you are currently a student.'))
            if profile.is_student:
                profile.student_course = request.POST.get('student_course', '').strip()
            else:
                profile.student_course = ''

        elif step == 4:
            profile.individual_income_range = request.POST.get('individual_income_range', '')
            profile.family_income_range = request.POST.get('family_income_range', '')
            profile.marital_status = request.POST.get('marital_status', '')
            dependents = request.POST.get('number_of_dependents', '').strip()
            if not dependents:
                profile.number_of_dependents = None
            elif dependents.isdigit() and int(dependents) <= MAX_PROFILE_DEPENDENTS:
                profile.number_of_dependents = int(dependents)
            else:
                raise ValidationError(_('Enter a valid number of dependents.'))
            profile.category = request.POST.get('category', '')

        elif step == 5:
            is_farmer = request.POST.get('is_farmer', '')
            has_disability = request.POST.get('has_disability', '')
            is_senior = request.POST.get('is_senior_citizen', '')
            is_widow = request.POST.get('is_widow', '')
            is_shg = request.POST.get('is_shg_member', '')
            is_job_seeker = request.POST.get('is_job_seeker', '')
            is_entrepreneur = request.POST.get('is_entrepreneur', '')
            is_ration = request.POST.get('is_ration_card_holder', '')

            def to_bool(val):
                if val in ('true', 'on', '1'):
                    return True
                if val in ('false', 'off', '0'):
                    return False
                if not val:
                    return None
                raise ValidationError(_('Choose Yes or No for each item.'))

            profile.is_farmer = to_bool(is_farmer)
            profile.has_disability = to_bool(has_disability)
            profile.is_senior_citizen = to_bool(is_senior)
            profile.is_widow = to_bool(is_widow)
            profile.is_shg_member = to_bool(is_shg)
            profile.is_job_seeker = to_bool(is_job_seeker)
            profile.is_entrepreneur = to_bool(is_entrepreneur)
            profile.is_ration_card_holder = to_bool(is_ration)
            if profile.is_farmer:
                profile.land_holding = request.POST.get('land_holding', '')
            elif profile.is_farmer is False:
                profile.land_holding = ''

        with transaction.atomic():
            profile.full_clean()
            editable_user_fields = {'full_name', 'preferred_language'}
            profile.user.full_clean(exclude=[
                field.name
                for field in profile.user._meta.fields
                if field.name not in editable_user_fields
            ])
            profile.user.save(update_fields=['full_name', 'preferred_language'])
            profile.save()
            log_audit_event(
                AuditLog.EVENT_PROFILE_UPDATED,
                request=request,
                user=profile.user,
                metadata={'profile_step': step},
            )
        return True
    except ValidationError as exc:
        error_fields = sorted(getattr(exc, 'error_dict', {}).keys())
        logger.info(
            'Rejected invalid profile step %s for user %s (fields=%s)',
            step,
            profile.user_id,
            error_fields,
        )
        messages.error(request, _('Some entered values are invalid. Please check this step and try again.'))
        return False
    except (ValueError, TypeError) as exc:
        logger.info('Rejected malformed profile step %s for user %s (%s)', step, profile.user_id, type(exc).__name__)
        messages.error(request, _('Some entered values are invalid. Please check this step and try again.'))
        return False


@login_required
def profile_view(request):
    """View and edit user profile."""
    profile = _get_or_create_profile(request.user)
    context = {
        'profile': profile,
        'page_title': _('My Profile'),
    }
    return render(request, 'profiles/profile.html', context)
