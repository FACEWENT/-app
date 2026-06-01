from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.institutions import router as institutions_router
from app.api.meta import router as meta_router
from app.api.offerings import router as offerings_router
from app.api.programs import router as programs_router
from app.api.recommendations import router as recommendations_router
from app.api.users import router as users_router
from app.api.favorites import router as favorites_router
from app.api.browsing import router as browsing_router
from app.api.transfer import router as transfer_router
from app.api.social import router as social_router
from app.api.study import router as study_router
from app.api.tutoring import router as tutoring_router
from app.api.moments import router as moments_router
from app.api.experience import router as experience_router
from app.api.soul_matching import router as soul_matching_router

app = FastAPI(title="Graduate School Data System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta_router)
app.include_router(institutions_router)
app.include_router(programs_router)
app.include_router(offerings_router)
app.include_router(recommendations_router)
app.include_router(ai_router)
app.include_router(users_router)
app.include_router(favorites_router)
app.include_router(browsing_router)
app.include_router(transfer_router)
app.include_router(social_router)
app.include_router(study_router)
app.include_router(tutoring_router)
app.include_router(moments_router)
app.include_router(experience_router)
app.include_router(soul_matching_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
