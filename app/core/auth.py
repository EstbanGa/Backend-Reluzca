"""
Configuración central de autenticación OAuth2
"""
from fastapi.security import OAuth2PasswordBearer

# Esquema OAuth2 centralizado - UNA SOLA INSTANCIA para toda la aplicación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
