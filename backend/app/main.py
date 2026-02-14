from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title="CareOps MVP", version="0.1.0")

from fastapi.middleware.cors import CORSMiddleware
from app.api.onboarding import router as onboarding_router
from app.api.bookings import router as bookings_router
from app.api.auth import router as auth_router
from app.api.cron import router as cron_router
from app.api.public import router as public_router
from app.api.conversations import router as conversations_router
from app.api.dashboard import router as dashboard_router
from app.api.staff import router as staff_router
from app.api.communications import router as communications_router
from app.api.validation import router as validation_router
from app.api.signup import router as signup_router
from app.api.leads import router as leads_router
from app.api.lead_conversion import router as lead_conversion_router
from app.api.auth_google import router as auth_google_router
from app.api.inbox import router as inbox_router

# Add CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

# Allow the configured FRONTEND_URL (e.g. LAN IP or Production Domain)
if settings.FRONTEND_URL and settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup readiness automation
from app.core.readiness import auto_seed_if_needed, print_readiness_report

@app.on_event("startup")
async def startup_event():
    """Run readiness checks and auto-seed on startup"""
    # auto_seed_if_needed()  # Disabled for production deployment
    print_readiness_report()

app.include_router(signup_router, prefix="/api", tags=["signup"])
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(leads_router, prefix="/api", tags=["leads"])
app.include_router(lead_conversion_router, prefix="/api", tags=["lead_conversion"])
app.include_router(auth_google_router, prefix="/api", tags=["auth_google"])
app.include_router(inbox_router, prefix="/api", tags=["inbox"])
app.include_router(onboarding_router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(bookings_router, prefix="/api/bookings", tags=["bookings"])
app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(staff_router, prefix="/api/staff", tags=["staff"])
app.include_router(cron_router, prefix="/api/cron", tags=["cron"])
app.include_router(public_router, prefix="/api/public", tags=["public"])
app.include_router(communications_router, prefix="/api/communications", tags=["communications"])
app.include_router(validation_router, prefix="/api/validation", tags=["validation"])

from app.api.settings import router as settings_router
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])

from app.api.inventory import router as inventory_router
app.include_router(inventory_router, prefix="/api/inventory", tags=["inventory"])

from app.api.forms import router as forms_router
app.include_router(forms_router, prefix="/api/forms", tags=["forms"])

from app.api.services import router as services_router
app.include_router(services_router, prefix="/api/services", tags=["services"])

from app.api.debug import router as debug_router
app.include_router(debug_router, prefix="/api/debug", tags=["debug"])

@app.get("/")
async def root():
    return {"message": "Welcome to CareOps API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
