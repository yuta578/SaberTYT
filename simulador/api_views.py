import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .auth import (
    api_login_required, decode_token, issue_tokens, revoke_token,
    token_from_request,
)
from .models import Usuario


def _body(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return {}


@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Método no permitido.'}, status=405)
    data = _body(request)
    identifier = str(data.get('username') or data.get('email') or '').strip()
    password = str(data.get('password') or '')
    user = Usuario.objects.filter(email__iexact=identifier).first()
    if not user:
        user = Usuario.objects.filter(codigo_institucional__iexact=identifier).first()
    if not user or not user.activo or not user.check_password(password):
        return JsonResponse({'detail': 'Credenciales inválidas.'}, status=401)
    return JsonResponse({
        'tokens': issue_tokens(user),
        'user': {
            'id': user.pk,
            'username': user.email,
            'name': user.nombre_completo,
            'role': user.rol,
            'custom_role': user.rol_personalizado.nombre if user.rol_personalizado_id else None,
        },
    })


@csrf_exempt
def refresh(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Método no permitido.'}, status=405)
    token = _body(request).get('refresh')
    payload = decode_token(token or '', 'refresh')
    user = Usuario.objects.filter(pk=payload.get('sub'), activo=True).first() if payload else None
    if not user:
        return JsonResponse({'detail': 'Token de renovación inválido.'}, status=401)
    revoke_token(token)
    return JsonResponse({'tokens': issue_tokens(user)})


@csrf_exempt
@api_login_required
def logout(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Método no permitido.'}, status=405)
    token = token_from_request(request)
    if token:
        revoke_token(token)
    refresh_token = _body(request).get('refresh')
    if refresh_token:
        revoke_token(refresh_token)
    return JsonResponse({'detail': 'Sesión cerrada correctamente.'})


@api_login_required
def me(request):
    user = request.authenticated_user
    return JsonResponse({
        'id': user.pk,
        'name': user.nombre_completo,
        'email': user.email,
        'role': user.rol,
        'active': user.activo,
    })
