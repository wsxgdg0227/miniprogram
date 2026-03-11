# -*- coding: gbk -*-
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


# Snippet 是唯一的业务表模型，映射到 snippets 表。
class Snippet(Base):
    __tablename__ = "snippets"

    # id: 主键，自增整数。
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # title: 代码标题，来自文件名或用户输入。
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # category: 分类，例如 "algorithm"、"template"、"cpp"。
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="cpp")
    # content: 完整代码正文，使用 Text 存储长文本。
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # created_at: 入库时间，默认使用 UTC 当前时间。
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
