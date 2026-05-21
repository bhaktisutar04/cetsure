"""
college.py — Pydantic schemas for college detail and search endpoints (F3)
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class CutoffDetail(BaseModel):
    branch_name: str
    category: str
    year: int
    cap_round: int
    closing_percentile: Optional[float] = None
    closing_rank: Optional[int] = None


class CollegeDetailResponse(BaseModel):
    college_code: str
    college_name: str
    cutoffs: List[CutoffDetail]


class CollegeSearchResult(BaseModel):
    college_code: str
    college_name: str


class CollegeSearchResponse(BaseModel):
    results: List[CollegeSearchResult]
