"""
Civic AI — States Context Processors
Injects active states into all template contexts.
"""
from .models import State


def active_states(request):
    """Make active states available globally in templates."""
    try:
        states = State.objects.filter(is_active=True).order_by('display_order')
        selected_state = None
        state_slug = None

        if request.user.is_authenticated and request.user.preferred_state:
            selected_state = request.user.preferred_state
            state_slug = selected_state.slug
        else:
            state_slug = request.session.get('selected_state')
            if state_slug:
                try:
                    selected_state = State.objects.get(slug=state_slug, is_active=True)
                except State.DoesNotExist:
                    state_slug = None

        return {
            'active_states': states,
            'selected_state': selected_state,
            'selected_state_slug': state_slug,
        }
    except Exception:
        return {
            'active_states': [],
            'selected_state': None,
            'selected_state_slug': None,
        }
