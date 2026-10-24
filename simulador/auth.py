import uuid
from datetime import timedelta
from functools import wraps

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone

from .models import TokenRevocado, Usuario


def _encode(user, token_type, lifetime):
    now = timezone.now()
    return jwt.encode({
        'sub': str(user.pk),
        'type': token_type,
        'jti': uuid.uuid4().hex,
        'iat': now,
        'exp': now + lifetime,
    }, settings.JWT_SIGNING_KEY, algorithm='HS256')


def issue_tokens(user):
    return {
        'access': _encode(
            user, 'access', timedelta(minutes=settings.JWT_ACCESS_MINUTES)
        ),
        'refresh': _encode(
            user, 'refresh', timedelta(days=settings.JWT_REFRESH_DAYS)
        ),
    }


def decode_token(token, expected_type=None):
    try:
        payload = jwt.decode(token, settings.JWT_SIGNING_KEY, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    if expected_type and payload.get('type') != expected_type:
        return None
    if TokenRevocado.esta_revocado(payload.get('jti')):
        return None
    return payload


def revoke_token(token):
    payload = decode_token(token)
    if payload:
        TokenRevocado.objects.get_or_create(
            jti=payload['jti'],
            defaults={'expira_en': timezone.datetime.fromtimestamp(
                payload['exp'], tz=timezone.get_current_timezone()
            )},
        )


def token_from_request(request):
    value = request.headers.get('Authorization', '')
    return value[7:].strip() if value.lower().startswith('bearer ') else None


def user_from_request(request):
    token = token_from_request(request)
    if token:
        payload = decode_token(token, 'access')
        if payload:
            return Usuario.objects.filter(pk=payload.get('sub'), activo=True).first()
        return None
    profile = request.session.get('demo_profile')
    if profile:
        return Usuario.objects.filter(pk=profile.get('id'), activo=True).first()
    return None


def api_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        user = user_from_request(request)
        if not user:
            return JsonResponse({'detail': 'Autenticación requerida.'}, status=401)
        request.authenticated_user = user
        return view(request, *args, **kwargs)
    return wrapped


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            user = user_from_request(request)
            if not user:
                if request.path.startswith('/api/'):
                    return JsonResponse({'detail': 'Autenticación requerida.'}, status=401)
                return redirect(f'/login/?next={request.path}')
            if not user.has_permission(permission):
                if request.path.startswith('/api/'):
                    return JsonResponse({'detail': 'No tienes permiso para esta acción.'}, status=403)
                return JsonResponse({'detail': 'No tienes permiso para esta acción.'}, status=403)
            request.authenticated_user = user
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
