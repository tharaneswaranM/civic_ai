import logging
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import Scheme, UserSchemeMatch
from apps.security import safe_external_https_url

logger = logging.getLogger(__name__)


class SchemeListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        schemes = Scheme.objects.filter(status=Scheme.STATUS_ACTIVE).select_related('state')[:20]
        data = [{
            'id': str(s.id),
            'name': s.name,
            'slug': s.slug,
            'level': s.level,
            'status': s.status,
            'state': s.state.name if s.state else 'Central',
            'description': s.get_description()[:200],
            'benefit': s.get_benefit()[:200],
        } for s in schemes]
        return Response({'schemes': data})


class RecommendedSchemesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        matches = UserSchemeMatch.objects.filter(
            user=request.user,
            result=UserSchemeMatch.RESULT_ELIGIBLE,
        ).select_related('scheme', 'scheme__state').order_by('-evaluated_at')[:10]
        data = [{
            'id': str(m.scheme.id),
            'name': m.scheme.name,
            'slug': m.scheme.slug,
            'result': m.result,
            'matched_rules': m.matched_rules,
        } for m in matches]
        return Response({'recommended': data})


class SchemeDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            scheme = Scheme.objects.get(pk=pk)
        except (Scheme.DoesNotExist, ValidationError, ValueError):
            return Response({'error': 'Not found'}, status=404)
        return Response({
            'id': str(scheme.id),
            'name': scheme.name,
            'level': scheme.level,
            'status': scheme.status,
            'description': scheme.get_description(),
            'benefit': scheme.get_benefit(),
            'official_url': safe_external_https_url(scheme.official_url),
        })


class SchemeEligibilityAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            scheme = Scheme.objects.get(pk=pk)
        except (Scheme.DoesNotExist, ValidationError, ValueError):
            return Response({'error': 'Not found'}, status=404)

        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response(
                {'error': 'User profile not found. Please complete profile setup first.'},
                status=400
            )

        try:
            from apps.eligibility.engine import EligibilityEngine
            engine = EligibilityEngine()
            result = engine.evaluate(profile, scheme)
            return Response({
                'result': result.result,
                'summary': result.summary,
                'configuration_errors': result.configuration_errors,
                'rule_results': [
                    {
                        'rule': r.rule_type,
                        'passed': r.passed,
                        'label': r.display_label,
                        'reason': r.reason,
                    }
                    for r in result.rule_results
                ],
                'missing_info': result.missing_info,
            })
        except Exception:
            logger.exception("Failed to evaluate eligibility for user %s on scheme %s", request.user.id, scheme.id)
            return Response({'error': 'Failed to evaluate eligibility.'}, status=500)
