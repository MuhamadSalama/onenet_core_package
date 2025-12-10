from fastapi import APIRouter
from ..schemas import HealthResponse, ConfigResponse, FeatureFlag
from ..utils.security import _now

router_meta = APIRouter(prefix="/meta", tags=["meta"])

@router_meta.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        success=True,
        data={
            "status": "healthy",
            "database": "healthy",
            "redis": "healthy",
            "timestamp": _now().isoformat(),
        },
    )


@router_meta.get("/config", response_model=ConfigResponse)
def get_config():
    flags = [
        FeatureFlag(
            name="wallet.qr_payments",
            enabled=True,
            description="Enable QR payments UI.",
        ),
        FeatureFlag(
            name="wallet.fx_tab",
            enabled=False,
            description="Experimental FX swap feature.",
        ),
        FeatureFlag(
            name="ops.risk_console",
            enabled=True,
            description="Risk console for admin users only.",
        ),
    ]
    return ConfigResponse(
        environment="dev",
        version="1.0.0-demo",
        feature_flags=flags,
    )
