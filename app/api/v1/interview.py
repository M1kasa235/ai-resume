"""AI 面试官 API — 独立面试会话管理 + 报告 + 流式"""

import re
import json
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.context import set_current_user_id
from app.models.interview import AIInterview, AIInterviewQA
from app.models.user import User
from app.schemas.interview import (
    AIInterviewStartRequest,
    AIInterviewReplyRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI面试"])

MAX_QUESTIONS = 25


def _parse_evaluation(raw: str) -> tuple[list[dict], int | None, str | None, str | None, str | None]:
    """解析 Agent 返回的 Markdown 评估报告，提取逐题评分和综合评估"""
    evaluations = []
    overall_score = None
    strength = None
    weakness = None
    improvement = None

    # 提取逐题评估块
    qa_blocks = re.split(r'(?=### Q\d+:)', raw)
    for block in qa_blocks:
        if not block.strip().startswith('### Q'):
            continue
        seq_match = re.match(r'### Q(\d+):', block)
        sequence = int(seq_match.group(1)) if seq_match else 0
        score_match = re.search(r'\*\*评分[：:]\*\*\s*(\d+)', block)
        score = int(score_match.group(1)) if score_match else None
        comment_match = re.search(r'\*\*点评[：:]\*\*\s*(.+?)(?=\*\*参考|\*\*你的|###|\Z)', block, re.DOTALL)
        comment = comment_match.group(1).strip() if comment_match else None
        ref_match = re.search(r'\*\*参考回答[：:]\*\*\s*(.+?)(?=###|\Z)', block, re.DOTALL)
        suggested = ref_match.group(1).strip() if ref_match else None

        evaluations.append({
            "sequence": sequence,
            "score": score,
            "comment": comment,
            "suggested_answer": suggested,
        })

    # 综合评分
    score_match = re.search(r'综合评分[：:]\*\*\s*(\d+)', raw)
    if score_match:
        overall_score = int(score_match.group(1))

    # 优劣势
    strength_match = re.search(r'### 优势分析\s*\n(.+?)(?=### 待改进|### 改进|\Z)', raw, re.DOTALL)
    if strength_match:
        strength = strength_match.group(1).strip()
    weakness_match = re.search(r'### 待改进点\s*\n(.+?)(?=### 改进|\Z)', raw, re.DOTALL)
    if weakness_match:
        weakness = weakness_match.group(1).strip()
    improve_match = re.search(r'### 改进建议\s*\n(.+?)(?=\Z)', raw, re.DOTALL)
    if improve_match:
        improvement = improve_match.group(1).strip()

    return evaluations, overall_score, strength, weakness, improvement


async def _build_interview_round_prompt(
    interview: AIInterview,
    user_id: int,
    is_first_round: bool,
    user_message: str | None,
) -> str:
    """统一构建面试提问 prompt，确保流式与非流式路径行为一致。"""
    if not is_first_round:
        return user_message or ""

    frontend_type = interview.interview_type
    if frontend_type == "behavioral":
        frontend_type = "hr"

    resume_text = ""
    try:
        from app.rag import get_rag_service

        rag = get_rag_service()
        focus_parts = [frontend_type]
        if interview.job_description:
            focus_parts.append(interview.job_description[:200])
        resume_text = await rag.retrieve_raw_chunks(
            user_id,
            focus=" ".join(focus_parts),
        )
    except Exception as e:
        logger.warning(f"简历检索失败: {e}")

    from app.agents.interview_agent import build_initial_prompt

    return build_initial_prompt(
        interview_type=frontend_type,
        job_title=interview.job_title or "未指定",
        company_name=interview.company_name or "",
        job_description=interview.job_description or "",
        resume_text=resume_text,
    )


@router.post("/ai-interview/sessions")
async def start_interview(
    request: AIInterviewStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新的 AI 面试会话，即时返回。首问由 /stream 端点流式生成。"""
    set_current_user_id(current_user.id)

    interview_type = request.interview_type or "comprehensive"
    if interview_type not in ("technical", "hr", "comprehensive"):
        interview_type = "comprehensive"

    db_interview_type = "behavioral" if interview_type == "hr" else interview_type

    interview = AIInterview(
        user_id=current_user.id,
        job_title=request.job_title,
        company_name=request.company_name,
        job_description=request.job_description,
        interview_type=db_interview_type,
        status="ongoing",
        started_at=datetime.now(timezone.utc),
    )
    db.add(interview)
    await db.commit()
    await db.refresh(interview)

    return {
        "session_id": str(interview.id),
        "job_title": request.job_title,
        "company_name": interview.company_name,
        "job_description": interview.job_description,
        "status": "ongoing",
        "interview_type": interview_type,
        "messages": [],
    }


@router.post("/ai-interview/sessions/{session_id}/stream")
async def stream_message(
    session_id: str,
    request: AIInterviewReplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE 流式端点：发送用户回答，流式返回 AI 追问。首次调用生成开场白。"""
    set_current_user_id(current_user.id)

    try:
        sid = int(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的会话 ID")

    interview = await db.get(AIInterview, sid)
    if not interview or interview.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    if interview.status != "ongoing":
        raise HTTPException(status_code=400, detail="该面试会话已结束")

    # 判断是否首次调用
    stmt = (
        select(AIInterviewQA)
        .where(AIInterviewQA.interview_id == sid)
        .order_by(desc(AIInterviewQA.sequence))
        .limit(1)
    )
    result = await db.execute(stmt)
    last_qa = result.scalar_one_or_none()
    is_first = last_qa is None

    next_sequence = (last_qa.sequence + 1) if last_qa else 1
    if next_sequence > MAX_QUESTIONS:
        raise HTTPException(status_code=400, detail="已达 25 题上限")

    # 非首次：保存用户回答
    if not is_first and request.message:
        last_qa.answer = request.message
        db.add(last_qa)
        await db.commit()

    thread_id = f"user_{current_user.id}_interview_{sid}"

    from app.agents.interview_agent import conduct_interview_stream
    prompt = await _build_interview_round_prompt(
        interview=interview,
        user_id=current_user.id,
        is_first_round=is_first,
        user_message=request.message,
    )

    async def event_stream():
        full_response = ""
        try:
            async for token in conduct_interview_stream(prompt, thread_id):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

            # 流结束后用独立会话写入，避免复用请求级 session 的生命周期竞态。
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as stream_db:
                stream_interview = await stream_db.get(AIInterview, sid)
                if not stream_interview:
                    raise RuntimeError("面试会话不存在，无法保存流式结果")

                new_qa = AIInterviewQA(
                    interview_id=sid,
                    sequence=next_sequence,
                    question=full_response or "好的，我们继续下一题。",
                )
                stream_db.add(new_qa)
                stream_interview.total_questions = next_sequence
                await stream_db.commit()

            yield f"data: {json.dumps({'type': 'done', 'sequence': next_sequence})}\n\n"
        except Exception as e:
            logger.error(f"流式生成失败: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': '生成失败，请重试'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/ai-interview/messages")
async def send_message(
    request: AIInterviewReplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送用户回答，获取 AI 面试官追问（非流式，留作兜底）。达到 25 题上限时自动结束。"""
    set_current_user_id(current_user.id)

    try:
        session_id_int = int(request.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的会话 ID")

    interview = await db.get(AIInterview, session_id_int)
    if not interview:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    if interview.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    if interview.status != "ongoing":
        raise HTTPException(status_code=400, detail="该面试会话已结束")

    stmt = (
        select(AIInterviewQA)
        .where(AIInterviewQA.interview_id == interview.id)
        .order_by(desc(AIInterviewQA.sequence))
        .limit(1)
    )
    result = await db.execute(stmt)
    last_qa = result.scalar_one_or_none()

    if last_qa:
        last_qa.answer = request.message
        db.add(last_qa)

    next_sequence = (last_qa.sequence + 1) if last_qa else 1

    if next_sequence > MAX_QUESTIONS:
        interview.total_questions = last_qa.sequence if last_qa else 0
        await db.commit()
        return {
            "session_id": request.session_id,
            "reply": (
                f"本次面试已达到 {MAX_QUESTIONS} 题的上限。"
                f"感谢你的参与！请点击「结束面试」查看完整评估报告。"
            ),
            "limit_reached": True,
        }

    is_first = last_qa is None
    thread_id = f"user_{current_user.id}_interview_{session_id_int}"

    from app.agents.interview_agent import conduct_interview

    prompt = await _build_interview_round_prompt(
        interview=interview,
        user_id=current_user.id,
        is_first_round=is_first,
        user_message=request.message,
    )

    try:
        ai_response = await conduct_interview(prompt, thread_id)
    except Exception as e:
        logger.error(f"面试 Agent 调用失败: {e}")
        ai_response = "好的，谢谢你的回答。我们继续下一题。"

    new_qa = AIInterviewQA(
        interview_id=interview.id,
        sequence=next_sequence,
        question=ai_response,
    )
    db.add(new_qa)
    interview.total_questions = next_sequence
    await db.commit()

    return {
        "session_id": request.session_id,
        "reply": ai_response,
    }


@router.get("/ai-interview/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取面试会话详情和历史消息"""
    set_current_user_id(current_user.id)

    try:
        sid = int(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的会话 ID")

    interview = await db.get(AIInterview, sid)
    if not interview:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    if interview.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")

    stmt = (
        select(AIInterviewQA)
        .where(AIInterviewQA.interview_id == interview.id)
        .order_by(AIInterviewQA.sequence)
    )
    result = await db.execute(stmt)
    qa_records = result.scalars().all()

    messages = []
    for qa in qa_records:
        messages.append({
            "role": "assistant",
            "content": qa.question,
            "created_at": qa.created_at.isoformat() if qa.created_at else None,
        })
        if qa.answer:
            messages.append({
                "role": "user",
                "content": qa.answer,
                "created_at": qa.created_at.isoformat() if qa.created_at else None,
            })

    frontend_type = interview.interview_type
    if frontend_type == "behavioral":
        frontend_type = "hr"

    return {
        "session_id": session_id,
        "job_title": interview.job_title,
        "company_name": interview.company_name,
        "job_description": interview.job_description,
        "status": interview.status,
        "interview_type": frontend_type,
        "messages": messages,
    }


async def _run_evaluation_background(interview_id: int, user_id: int, thread_id: str):
    """后台异步生成面试评估报告，写入 DB 后状态变为 completed"""
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            interview = await db.get(AIInterview, interview_id)
            if not interview:
                logger.error(f"后台评估: 面试 {interview_id} 不存在")
                return

            stmt = (
                select(AIInterviewQA)
                .where(AIInterviewQA.interview_id == interview_id)
                .order_by(AIInterviewQA.sequence)
            )
            result = await db.execute(stmt)
            qa_records = result.scalars().all()

            if not qa_records:
                interview.status = "completed"
                interview.report_markdown = "无问答记录，无法生成报告。"
                await db.commit()
                return

            parts = []
            for qa in qa_records:
                parts.append(f"### Q{qa.sequence}: {qa.question}")
                if qa.answer:
                    parts.append(f"**候选人回答：** {qa.answer}")
                parts.append("")
            transcript_text = "\n".join(parts)

            frontend_type = interview.interview_type
            if frontend_type == "behavioral":
                frontend_type = "hr"

            from app.agents.interview_agent import conduct_interview, build_evaluation_prompt
            eval_prompt = build_evaluation_prompt(transcript_text, frontend_type)

            try:
                raw_eval = await conduct_interview(eval_prompt, thread_id)
                evals, overall_score, strength, weakness, improvement = _parse_evaluation(raw_eval)
            except Exception as e:
                logger.error(f"后台评估 LLM 失败: {e}")
                interview.status = "completed"
                interview.report_markdown = f"评估生成失败：{str(e)}"
                interview.total_questions = len(qa_records)
                await db.commit()
                return

            if evals:
                for ev in evals:
                    seq = ev["sequence"]
                    for qa in qa_records:
                        if qa.sequence == seq:
                            qa.evaluation_score = ev.get("score")
                            qa.evaluation_comment = ev.get("comment")
                            qa.suggested_answer = ev.get("suggested_answer")
                            db.add(qa)
                            break

            interview.status = "completed"
            interview.total_questions = len(qa_records)
            interview.overall_score = overall_score
            interview.strength_analysis = strength
            interview.weakness_analysis = weakness
            interview.improvement_suggestions = improvement
            interview.report_markdown = raw_eval
            await db.commit()
            logger.info(f"后台评估完成: interview={interview_id}, score={overall_score}")

        except Exception as e:
            logger.error(f"后台评估异常: {e}")
            try:
                interview = await db.get(AIInterview, interview_id)
                if interview and interview.status == "evaluating":
                    interview.status = "completed"
                    interview.report_markdown = f"评估异常：{str(e)}"
                    await db.commit()
            except Exception:
                pass


async def recover_stuck_evaluations():
    """启动时恢复卡在 evaluating 状态的面试评估

    遍历 status == 'evaluating' 且 ended_at 超过 90 秒的会话，
    重新触发后台评估。服务重启后评估丢失的场景靠此恢复。
    """
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        stmt = (
            select(AIInterview)
            .where(AIInterview.status == "evaluating")
        )
        result = await db.execute(stmt)
        stuck = result.scalars().all()

        if not stuck:
            return

        now = datetime.now(timezone.utc)
        recoverable = []
        for iv in stuck:
            if iv.ended_at and (now - iv.ended_at).total_seconds() > 90:
                recoverable.append(iv)

        if not recoverable:
            logger.info(f"发现 {len(stuck)} 个 evaluating 会话但尚未超时，跳过恢复")
            return

        logger.warning(f"恢复 {len(recoverable)} 个卡住的面试评估")

        for i, iv in enumerate(recoverable):
            thread_id = f"user_{iv.user_id}_interview_{iv.id}"
            asyncio.create_task(_run_evaluation_background(iv.id, iv.user_id, thread_id))
            if i < len(recoverable) - 1:
                await asyncio.sleep(2)  # 错开 LLM 调用，避免并发风暴


@router.post("/ai-interview/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """结束面试，后台异步生成评估报告，即时返回"""
    set_current_user_id(current_user.id)

    try:
        sid = int(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的会话 ID")

    interview = await db.get(AIInterview, sid)
    if not interview:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    if interview.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    if interview.status == "evaluating":
        return {
            "session_id": session_id,
            "status": "evaluating",
            "total_questions": interview.total_questions,
        }
    if interview.status != "ongoing":
        raise HTTPException(status_code=400, detail="该面试会话已结束")

    interview.status = "evaluating"
    interview.ended_at = datetime.now(timezone.utc)

    stmt = (
        select(AIInterviewQA)
        .where(AIInterviewQA.interview_id == interview.id)
    )
    result = await db.execute(stmt)
    interview.total_questions = len(result.scalars().all())
    await db.commit()

    thread_id = f"user_{current_user.id}_interview_{sid}"

    asyncio.create_task(_run_evaluation_background(sid, current_user.id, thread_id))

    return {
        "session_id": session_id,
        "status": "evaluating",
        "total_questions": interview.total_questions,
    }


@router.get("/ai-interview/reports/{session_id}")
async def get_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取面试评估报告"""
    set_current_user_id(current_user.id)

    try:
        sid = int(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的会话 ID")

    interview = await db.get(AIInterview, sid)
    if not interview:
        raise HTTPException(status_code=404, detail="面试记录不存在")
    if interview.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该记录")

    stmt = (
        select(AIInterviewQA)
        .where(AIInterviewQA.interview_id == interview.id)
        .order_by(AIInterviewQA.sequence)
    )
    result = await db.execute(stmt)
    qa_records = result.scalars().all()

    evaluations = []
    for qa in qa_records:
        evaluations.append({
            "sequence": qa.sequence,
            "question": qa.question,
            "answer": qa.answer,
            "score": qa.evaluation_score,
            "comment": qa.evaluation_comment,
            "suggested_answer": qa.suggested_answer,
        })

    frontend_type = interview.interview_type
    if frontend_type == "behavioral":
        frontend_type = "hr"

    return {
        "session_id": session_id,
        "job_title": interview.job_title,
        "company_name": interview.company_name,
        "interview_type": frontend_type,
        "status": interview.status,
        "total_questions": interview.total_questions,
        "overall_score": interview.overall_score,
        "strength_analysis": interview.strength_analysis,
        "weakness_analysis": interview.weakness_analysis,
        "improvement_suggestions": interview.improvement_suggestions,
        "report_markdown": interview.report_markdown,
        "evaluations": evaluations,
        "started_at": interview.started_at.isoformat() if interview.started_at else None,
        "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
    }


@router.get("/ai-interview/reports")
async def list_reports(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的历史面试报告列表（含评估中的会话）"""
    set_current_user_id(current_user.id)

    status_filter = or_(
        AIInterview.status == "completed",
        AIInterview.status == "evaluating",
    )

    stmt = (
        select(AIInterview)
        .where(AIInterview.user_id == current_user.id, status_filter)
        .order_by(desc(AIInterview.ended_at))
    )

    # 总数
    total_result = await db.execute(
        select(AIInterview).where(AIInterview.user_id == current_user.id, status_filter)
    )
    total = len(total_result.scalars().all())

    # 分页
    offset = (page - 1) * size
    page_stmt = stmt.offset(offset).limit(size)
    result = await db.execute(page_stmt)
    interviews = result.scalars().all()

    items = []
    for iv in interviews:
        ft = iv.interview_type
        if ft == "behavioral":
            ft = "hr"
        items.append({
            "session_id": str(iv.id),
            "job_title": iv.job_title,
            "company_name": iv.company_name,
            "interview_type": ft,
            "status": iv.status,
            "total_questions": iv.total_questions,
            "overall_score": iv.overall_score,
            "started_at": iv.started_at.isoformat() if iv.started_at else None,
            "ended_at": iv.ended_at.isoformat() if iv.ended_at else None,
        })

    return {"total": total, "items": items}
