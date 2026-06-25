"""
predict.py — FastAPI router for prediction endpoint (F3)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from backend.schemas.predict import PredictRequest, PredictResponse
from backend.prediction.predict import predict
from backend.auth.firebase_auth import get_current_user
import logging
logger = logging.getLogger(__name__)
router = APIRouter(tags=["prediction"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict college admission chances",
    description="Takes a student's MHT-CET percentile, reservation category, branch interest, and optional filters, and yields a categorised Safe / Moderate / Reach list of matching colleges.",
)
async def get_prediction(req: PredictRequest, current_user: dict = Depends(get_current_user)):
    try:
        res = predict(
            percentile=req.percentile,
            category=req.category,
            branch=req.branch,
            district=req.district,
            quota=req.quota,
            cap_round=req.cap_round,
        )
        return res
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong. Please try again.",
        )