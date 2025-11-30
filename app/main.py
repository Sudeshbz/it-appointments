from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi  # önemli

from .database import Base, engine
from . import models
from .routers import auth, companies, services, appointments

# Tabloları oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-tenant IT Appointment System",
    version="0.1.0",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="IT Appointment API",
        routes=app.routes,
    )
    # Burada Bearer Token şemasını açıkça tanımlıyoruz
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
        }
    }
    for route in openapi_schema["paths"].values():
        for method in route.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def root():
    return {"message": "IT Appointment API çalışıyor"}


app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(services.router)
app.include_router(appointments.router)
