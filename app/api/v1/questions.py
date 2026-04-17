# app/api/v1/questions.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.question_service import QuestionService, PracticeService
from app.schemas.question import (
    QuestionListResponse, QuestionDetail,
    AnswerSubmitRequest, AnswerSubmitResponse, PracticeStats,
    WrongQuestionListResponse, FavoriteQuestionListResponse
)

router = APIRouter(prefix="/questions", tags=["题库"])


# ==================== 题目浏览 ====================

@router.get("", response_model=QuestionListResponse)
async def get_question_list(
    category_id: int = Query(None, description="分类ID"),
    difficulty: str = Query(None, description="难度: easy/medium/hard"),
    question_type: str = Query(None, description="题型"),
    keyword: str = Query(None, description="关键词搜索"),
    only_hot: bool = Query(False, description="只看热门"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取题目列表（支持多维度筛选）"""
    service = QuestionService(db)
    return await service.get_question_list(
        category_id=category_id,
        difficulty=difficulty,
        question_type=question_type,
        keyword=keyword,
        only_hot=only_hot,
        page=page,
        page_size=page_size
    )


@router.get("/{question_id}", response_model=QuestionDetail)
async def get_question_detail(
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取题目详情"""
    service = QuestionService(db)
    return await service.get_question_detail(question_id)


# ==================== 作答 ====================

@router.post("/{question_id}/answer", response_model=AnswerSubmitResponse)
async def submit_answer(
    question_id: int,
    request: AnswerSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交答案"""
    service = PracticeService(db)
    return await service.submit_answer(current_user.id, question_id, request)


# ==================== 个人统计 ====================

@router.get("/my/stats", response_model=PracticeStats)
async def get_practice_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的刷题统计"""
    service = PracticeService(db)
    return await service.get_practice_stats(current_user.id)


@router.get("/my/wrong", response_model=WrongQuestionListResponse)
async def get_wrong_questions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的错题列表"""
    service = PracticeService(db)
    return await service.get_wrong_questions(current_user.id, page, page_size)


@router.put("/my/wrong/{wrong_id}/mastered")
async def mark_wrong_as_mastered(
    wrong_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """标记错题为已掌握"""
    service = PracticeService(db)
    return await service.mark_wrong_as_mastered(current_user.id, wrong_id)


@router.get("/my/favorites", response_model=FavoriteQuestionListResponse)
async def get_favorites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的收藏列表"""
    service = PracticeService(db)
    return await service.get_favorites(current_user.id, page, page_size)


# ==================== 收藏操作 ====================

@router.post("/{question_id}/favorite")
async def toggle_favorite(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """收藏/取消收藏题目"""
    service = PracticeService(db)
    return await service.toggle_favorite(current_user.id, question_id)
