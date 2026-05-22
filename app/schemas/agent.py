from typing import Optional,List
from pydantic import BaseModel, Field

#数据模型
class ChatRequest(BaseModel):
    message:str
    image_url: Optional[str] = Field(None, description="图片URL，可选")
    thread_id: str = Field(..., description="会话线程ID，用于关联历史消息")
