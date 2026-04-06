import functools
import jwt
import requests
from flask import request, g, jsonify
from app.config import Config

# Cache for Supabase JWKS
_jwks_cache = None


def _get_jwks():
    """Fetch Supabase JWKS for JWT verification."""
    global _jwks_cache
    if _jwks_cache is None:
        jwks_url = f"{Config.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        response = requests.get(jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def _decode_token(token: str) -> dict:
    """Decode and verify a Supabase JWT token."""
    try:
        jwks = _get_jwks()
        # Get the signing key
        header = jwt.get_unverified_header(token)
        key = None
        for jwk_key in jwks.get("keys", []):
            if jwk_key.get("kid") == header.get("kid"):
                if jwk_key.get("kty") == "RSA":
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk_key)
                break

        if key is None:
            # Fallback: We can't trust SUPABASE_ANON_KEY as the secret for users, 
            # but we can do an unverified decode or catch all exceptions if it fails.
            # In a real app we need the JWT_SECRET from Supabase to verify HS256 locally.
            try:
                payload = jwt.decode(
                    token,
                    Config.SUPABASE_ANON_KEY,
                    algorithms=["HS256"],
                    audience="authenticated",
                )
            except Exception:
                # Se não conseguir decodificar com a Anon Key (comum, pois a chave certa é o JWT Secret),
                # vamos usar o cliente oficial do Supabase para verificar
                from app.extensions import get_supabase
                sb = get_supabase()
                user_res = sb.auth.get_user(token)
                if getattr(user_res, "user", None):
                    return {
                        "sub": user_res.user.id,
                        "email": user_res.user.email,
                        "user_metadata": user_res.user.user_metadata if hasattr(user_res.user, 'user_metadata') else {}
                    }
                return None
        else:
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience="authenticated",
            )
        return payload
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


def require_auth(f):
    """Decorator to require valid Supabase JWT authentication."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token de autenticação ausente"}), 401

        token = auth_header.split(" ", 1)[1]
        payload = _decode_token(token)

        if payload is None:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verify email domain restriction
        email = payload.get("email", "")
        if not email.endswith("@mendoncagalvao.com.br"):
            return jsonify({"error": "Acesso restrito ao domínio mendoncagalvao.com.br"}), 403

        g.user_id = payload.get("sub")
        g.user_email = email
        g.user_role = payload.get("user_metadata", {}).get("role", "developer")
        g.token = token

        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator to require admin role."""
    @functools.wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        from app.extensions import get_supabase
        sb = get_supabase()
        user = sb.table("users").select("role").eq("id", g.user_id).single().execute()
        if not user.data or user.data.get("role") != "admin":
            return jsonify({"error": "Acesso restrito a administradores"}), 403
        return f(*args, **kwargs)
    return decorated
