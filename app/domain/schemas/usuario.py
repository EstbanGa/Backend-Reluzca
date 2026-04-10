from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class UsuarioBase(BaseModel):
    """Schema base para Usuario con todos los campos de Django"""
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    correo: EmailStr = Field(..., alias="email")  # Acepta "email" del frontend, usa "correo" internamente
    documento: Optional[str] = Field(None, max_length=20)
    telefono: str = Field(..., max_length=15)
    tipo_persona: Optional[str] = Field(None, max_length=20)  # natural, juridica
    fecha_nacimiento: Optional[date] = None
    rol: str = Field(default="cliente", max_length=20)  # admin, cliente, empleada
    estado: str = Field(default="pendiente", max_length=20)  # activo, inactivo, pendiente
    ranking: Optional[Decimal] = Field(None, max_digits=3, decimal_places=2)  # Para empleadas
    
    model_config = {
        "populate_by_name": True  # Permite usar tanto "email" como "correo"
    }


class UsuarioCreate(UsuarioBase):
    """Schema para crear usuario - incluye password"""
    password: str = Field(..., min_length=6)


class UsuarioUpdate(BaseModel):
    """Schema para actualizar usuario - todos los campos opcionales"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(None, min_length=1, max_length=100)
    correo: Optional[EmailStr] = Field(None, alias="email")  # Acepta "email" del frontend
    documento: Optional[str] = Field(None, max_length=20)
    telefono: Optional[str] = Field(None, max_length=15)
    tipo_persona: Optional[str] = Field(None, max_length=20)
    fecha_nacimiento: Optional[date] = None
    rol: Optional[str] = Field(None, max_length=20)
    estado: Optional[str] = Field(None, max_length=20)
    ranking: Optional[Decimal] = Field(None, max_digits=3, decimal_places=2)
    password: Optional[str] = Field(None, min_length=6)
    
    model_config = {
        "populate_by_name": True  # Permite usar tanto "email" como "correo"
    }


class UsuarioResponse(BaseModel):
    """Schema de respuesta con TODOS los campos de Django"""
    id: UUID
    rol: str
    fecha_registro: Optional[datetime] = None
    nombre: str
    apellido: str
    email: EmailStr  # Se llama "email" en la respuesta
    documento: Optional[str] = None
    telefono: str
    tipo_persona: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    estado: str
    ranking: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Override para mapear correo -> email"""
        if hasattr(obj, 'correo') and not hasattr(obj, 'email'):
            obj.email = obj.correo
        return super().model_validate(obj, **kwargs)


class UsuarioLogin(BaseModel):
    """Schema para login"""
    correo: EmailStr = Field(..., alias="email")  # Acepta "email" del frontend
    password: str
    
    model_config = {
        "populate_by_name": True
    }


class Token(BaseModel):
    """Schema para token JWT"""
    access_token: str
    token_type: str = "bearer"
    user: Optional['UsuarioResponse'] = None  # Información del usuario logueado


class TokenData(BaseModel):
    """Datos decodificados del token"""
    correo: Optional[str] = Field(None, alias="email")  # Acepta tanto "email" como "correo"
    rol: Optional[str] = None
    
    model_config = {
        "populate_by_name": True
    }


class UsuariosEstadisticas(BaseModel):
    """Estadísticas de usuarios por rol"""
    total: int
    admins: int
    clientes: int
    empleadas: int
    activos: int
    inactivos: int
    pendientes: int


class UsuariosRolResponse(BaseModel):
    """Respuesta con usuarios de un rol específico y estadísticas"""
    usuarios: List[UsuarioResponse]
    estadisticas: UsuariosEstadisticas


class UsuarioCompleteResponse(BaseModel):
    """Schema de respuesta con TODA la información del usuario (perfil + reservas + ubicaciones)"""
    # Información del usuario
    id: UUID
    rol: str
    fecha_registro: Optional[datetime] = None
    nombre: str
    apellido: str
    email: EmailStr  # Se llama "email" en la respuesta
    documento: Optional[str] = None
    telefono: str
    tipo_persona: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    estado: str
    ranking: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Reservas (como cliente o empleada)
    reservas_cliente: Optional[list] = []
    reservas_empleada: Optional[list] = []
    
    # Ubicaciones
    ubicaciones: Optional[list] = []
    ubicaciones_empleada: Optional[list] = []
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
