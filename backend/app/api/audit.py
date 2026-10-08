from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import AuditLog, User
from app.schemas.schemas import AuditLogDTO
from app.api.deps import require_admin

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/logs", response_model=List[AuditLogDTO])
def get_audit_logs(
    limit: int = 100,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint providing read-only access to tamper-evident audit ledger."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs
