# app/services/question_service.py
from typing import Optional, List, Tuple
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from datetime import datetime

from app.models.question import Question, QuestionCategory, UserPractice, UserWrongQuestion
from app.models.user import User
from app.schemas.question import (
    QuestionListResponse, QuestionListItem, QuestionDetail,
    AnswerSubmitRequest, AnswerSubmitResponse, PracticeStats,
    WrongQuestionItem, WrongQuestionListResponse,
    FavoriteQuestionItem, FavoriteQuestionListResponse
)


class QuestionService:
    """题目服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_question_list(
        self,
        category_id: Optional[int] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        keyword: Optional[str] = None,
        only_hot: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> QuestionListResponse:
        """获取题目列表（支持筛选）"""
        offset = (page - 1) * page_size
        
        # 构建查询
        query = select(Question).where(Question.is_active == True)
        count_query = select(func.count()).select_from(Question).where(Question.is_active == True)
        
        # 分类筛选
        if category_id:
            query = query.where(Question.category_id == category_id)
            count_query = count_query.where(Question.category_id == category_id)
        
        # 难度筛选
        if difficulty:
            query = query.where(Question.difficulty == difficulty)
            count_query = count_query.where(Question.difficulty == difficulty)
        
        # 题型筛选
        if question_type:
            query = query.where(Question.type == question_type)
            count_query = count_query.where(Question.type == question_type)
        
        # 关键词搜索
        if keyword:
            keyword_filter = or_(
                Question.title.contains(keyword),
                Question.content.contains(keyword)
            )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)
        
        # 只看热门
        if only_hot:
            query = query.where(Question.is_hot == True)
            count_query = count_query.where(Question.is_hot == True)
        
        # 排序：优先按热度，再按创建时间
        query = query.order_by(desc(Question.frequency), desc(Question.created_at))
        
        # 分页
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        questions = result.scalars().all()
        
        items = [
            QuestionListItem(
                id=q.id,
                title=q.title,
                type=q.type,
                difficulty=q.difficulty,
                tags=q.tags,
                frequency=q.frequency,
                is_hot=q.is_hot
            ) for q in questions
        ]
        
        return QuestionListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    async def get_question_detail(self, question_id: int) -> QuestionDetail:
        """获取题目详情"""
        stmt = select(Question).where(
            and_(Question.id == question_id, Question.is_active == True)
        )
        result = await self.db.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")
        
        return QuestionDetail(
            id=question.id,
            category_id=question.category_id,
            title=question.title,
            content=question.content,
            type=question.type,
            difficulty=question.difficulty,
            options=question.options,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            code_template=question.code_template,
            test_cases=question.test_cases,
            tags=question.tags,
            company_tags=question.company_tags,
            frequency=question.frequency,
            is_hot=question.is_hot,
            created_at=question.created_at
        )


class PracticeService:
    """刷题服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_answer(
        self,
        user_id: int,
        question_id: int,
        request: AnswerSubmitRequest
    ) -> AnswerSubmitResponse:
        """提交答案"""
        # 获取题目
        stmt = select(Question).where(
            and_(Question.id == question_id, Question.is_active == True)
        )
        result = await self.db.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")
        
        # 判断答案是否正确
        is_correct = self._check_answer(question, request.answer)
        
        # 记录刷题历史
        practice = UserPractice(
            user_id=user_id,
            question_id=question_id,
            status='correct' if is_correct else 'wrong',
            user_answer=request.answer,
            time_spent_seconds=request.time_spent
        )
        self.db.add(practice)
        
        # 如果答错，加入错题本
        if not is_correct:
            await self._add_to_wrong_questions(user_id, question_id)
        
        await self.db.commit()
        
        # 返回结果（不直接暴露正确答案，除非答错）
        return AnswerSubmitResponse(
            is_correct=is_correct,
            correct_answer=question.correct_answer if not is_correct else None,
            explanation=question.explanation
        )

    async def get_practice_stats(self, user_id: int) -> PracticeStats:
        """获取个人刷题统计"""
        # 总刷题数
        count_stmt = select(func.count()).select_from(UserPractice).where(
            UserPractice.user_id == user_id
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # 正确数量
        correct_stmt = select(func.count()).select_from(UserPractice).where(
            and_(
                UserPractice.user_id == user_id,
                UserPractice.status == 'correct'
            )
        )
        correct_result = await self.db.execute(correct_stmt)
        correct_count = correct_result.scalar() or 0
        
        # 错误数量
        wrong_count = total - correct_count
        
        # 正确率
        accuracy_rate = (correct_count / total * 100) if total > 0 else 0.0
        
        return PracticeStats(
            total_practiced=total,
            correct_count=correct_count,
            wrong_count=wrong_count,
            accuracy_rate=round(accuracy_rate, 2)
        )

    async def toggle_favorite(self, user_id: int, question_id: int) -> dict:
        """收藏/取消收藏题目"""
        # 检查题目是否存在
        stmt = select(Question).where(
            and_(Question.id == question_id, Question.is_active == True)
        )
        result = await self.db.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="题目不存在")
        
        # 查找是否已收藏
        stmt = select(UserPractice).where(
            and_(
                UserPractice.user_id == user_id,
                UserPractice.question_id == question_id
            )
        )
        result = await self.db.execute(stmt)
        practice = result.scalar_one_or_none()
        
        if practice:
            # 切换收藏状态
            practice.is_favorite = not practice.is_favorite
            action = "已收藏" if practice.is_favorite else "已取消收藏"
        else:
            # 创建新的练习记录并标记为收藏
            practice = UserPractice(
                user_id=user_id,
                question_id=question_id,
                is_favorite=True
            )
            self.db.add(practice)
            action = "已收藏"
        
        await self.db.commit()
        return {"message": action, "is_favorite": practice.is_favorite}

    async def get_favorites(self, user_id: int, page: int = 1, page_size: int = 20) -> FavoriteQuestionListResponse:
        """获取收藏列表"""
        offset = (page - 1) * page_size
        
        # 查询总数
        count_stmt = select(func.count()).select_from(UserPractice).where(
            and_(
                UserPractice.user_id == user_id,
                UserPractice.is_favorite == True
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # 查询列表
        stmt = select(UserPractice).where(
            and_(
                UserPractice.user_id == user_id,
                UserPractice.is_favorite == True
            )
        ).order_by(desc(UserPractice.practiced_at)).offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        practices = result.scalars().all()
        
        # 获取题目信息
        question_ids = [p.question_id for p in practices]
        if question_ids:
            q_stmt = select(Question).where(Question.id.in_(question_ids))
            q_result = await self.db.execute(q_stmt)
            questions_map = {q.id: q for q in q_result.scalars().all()}
        else:
            questions_map = {}
        
        items = []
        for practice in practices:
            question = questions_map.get(practice.question_id)
            if question:
                items.append(FavoriteQuestionItem(
                    id=practice.id,
                    question_id=question.id,
                    question_title=question.title,
                    difficulty=question.difficulty,
                    type=question.type,
                    practiced_at=practice.practiced_at
                ))
        
        return FavoriteQuestionListResponse(total=total, items=items)

    async def get_wrong_questions(self, user_id: int, page: int = 1, page_size: int = 20) -> WrongQuestionListResponse:
        """获取错题列表"""
        offset = (page - 1) * page_size
        
        # 查询总数（未掌握的错题）
        count_stmt = select(func.count()).select_from(UserWrongQuestion).where(
            and_(
                UserWrongQuestion.user_id == user_id,
                UserWrongQuestion.is_mastered == False
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # 查询列表
        stmt = select(UserWrongQuestion).where(
            and_(
                UserWrongQuestion.user_id == user_id,
                UserWrongQuestion.is_mastered == False
            )
        ).order_by(desc(UserWrongQuestion.last_wrong_at)).offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        wrong_records = result.scalars().all()
        
        # 获取题目信息
        question_ids = [w.question_id for w in wrong_records]
        if question_ids:
            q_stmt = select(Question).where(Question.id.in_(question_ids))
            q_result = await self.db.execute(q_stmt)
            questions_map = {q.id: q for q in q_result.scalars().all()}
        else:
            questions_map = {}
        
        items = []
        for record in wrong_records:
            question = questions_map.get(record.question_id)
            if question:
                items.append(WrongQuestionItem(
                    id=record.id,
                    question_id=question.id,
                    question_title=question.title,
                    difficulty=question.difficulty,
                    wrong_count=record.wrong_count,
                    last_wrong_at=record.last_wrong_at,
                    is_mastered=record.is_mastered,
                    notes=record.notes
                ))
        
        return WrongQuestionListResponse(total=total, items=items)

    async def mark_wrong_as_mastered(self, user_id: int, wrong_id: int) -> dict:
        """标记错题为已掌握"""
        stmt = select(UserWrongQuestion).where(
            and_(
                UserWrongQuestion.id == wrong_id,
                UserWrongQuestion.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(status_code=404, detail="错题记录不存在")
        
        record.is_mastered = True
        await self.db.commit()
        
        return {"message": "已标记为掌握"}

    # ==================== 私有方法 ====================

    def _check_answer(self, question: Question, user_answer: str) -> bool:
        """校验答案"""
        if not question.correct_answer:
            return False
        
        # 简单字符串比对（可根据题型扩展更复杂的逻辑）
        return user_answer.strip().lower() == question.correct_answer.strip().lower()

    async def _add_to_wrong_questions(self, user_id: int, question_id: int):
        """添加到错题本"""
        # 查找是否已在错题本中
        stmt = select(UserWrongQuestion).where(
            and_(
                UserWrongQuestion.user_id == user_id,
                UserWrongQuestion.question_id == question_id
            )
        )
        result = await self.db.execute(stmt)
        wrong_record = result.scalar_one_or_none()
        
        if wrong_record:
            # 更新错误次数
            wrong_record.wrong_count += 1
            wrong_record.last_wrong_at = datetime.utcnow()
        else:
            # 新增错题记录
            wrong_record = UserWrongQuestion(
                user_id=user_id,
                question_id=question_id,
                wrong_count=1
            )
            self.db.add(wrong_record)
