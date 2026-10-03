"""Civic AI — Assistant API View"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class ChatAPIView(APIView):
    """
    AI Chat endpoint.
    Phase 1: Returns a mocked/structured response.
    Phase 3: Full RAG + Google AI integration.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not hasattr(request.data, 'get'):
            return Response({'error': 'A JSON object is required.'}, status=400)
        raw_message = request.data.get('message', '')
        message = raw_message.strip() if isinstance(raw_message, str) else ''
        supported = {code for code, _name in settings.LANGUAGES}
        requested_language = request.data.get('language')
        if not isinstance(requested_language, str) or requested_language not in supported:
            requested_language = getattr(request.user, 'preferred_language', '')
        language = requested_language if requested_language in supported else getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
        context_scheme_id = request.data.get('scheme_id')

        if not message:
            return Response({'error': 'message is required'}, status=400)
        if len(message) > 4000:
            return Response({'error': 'message must be 4000 characters or fewer'}, status=413)

        # Phase 1: Return intelligent mock response
        with translation.override(language):
            response_text = self._generate_response(message, request.user, language, context_scheme_id)

        # Store in conversation history
        from django.core.exceptions import ValidationError
        from apps.assistant.models import AssistantConversation, AssistantMessage
        conv_id = request.data.get('conversation_id')
        conversation = None
        if conv_id:
            try:
                conversation = AssistantConversation.objects.get(
                    id=conv_id, user=request.user
                )
            except (AssistantConversation.DoesNotExist, ValidationError, ValueError):
                pass

        if not conversation:
            conversation = AssistantConversation.objects.create(
                user=request.user, language=language,
                title=message[:50]
            )

        AssistantMessage.objects.create(
            conversation=conversation, role='user', content=message
        )
        assistant_msg = AssistantMessage.objects.create(
            conversation=conversation, role='assistant', content=response_text
        )

        return Response({
            'success': True,
            'response': response_text,
            'conversation_id': str(conversation.id),
            'message_id': str(assistant_msg.id),
            'sources': [],
        })

    def _generate_response(self, message, user, language, scheme_id):
        """Phase 1 mock. Will be replaced with Google AI + RAG in Phase 3."""
        msg_lower = message.lower()

        if any(w in msg_lower for w in ['eligible', 'qualify', 'schemes for me', 'தகுதி', 'திட்டங்கள்', 'అర్హత', 'పథకాలు']):
            return (
                _("Based on your profile, I can see potential matches for government schemes.") + ' '
                + _("Please complete your profile for a full eligibility analysis.") + ' '
                + _("Visit the 'My Schemes' section to see your personalized recommendations.")
            )
        elif any(w in msg_lower for w in ['document', 'papers', 'certificate', 'ஆவண', 'சான்றிதழ்', 'పత్రాలు', 'ధృవీకరణ పత్రం']):
            return (
                _("Government schemes typically require: Aadhaar card, income certificate, bank passbook, caste certificate (if applicable), residence proof, and scheme-specific documents.") + ' '
                + _("Check each scheme's detail page for exact requirements.")
            )
        elif any(w in msg_lower for w in ['apply', 'how to apply', 'application', 'விண்ணப்ப', 'దరఖాస్తు']):
            return (
                _("To apply for a government scheme: 1) Verify your eligibility, 2) Gather required documents, 3) Visit the official scheme portal or nearest government office, 4) Submit your application with documents, 5) Track your application status.") + ' '
                + _("I can guide you for specific schemes.")
            )
        else:
            return (
                _("I'm Civic AI, your assistant for government schemes and civic services.") + ' '
                + _("I can help you discover schemes you may be eligible for, explain scheme details, list required documents, and guide you through the application process.") + ' '
                + _("What would you like to know?")
            )
