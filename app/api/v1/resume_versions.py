"""简历版本管理接口"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.resume_version import ResumeVersion
from app.schemas.resume_version import (
    VersionListResponse,
    VersionDetail,
    VersionItem,
    SaveVersionRequest,
    CompareResponse,
    CompareItem,
)
from app.rag.core.vector_store import vector_store

router = APIRouter(prefix="/resume/versions", tags=["简历版本"])


@router.get("", response_model=VersionListResponse)
async def list_versions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取版本列表"""
    stmt = select(ResumeVersion).where(
        ResumeVersion.user_id == current_user.id
    ).order_by(desc(ResumeVersion.version))
    result = await db.execute(stmt)
    versions = result.scalars().all()
    return VersionListResponse(
        versions=[
            VersionItem(
                id=v.id,
                version=v.version,
                source=v.source,
                summary=v.summary,
                job_id=v.job_id,
                created_at=v.created_at,
            )
            for v in versions
        ]
    )


@router.post("", response_model=VersionItem)
async def save_version(
    request: SaveVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """保存新版本"""
    # 获取当前最大版本号
    stmt = select(func.max(ResumeVersion.version)).where(
        ResumeVersion.user_id == current_user.id
    )
    result = await db.execute(stmt)
    max_version = result.scalar() or 0

    version = ResumeVersion(
        user_id=current_user.id,
        version=max_version + 1,
        content=request.content,
        source=request.source,
        summary=request.summary,
        job_id=request.job_id,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    return VersionItem(
        id=version.id,
        version=version.version,
        source=version.source,
        summary=version.summary,
        job_id=version.job_id,
        created_at=version.created_at,
    )


@router.get("/{version_id}", response_model=VersionDetail)
async def get_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取版本详情"""
    stmt = select(ResumeVersion).where(
        ResumeVersion.id == version_id,
        ResumeVersion.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    return VersionDetail(
        id=version.id,
        version=version.version,
        source=version.source,
        content=version.content,
        summary=version.summary,
        job_id=version.job_id,
        created_at=version.created_at,
    )


@router.get("/{v1_id}/compare/{v2_id}", response_model=CompareResponse)
async def compare_versions(
    v1_id: int,
    v2_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对比两个版本的差异"""
    stmt1 = select(ResumeVersion).where(
        ResumeVersion.id == v1_id,
        ResumeVersion.user_id == current_user.id,
    )
    stmt2 = select(ResumeVersion).where(
        ResumeVersion.id == v2_id,
        ResumeVersion.user_id == current_user.id,
    )
    v1 = (await db.execute(stmt1)).scalar_one_or_none()
    v2 = (await db.execute(stmt2)).scalar_one_or_none()
    if not v1 or not v2:
        raise HTTPException(status_code=404, detail="版本不存在")

    # 简单分段对比
    import difflib
    lines1 = v1.content.split("\n")
    lines2 = v2.content.split("\n")
    diff = list(difflib.unified_diff(lines1, lines2, lineterm=""))

    changes = []
    section = "全文"
    for line in diff:
        if line.startswith("+"):
            changes.append(CompareItem(section=section, before="", after=line[1:]))
        elif line.startswith("-"):
            changes.append(CompareItem(section=section, before=line[1:], after=""))

    return CompareResponse(
        v1_id=v1.id,
        v2_id=v2.id,
        v1_version=v1.version,
        v2_version=v2.version,
        changes=changes,
    )
