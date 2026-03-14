from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, AsyncGenerator

from datalayer.database import get_db
from services import ResultsService

router = APIRouter(prefix="/results", tags=["Results"])


class TrialData(BaseModel):
    """Model for trial data from jsPsych"""
    trial_index: int
    rt: float | None = None
    response: str | None = None
    task_type: str | None = None
    sentence_id: str | None = None
    word: str | None = None
    word_position: int | None = None
    condition: str | None = None
    sentence: str | None = None
    is_grammatical: bool | None = None
    attrition_marker: str | None = None
    accuracy: int | None = None
    correct_answer: str | None = None

    class Config:
        extra = "allow"  # Allow additional fields from jsPsych


class ResultsSubmissionRequest(BaseModel):
    """Request model for submitting test results"""
    participant_name: str
    trials: List[Dict[str, Any]]


class ResultsSubmissionResponse(BaseModel):
    """Response model for results submission"""
    participant_id: str
    message: str
    trial_count: int


@router.post("/spr", response_model=ResultsSubmissionResponse)
async def submit_spr_results(
    request: ResultsSubmissionRequest,
    db: AsyncClient = Depends(get_db),
) -> ResultsSubmissionResponse:
    """
    Submit Self-Paced Reading (SPR) test results.

    Args:
        request: Participant name and trial data
        db: Firestore database client

    Returns:
        Confirmation with participant_id
    """
    try:
        if not request.participant_name or not request.participant_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participant name is required",
            )

        if not request.trials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one trial result is required",
            )

        service = ResultsService(db)
        participant_id = await service.save_session(
            request.participant_name,
            "spr",
            request.trials,
        )

        return ResultsSubmissionResponse(
            participant_id=participant_id,
            message=f"SPR test results for '{request.participant_name}' saved successfully",
            trial_count=len([t for t in request.trials if t.get("trial_index") is not None]),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting SPR results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save results",
        )


@router.post("/gj", response_model=ResultsSubmissionResponse)
async def submit_gj_results(
    request: ResultsSubmissionRequest,
    db: AsyncClient = Depends(get_db),
) -> ResultsSubmissionResponse:
    """
    Submit Grammatical Judgment (GJ) test results.

    Args:
        request: Participant name and trial data
        db: Firestore database client

    Returns:
        Confirmation with participant_id
    """
    try:
        if not request.participant_name or not request.participant_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participant name is required",
            )

        if not request.trials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one trial result is required",
            )

        service = ResultsService(db)
        participant_id = await service.save_session(
            request.participant_name,
            "gj",
            request.trials,
        )

        return ResultsSubmissionResponse(
            participant_id=participant_id,
            message=f"GJ test results for '{request.participant_name}' saved successfully",
            trial_count=len([t for t in request.trials if t.get("trial_index") is not None]),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting GJ results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save results",
        )
