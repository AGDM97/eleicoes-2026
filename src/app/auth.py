"""
Autenticação e autorização para FastAPI.

Se API_KEY está vazia, endpoints são públicos.
Caso contrário, requer header Authorization: Bearer <API_KEY>.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from .config import API_KEY


def check_api_key(authorization: str | None = Header(None)) -> None:
    """
    Valida o token de autenticação.
    
    Args:
        authorization: Header Authorization da requisição.
    
    Raises:
        HTTPException: Se API_KEY está definida e token é inválido.
    """
    if not API_KEY:
        # API pública: sem autenticação necessária
        return
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente",
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato inválido. Use: Authorization: Bearer <token>",
        )
    
    token = parts[1]
    if token != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token inválido",
        )
