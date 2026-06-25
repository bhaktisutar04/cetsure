"""
college.py — FastAPI router for college endpoints (F3)
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy import text
from backend.schemas.college import CollegeDetailResponse, CollegeSearchResponse, CutoffDetail, CollegeSearchResult
from backend.prediction.predict import _get_engine
from backend.auth.firebase_auth import get_current_user
import logging
logger = logging.getLogger(__name__)
router = APIRouter(tags=["college"])


@router.get(
    "/college/{college_code}",
    response_model=CollegeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get college details and historical cutoffs",
    description="Returns the full profile and historical allotment cutoff records for a given unique college code.",
)
async def get_college_details(college_code: str, current_user: dict = Depends(get_current_user)):
    try:
        engine = _get_engine()
        query = text("""
            SELECT college_name, branch_name, category, year, cap_round, 
                   closing_percentile, closing_rank 
            FROM cutoffs 
            WHERE college_code = :college_code 
            ORDER BY year DESC, cap_round ASC, branch_name ASC, category ASC
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"college_code": college_code})
            rows = [dict(row._mapping) for row in result]
            
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"College with code '{college_code}' not found."
            )
            
        # Get college name from the first record
        college_name = rows[0]["college_name"]
        
        cutoffs = []
        for row in rows:
            cutoffs.append(
                CutoffDetail(
                    branch_name=row["branch_name"],
                    category=row["category"],
                    year=row["year"],
                    cap_round=row["cap_round"],
                    closing_percentile=row["closing_percentile"],
                    closing_rank=row["closing_rank"],
                )
            )
            
        return CollegeDetailResponse(
            college_code=college_code,
            college_name=college_name,
            cutoffs=cutoffs,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"College error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong. Please try again.",
        )


@router.get(
    "/search",
    response_model=CollegeSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search colleges by name or code",
    description="Enables searching and autocompleting colleges by name or unique college code.",
)
async def search_colleges(
    q: str = Query(..., min_length=2, description="Search query string (minimum 2 characters)"),
    current_user: dict = Depends(get_current_user)
):
    try:
        engine = _get_engine()
        
        query = text("""
            SELECT DISTINCT college_code, college_name 
            FROM cutoffs 
            WHERE LOWER(college_name) LIKE LOWER(:q) 
               OR college_code LIKE :q 
            ORDER BY college_name ASC
            LIMIT 50
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"q": f"%{q}%"})
            rows = [dict(row._mapping) for row in result]
            
        results = [
            CollegeSearchResult(
                college_code=row["college_code"],
                college_name=row["college_name"],
            )
            for row in rows
        ]
        
        return CollegeSearchResponse(results=results)
        
    except Exception as e:
        logger.error(f"College error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong. Please try again.",
        )
