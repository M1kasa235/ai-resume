# app/schemas/job.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# ==================== 岗位分类 ====================

class JobCategoryBase(BaseModel):
    name: str = Field(..., max_length=50, description="分类名称")
    code: str = Field(..., max_length=30, description="分类编码")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: int = Field(0, description="排序")

class JobCategoryCreate(JobCategoryBase):
    pass

class JobCategoryUpdate(BaseModel):
    """更新分类请求（全部可选）"""
    name: Optional[str] = Field(None, max_length=50)
    code: Optional[str] = Field(None, max_length=30)
    parent_id: Optional[int] = Field(None)
    sort_order: Optional[int] = Field(None)
    is_active: Optional[bool] = Field(None)

class JobCategoryResponse(JobCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime

class JobCategoryTree(JobCategoryResponse):
    """分类树结构"""
    children: List["JobCategoryTree"] = []


# ==================== 岗位基础模型 ====================

class JobBase(BaseModel):
    title: str = Field(..., max_length=200, description="职位标题")
    category_id: Optional[int] = Field(None, description="分类ID")
    company_name: str = Field(..., max_length=100, description="公司名称")
    company_logo: Optional[str] = Field(None, description="公司Logo")
    company_stage: Optional[str] = Field(None, description="公司阶段")
    company_size: Optional[str] = Field(None, description="公司规模")
    description: Optional[str] = Field(None, description="职位描述")
    requirements: Optional[str] = Field(None, description="岗位要求")
    salary_min: Optional[int] = Field(None, ge=0, description="最低薪资")
    salary_max: Optional[int] = Field(None, ge=0, description="最高薪资")
    salary_months: int = Field(12, ge=12, le=24, description="薪几个月")
    city: Optional[str] = Field(None, max_length=50, description="工作城市")
    district: Optional[str] = Field(None, max_length=50, description="区县")
    address: Optional[str] = Field(None, max_length=255, description="详细地址")
    experience_min: Optional[int] = Field(None, ge=0, le=50, description="最低经验")
    experience_max: Optional[int] = Field(None, ge=0, le=50, description="最高经验")
    education_requirement: str = Field("unlimited", description="学历要求")
    skills_required: Optional[List[str]] = Field(None, description="所需技能")
    tags: Optional[List[str]] = Field(None, description="标签")
    source: str = Field("internal", description="来源")
    source_url: Optional[str] = Field(None, description="原始链接")
    is_urgent: bool = Field(False, description="是否急聘")
    expired_at: Optional[datetime] = Field(None, description="过期时间")

class JobCreate(JobBase):
    """创建岗位请求"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "title": "高级Python后端工程师",
            "company_name": "某互联网大厂",
            "salary_min": 30,
            "salary_max": 50,
            "city": "北京",
            "experience_min": 3,
            "experience_max": 5,
            "skills_required": ["Python", "FastAPI", "MySQL", "Redis"],
            "tags": ["双休", "五险一金", "带薪年假"]
        }
    })

class JobUpdate(BaseModel):
    """更新岗位请求（全部可选）"""
    title: Optional[str] = Field(None, max_length=200)
    category_id: Optional[int] = None
    company_name: Optional[str] = Field(None, max_length=100)
    company_logo: Optional[str] = None
    company_stage: Optional[str] = None
    company_size: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_months: Optional[int] = Field(None, ge=12, le=24)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=255)
    experience_min: Optional[int] = Field(None, ge=0, le=50)
    experience_max: Optional[int] = Field(None, ge=0, le=50)
    education_requirement: Optional[str] = None
    skills_required: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_urgent: Optional[bool] = None
    is_active: Optional[bool] = None
    expired_at: Optional[datetime] = None

class JobResponse(JobBase):
    """岗位详情响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    view_count: int
    apply_count: int
    is_active: bool
    published_at: datetime
    created_at: datetime
    updated_at: datetime

    # 扩展字段
    salary_display: str = Field("", description="薪资显示文本")
    experience_display: str = Field("", description="经验显示文本")
    category: Optional[JobCategoryResponse] = None
    is_favorited: bool = Field(False, description="当前用户是否收藏")

class JobListResponse(BaseModel):
    """岗位列表响应"""
    total: int = Field(..., description="总数")
    items: List[JobResponse] = Field(..., description="岗位列表")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")


# ==================== 搜索筛选参数 ====================

class JobSearchParams(BaseModel):
    """岗位搜索参数"""
    keyword: Optional[str] = Field(None, description="关键词（搜索标题、描述、公司）")
    city: Optional[str] = Field(None, description="城市")
    category_id: Optional[int] = Field(None, description="分类ID")
    salary_min: Optional[int] = Field(None, ge=0, description="最低薪资要求")
    salary_max: Optional[int] = Field(None, ge=0, description="最高薪资要求")
    experience_min: Optional[int] = Field(None, ge=0, le=50)
    experience_max: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = Field(None, description="学历要求")
    company_stage: Optional[str] = Field(None, description="公司阶段")
    skills: Optional[List[str]] = Field(None, description="所需技能")
    sort_by: str = Field("published_at", description="排序字段: published_at/salary_min/apply_count/view_count")
    sort_order: str = Field("desc", description="排序方向: asc/desc")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    only_urgent: bool = Field(False, description="只看急聘")
    only_active: bool = Field(True, description="只看在招")


# ==================== 收藏相关 ====================

class UserFavoriteJobCreate(BaseModel):
    job_id: int = Field(..., description="岗位ID")

class UserFavoriteJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    job: JobResponse
    created_at: datetime