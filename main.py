from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.infrastructure.database import engine, Base
from app.presentation.api.v1 import (
    auth_router,
    usuarios_router,
    planes_router,
    reservas_router,
    ubicaciones_router,
    dashboard_router,
    notificaciones_router,
    pqrs_router,
    calificaciones_router
)

# Crear las tablas en la base de datos (descomentado cuando tengas DB configurada)
# Base.metadata.create_all(bind=engine)

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API Backend para Reluzca - Sistema de gestión de servicios de limpieza",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False  # Deshabilitar redirects para evitar loops en Lambda
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes en desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar los routers
app.include_router(auth_router, prefix="/api")
app.include_router(usuarios_router, prefix="/api")
app.include_router(planes_router, prefix="/api")
app.include_router(reservas_router, prefix="/api")
app.include_router(ubicaciones_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(notificaciones_router, prefix="/api")
app.include_router(pqrs_router, prefix="/api")
app.include_router(calificaciones_router, prefix="/api")

# Debug: imprimir rutas registradas



@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "message": "Bienvenido a la API de Reluzca",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/api/health")
def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
