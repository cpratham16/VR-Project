from fastapi import APIRouter
from app.api.v1 import health, auth, patient, screening, mood, doctor, chat, panic, doctor_alerts, community, doctor_moderation, doctor_vr, patient_vr, admin

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(patient.router, prefix="/patient", tags=["patient"])
api_router.include_router(screening.router, prefix="/patient/screening", tags=["screening"])
api_router.include_router(mood.router, prefix="/patient/mood", tags=["mood"])
api_router.include_router(chat.router, prefix="/patient/chat", tags=["chat"])
api_router.include_router(panic.router, prefix="/patient/panic", tags=["panic"])
api_router.include_router(community.router, prefix="/community", tags=["community"])
api_router.include_router(doctor.router, prefix="/doctor", tags=["doctor"])
api_router.include_router(doctor_alerts.router, prefix="/doctor/alerts", tags=["doctor_alerts"])
api_router.include_router(doctor_moderation.router, prefix="/doctor/moderation", tags=["doctor_moderation"])
api_router.include_router(doctor_vr.router, prefix="/doctor/vr", tags=["doctor_vr"])
api_router.include_router(patient_vr.router, prefix="/patient/vr", tags=["patient_vr"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
