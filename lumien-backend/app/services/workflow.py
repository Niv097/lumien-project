from typing import List
from ..models.models import CaseStatus, Complaint
from fastapi import HTTPException

class WorkflowService:
    VALID_TRANSITIONS = {
        CaseStatus.INGESTED: [CaseStatus.ENRICHED],
        CaseStatus.ENRICHED: [
            CaseStatus.ROUTED, 
            CaseStatus.NOT_RELATED, 
            CaseStatus.BANK_CONFIRMED,
            CaseStatus.HOLD_INITIATED,
            CaseStatus.ALREADY_FROZEN
        ],
        CaseStatus.ROUTED: [
            CaseStatus.BANK_PENDING,
            CaseStatus.BANK_CONFIRMED, 
            CaseStatus.RELATED_CONFIRMED,
            CaseStatus.HOLD_INITIATED,
            CaseStatus.NOT_RELATED, 
            CaseStatus.ALREADY_FROZEN,
            CaseStatus.FUNDS_MOVED
        ],
        CaseStatus.UNDER_REVIEW: [
            CaseStatus.RELATED_CONFIRMED,
            CaseStatus.HOLD_INITIATED,
            CaseStatus.NOT_RELATED,
            CaseStatus.ALREADY_FROZEN
        ],
        CaseStatus.RELATED_CONFIRMED: [
            CaseStatus.HOLD_INITIATED,
            CaseStatus.NOT_RELATED,
            CaseStatus.CLOSED
        ],
        CaseStatus.BANK_PENDING: [
            CaseStatus.BANK_CONFIRMED, 
            CaseStatus.NOT_RELATED, 
            CaseStatus.ALREADY_FROZEN,
            CaseStatus.FUNDS_MOVED
        ],
        CaseStatus.BANK_CONFIRMED: [
            CaseStatus.HOLD_INITIATED,
            CaseStatus.HOLD_CONFIRMED,
            CaseStatus.PARTIAL_HOLD,
            CaseStatus.CLOSED_NO_FUNDS
        ],
        CaseStatus.HOLD_INITIATED: [CaseStatus.HOLD_CONFIRMED, CaseStatus.CLOSED_SUCCESS, CaseStatus.RECONCILED],
        CaseStatus.HOLD_CONFIRMED: [CaseStatus.RECONCILED, CaseStatus.CLOSED_SUCCESS],
        CaseStatus.PARTIAL_HOLD: [CaseStatus.RECONCILED],
        CaseStatus.ALREADY_FROZEN: [CaseStatus.CLOSED_SUCCESS],
        CaseStatus.FUNDS_MOVED: [CaseStatus.NOT_RELATED, CaseStatus.CLOSED_NO_FUNDS],
        CaseStatus.NOT_RELATED: [CaseStatus.ENRICHED, CaseStatus.ROUTED],
    }

    def validate_transition(self, current_status: CaseStatus, target_status: CaseStatus):
        if target_status == current_status:
            return True
            
        allowed = self.VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid state transition from {current_status} to {target_status}"
            )
        return True

workflow_service = WorkflowService()
