from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.domain.models.usuario import Usuario
from app.domain.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def get_by_email(self, email: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.correo == email).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        return self.db.query(Usuario).offset(skip).limit(limit).all()

    def get_by_rol(self, rol: str, skip: int = 0, limit: int = 100) -> List[Usuario]:
        return self.db.query(Usuario).filter(Usuario.rol == rol).offset(skip).limit(limit).all()

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Usuario]:
        search_filter = or_(
            Usuario.nombre.ilike(f"%{query}%"),
            Usuario.apellido.ilike(f"%{query}%"),
            Usuario.correo.ilike(f"%{query}%")
        )
        return self.db.query(Usuario).filter(search_filter).offset(skip).limit(limit).all()

    def create(self, usuario_data: UsuarioCreate, hashed_password: str) -> Usuario:
        """Crea un nuevo usuario con todos los campos de Django"""
        # Default estado: clientes empiezan en "pendiente", empleadas/admins en "activo"
        default_estado = "pendiente" if usuario_data.rol == "cliente" else "activo"
        
        from datetime import datetime
        
        db_usuario = Usuario(
            correo=usuario_data.correo,
            password=hashed_password,
            nombre=usuario_data.nombre,
            apellido=usuario_data.apellido,
            telefono=usuario_data.telefono,
            documento=usuario_data.documento,
            tipo_persona=usuario_data.tipo_persona,
            fecha_nacimiento=usuario_data.fecha_nacimiento,
            rol=usuario_data.rol,
            estado=usuario_data.estado or default_estado,
            ranking=usuario_data.ranking,
            fecha_registro=datetime.utcnow()
        )
        self.db.add(db_usuario)
        self.db.commit()
        self.db.refresh(db_usuario)
        return db_usuario

    def update(self, usuario_id: int, usuario_data: UsuarioUpdate, hashed_password: Optional[str] = None) -> Optional[Usuario]:
        """Actualiza un usuario con validación de campo correo"""
        db_usuario = self.get_by_id(usuario_id)
        if not db_usuario:
            return None

        update_data = usuario_data.model_dump(exclude_unset=True)
        
        # Si hay password nuevo, usar el hash proporcionado
        if hashed_password:
            update_data["password"] = hashed_password
        elif "password" in update_data:
            del update_data["password"]
        
        # Mapear correo si viene como email
        if "email" in update_data:
            update_data["correo"] = update_data.pop("email")

        for field, value in update_data.items():
            if hasattr(db_usuario, field):
                setattr(db_usuario, field, value)

        self.db.commit()
        self.db.refresh(db_usuario)
        return db_usuario

    def delete(self, usuario_id: int) -> bool:
        db_usuario = self.get_by_id(usuario_id)
        if not db_usuario:
            return False

        self.db.delete(db_usuario)
        self.db.commit()
        return True

    def deactivate(self, usuario_id: int) -> Optional[Usuario]:
        db_usuario = self.get_by_id(usuario_id)
        if not db_usuario:
            return None

        db_usuario.estado = "inactivo"
        self.db.commit()
        self.db.refresh(db_usuario)
        return db_usuario
