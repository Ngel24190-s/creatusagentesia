"""AI Agents API routes for farm intelligence."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.agents.farm_agent import FarmAgent

router = APIRouter(prefix="/agents", tags=["agents"])


class QuestionRequest(BaseModel):
    question: str


@router.get("/farm-health")
async def get_farm_health(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Get AI-computed farm health score and diagnostics."""
    agent = FarmAgent(db)
    return await agent.get_health_score()


@router.get("/recommendations")
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Get AI-generated actionable recommendations."""
    agent = FarmAgent(db)
    return await agent.get_recommendations()


@router.get("/forecast")
async def get_forecast(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Get production and revenue forecasts."""
    agent = FarmAgent(db)
    return await agent.get_forecast()


@router.post("/ask")
async def ask_agent(
    request: QuestionRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Ask the AI agent a question about the farm."""
    agent = FarmAgent(db)
    return await agent.answer_question(request.question)
