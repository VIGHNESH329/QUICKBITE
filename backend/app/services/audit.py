import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import AuditLog

logger = logging.getLogger("quickbite.audit")

class AuditService:
    """
    Append-only security audit logging service.
    Persists immutable audit records for non-repudiation and forensic audit trails.
    """
    @staticmethod
    def log(
        db: Session,
        action_type: str,
        entity_name: str,
        user_id: Optional[int] = None,
        entity_id: Optional[int] = None,
        status_result: str = "SUCCESS",
        client_ip: Optional[str] = None,
        details_json: Optional[str] = None
    ) -> AuditLog:
        try:
            entry = AuditLog(
                user_id=user_id,
                action_type=action_type,
                entity_name=entity_name,
                entity_id=entity_id,
                status_result=status_result,
                client_ip=client_ip,
                details_json=details_json
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            logger.info(f"AUDIT: [{status_result}] action={action_type} user={user_id} entity={entity_name}:{entity_id}")
            return entry
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record audit log: {str(e)}")
            raise e
