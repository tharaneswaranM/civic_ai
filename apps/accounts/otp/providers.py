"""
Civic AI — OTP Provider Abstraction
Pluggable OTP delivery system.

To add a new provider:
  1. Create a class in this file inheriting from BaseOTPProvider
  2. Add it to settings.OTP_PROVIDERS
  3. Set OTP_PROVIDER in .env

The application logic never needs to change.
"""
import logging
import random
import hashlib
import hmac
from abc import ABC, abstractmethod
from django.conf import settings

logger = logging.getLogger(__name__)


# ─── Base Provider ─────────────────────────────────────────────────────────────

class BaseOTPProvider(ABC):
    """Abstract base class for all OTP providers."""

    @abstractmethod
    def send_otp(self, mobile_number: str, otp: str) -> dict:
        """
        Send OTP to the mobile number.
        
        Args:
            mobile_number: E.164 format, e.g. +919876543210
            otp: 6-digit OTP string
            
        Returns:
            dict with keys:
                success (bool)
                message (str)
                provider_reference (str) — provider's message ID if available
        """
        raise NotImplementedError

    def generate_otp(self) -> str:
        """Generate a secure 6-digit OTP."""
        return str(random.SystemRandom().randint(100000, 999999))

    def hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage. Never store OTP plaintext."""
        return hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            otp.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

    def verify_otp(self, otp: str, otp_hash: str) -> bool:
        """Verify OTP against its hash."""
        return hmac.compare_digest(self.hash_otp(otp), otp_hash)


# ─── Mock Provider (Development) ──────────────────────────────────────────────

class MockOTPProvider(BaseOTPProvider):
    """
    Development-only OTP provider.
    Does not disclose generated OTPs in logs or standard output.
    """

    MOCK_OTP = '123456'  # Fixed OTP for easy UI testing

    def send_otp(self, mobile_number: str, otp: str) -> dict:
        masked = mobile_number[:-4] + '****' if len(mobile_number) > 4 else '****'
        logger.info('[MOCK OTP] Development OTP dispatched for %s', masked)
        return {
            'success': True,
            'message': 'Mock OTP sent (development mode).',
            'provider_reference': 'mock-dev-001',
        }

    def verify_otp(self, otp: str, otp_hash: str) -> bool:
        # The fixed test code must never bypass verification outside development.
        if getattr(settings, 'OTP_MOCK_ALLOWED', False) and otp == self.MOCK_OTP:
            return True
        return super().verify_otp(otp, otp_hash)


# ─── MSG91 Provider ───────────────────────────────────────────────────────────

class MSG91OTPProvider(BaseOTPProvider):
    """MSG91 SMS OTP provider."""

    def __init__(self):
        provider_config = settings.OTP_PROVIDERS.get('msg91', {})
        self.auth_key = provider_config.get('AUTH_KEY', '')
        self.sender_id = provider_config.get('SENDER_ID', 'CIVICAI')
        self.template_id = provider_config.get('TEMPLATE_ID', '')

    def send_otp(self, mobile_number: str, otp: str) -> dict:
        try:
            import httpx
            # Remove '+' prefix for MSG91
            number = mobile_number.lstrip('+')
            payload = {
                'template_id': self.template_id,
                'mobile': number,
                'authkey': self.auth_key,
                'otp': otp,
            }
            response = httpx.post(
                'https://api.msg91.com/api/v5/otp',
                json=payload,
                timeout=10,
            )
            data = response.json()
            success = data.get('type') == 'success'
            return {
                'success': success,
                'message': data.get('message', ''),
                'provider_reference': data.get('request_id', ''),
            }
        except Exception as e:
            logger.error('MSG91 OTP send failed (%s)', type(e).__name__)
            return {'success': False, 'message': 'OTP delivery failed.', 'provider_reference': ''}


# ─── Twilio Provider ──────────────────────────────────────────────────────────

class TwilioOTPProvider(BaseOTPProvider):
    """Twilio Verify SMS OTP provider."""

    def __init__(self):
        provider_config = settings.OTP_PROVIDERS.get('twilio', {})
        self.account_sid = provider_config.get('ACCOUNT_SID', '')
        self.auth_token = provider_config.get('AUTH_TOKEN', '')
        self.from_number = provider_config.get('FROM_NUMBER', '')

    def send_otp(self, mobile_number: str, otp: str) -> dict:
        try:
            import httpx
            message_body = f"Your Civic AI OTP is: {otp}. Valid for 5 minutes. Do not share."
            response = httpx.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json',
                data={
                    'From': self.from_number,
                    'To': mobile_number,
                    'Body': message_body,
                },
                auth=(self.account_sid, self.auth_token),
                timeout=10,
            )
            data = response.json()
            success = response.status_code in [200, 201]
            return {
                'success': success,
                'message': data.get('status', ''),
                'provider_reference': data.get('sid', ''),
            }
        except Exception as e:
            logger.error('Twilio OTP send failed (%s)', type(e).__name__)
            return {'success': False, 'message': 'OTP delivery failed.', 'provider_reference': ''}


# ─── Fast2SMS Provider ────────────────────────────────────────────────────────

class Fast2SMSOTPProvider(BaseOTPProvider):
    """Fast2SMS OTP provider for India."""

    def __init__(self):
        provider_config = settings.OTP_PROVIDERS.get('fast2sms', {})
        self.api_key = provider_config.get('API_KEY', '')

    def send_otp(self, mobile_number: str, otp: str) -> dict:
        try:
            import httpx
            # Remove country code for Fast2SMS
            number = mobile_number.lstrip('+91').lstrip('+')
            response = httpx.post(
                'https://www.fast2sms.com/dev/bulkV2',
                headers={'authorization': self.api_key},
                data={
                    'route': 'otp',
                    'variables_values': otp,
                    'numbers': number,
                },
                timeout=10,
            )
            data = response.json()
            success = data.get('return', False)
            return {
                'success': success,
                'message': data.get('message', [''])[0] if isinstance(data.get('message'), list) else data.get('message', ''),
                'provider_reference': ','.join(data.get('request_id', [])),
            }
        except Exception as e:
            logger.error('Fast2SMS OTP send failed (%s)', type(e).__name__)
            return {'success': False, 'message': 'OTP delivery failed.', 'provider_reference': ''}


# ─── Exotel Provider ──────────────────────────────────────────────────────────
class ExotelOTPProvider(BaseOTPProvider):
    """Exotel SMS OTP provider for Indian telecom."""

    def __init__(self):
        provider_config = settings.OTP_PROVIDERS.get('exotel', {})
        self.account_sid = provider_config.get('ACCOUNT_SID', '')
        self.api_key = provider_config.get('API_KEY', '')
        self.api_token = provider_config.get('API_TOKEN', '')
        self.subdomain = provider_config.get('SUBDOMAIN', 'api.exotel.com')
        self.sender_id = provider_config.get('SENDER_ID', 'CIVICAI')

    def send_otp(self, mobile_number: str, otp: str) -> dict:
        try:
            import httpx
            # Exotel SMS API endpoint
            url = f"https://{self.subdomain}/v1/Accounts/{self.account_sid}/Sms/send.json"
            message_body = f"Your Civic AI verification code is {otp}. Valid for 5 minutes. Do not share this OTP."
            response = httpx.post(
                url,
                data={
                    'From': self.sender_id,
                    'To': mobile_number,
                    'Body': message_body,
                },
                auth=(self.api_key, self.api_token),
                timeout=10,
            )
            data = response.json()
            sms_data = data.get('SMSMessage', {})
            status = sms_data.get('Status', '')
            success = response.status_code in [200, 201] and status != 'failed'
            return {
                'success': success,
                'message': status or 'SMS dispatched',
                'provider_reference': sms_data.get('Sid', ''),
            }
        except Exception as e:
            logger.error('Exotel OTP send failed (%s)', type(e).__name__)
            return {'success': False, 'message': 'OTP delivery failed.', 'provider_reference': ''}


# ─── Factory ──────────────────────────────────────────────────────────────────

def get_otp_provider() -> BaseOTPProvider:
    """
    Factory function. Returns the configured OTP provider instance.
    The provider is determined by settings.OTP_PROVIDER.
    """
    provider_name = getattr(settings, 'OTP_PROVIDER', 'mock')
    if provider_name == 'mock' and not getattr(settings, 'OTP_MOCK_ALLOWED', False):
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured('The mock OTP provider is only available when DEBUG is enabled.')
    providers_config = getattr(settings, 'OTP_PROVIDERS', {})
    provider_entry = providers_config.get(provider_name, {})
    backend_path = provider_entry.get('BACKEND', 'apps.accounts.otp.providers.MockOTPProvider')

    # Import and instantiate the backend class dynamically
    module_path, class_name = backend_path.rsplit('.', 1)
    import importlib
    module = importlib.import_module(module_path)
    provider_class = getattr(module, class_name)
    return provider_class()
