from fastapi.middleware.cors import CORSMiddleware

from config import settings


def apply_cors(app):
    origins = (
        [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",")]
        if settings.CORS_ALLOW_ORIGINS
        else ["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
