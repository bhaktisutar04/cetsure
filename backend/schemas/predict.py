# """
# predict.py — Pydantic schemas for prediction endpoint (F3)
# """

# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict, Any


# class PredictRequest(BaseModel):
#     percentile: float = Field(
#         ...,
#         ge=0.0,
#         le=100.0,
#         description="Student MHT-CET percentile (must be between 0 and 100)",
#     )
#     category: str = Field(..., description="Admission category e.g. GOPENS, GOBCS")
#     branch: str = Field(..., description="Preferred branch or discipline")
#     district: Optional[str] = Field(None, description="Optional district filter")
#     quota: str = Field("MH", description="Admission quota: MH (Maharashtra) or AI (All India)")


# class CollegePrediction(BaseModel):
#     college_code: str
#     college_name: str
#     branch_name: str
#     weighted_cutoff: float
#     cutoff_2022: Optional[float] = None
#     cutoff_2023: Optional[float] = None
#     cutoff_2024: Optional[float] = None
#     cutoff_2025: Optional[float] = None
#     trend: str
#     data_years: int
#     bucket: str


# class PredictionMeta(BaseModel):
#     percentile: float
#     category: str
#     branch: str
#     district: Optional[str] = None
#     total_colleges: int


# class PredictResponse(BaseModel):
#     safe: List[CollegePrediction]
#     moderate: List[CollegePrediction]
#     reach: List[CollegePrediction]
#     meta: PredictionMeta
from pydantic import BaseModel, Field
from typing import Optional, List


class PredictRequest(BaseModel):
    percentile: float = Field(..., ge=0.0, le=100.0)
    category: str
    branch: str
    district: Optional[str] = None
    quota: str = "MH"


class CollegePrediction(BaseModel):
    college_code: str
    college_name: str
    district: Optional[str] = None
    branch_name: str

    weighted_cutoff: float
    last_year_cutoff: Optional[float] = None

    cutoff_2022: Optional[float] = None
    cutoff_2023: Optional[float] = None
    cutoff_2024: Optional[float] = None
    cutoff_2025: Optional[float] = None

    trend: str
    data_years: int
    chance_score: int
    reason: str
    bucket: str


class PredictionMeta(BaseModel):
    percentile: float
    category: str
    branch: str
    district: Optional[str] = None
    quota: str = "MH"
    total_colleges: int


class PredictResponse(BaseModel):
    safe: List[CollegePrediction]
    moderate: List[CollegePrediction]
    reach: List[CollegePrediction]
    meta: PredictionMeta