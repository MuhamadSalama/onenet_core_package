from fastapi import APIRouter, Depends
from datetime import timedelta
from ..schemas import WalletBalanceResponse, TransactionListResponse, TransactionItem, UserRead
from ..dependencies import require_permissions, get_current_user
from ..utils.security import _now
from ..logger import get_logger

logger = get_logger(__name__)

router_wallet = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])

@router_wallet.get(
    "/balance",
    response_model=WalletBalanceResponse,
    dependencies=[Depends(require_permissions(["wallet:read"]))],
)
def get_balance(user: UserRead = Depends(get_current_user)):
    # Simple demo data depending on user
    if "admin" in user.roles:
        available = 250000.50
        ledger = 250500.50
    else:
        available = 1500.75
        ledger = 1600.75

    logger.info(f"Wallet balance retrieved for user {user.email} (ID: {user.id})")
    
    return WalletBalanceResponse(
        currency="SAR",
        available=available,
        ledger=ledger,
        last_updated=_now(),
    )


@router_wallet.get(
    "/transactions",
    response_model=TransactionListResponse,
    dependencies=[Depends(require_permissions(["wallet:read"]))],
)
def get_transactions(user: UserRead = Depends(get_current_user)):
    now = _now()
    items = [
        TransactionItem(
            id="TX-001",
            type="CREDIT",
            amount=500.0,
            currency="SAR",
            description="QR Payment – Coffee Shop",
            created_at=now - timedelta(minutes=15),
        ),
        TransactionItem(
            id="TX-002",
            type="DEBIT",
            amount=-200.0,
            currency="SAR",
            description="Wallet Transfer – Friend",
            created_at=now - timedelta(hours=1),
        ),
        TransactionItem(
            id="TX-003",
            type="CREDIT",
            amount=1500.0,
            currency="SAR",
            description="Salary – Employer",
            created_at=now - timedelta(days=1),
        ),
    ]
    
    logger.info(
        f"Wallet transactions retrieved for user {user.email} (ID: {user.id}), "
        f"returned {len(items)} transactions"
    )
    
    return TransactionListResponse(items=items)
