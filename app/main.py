
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import engine
from app.models import PendingSupportAction

from app.api.admin_auth import router as admin_auth_router
from app.api.customer_auth import router as customer_auth_router
from app.api.products import router as products_router
from app.api.product_documents import router as product_documents_router
from app.api.cart import router as cart_router
from app.api.orders import router as orders_router
from app.api.knowledge import router as knowledge_router
from app.api.chat import router as chat_router
from app.api.support_tickets import router as support_tickets_router
from app.api.admin.orders import router as admin_orders_router
from app.api import support_tickets
from app.api.admin_support_tickets import router as admin_support_tickets_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    PendingSupportAction.__table__.create(
        bind=engine,
        checkfirst=True,
    )
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(admin_auth_router)
app.include_router(customer_auth_router)
app.include_router(products_router)
app.include_router(product_documents_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(knowledge_router)
app.include_router(chat_router)
app.include_router(support_tickets_router)
app.include_router(admin_orders_router)
app.include_router(support_tickets.router)
app.include_router(admin_support_tickets_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "application": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
