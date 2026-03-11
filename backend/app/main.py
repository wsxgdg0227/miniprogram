# -*- coding: gbk -*-
from typing import Generator, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, SessionLocal, engine
from .models import Snippet
from .schemas import SnippetOut, UploadSnippetRequest

# 创建 FastAPI 应用实例。
# 你可以把它理解成 C++ Web 框架里的“主 Application 对象”。
app = FastAPI(title="CppTemplate-Cloud API", version="0.1.0")

# 配置跨域中间件。
# 小程序真机与开发工具请求后端时，可能涉及跨域，先允许全部来源方便 MVP 联调。
# 上线时建议把 allow_origins 收紧为你的可信域名列表。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 启动时确保数据库表存在。
# 这里会根据 ORM 模型自动建表（若已存在则不会重复创建）。
Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    # 每个请求进来时，先创建一个独立的数据库会话对象。
    db = SessionLocal()
    try:
        # yield 把 db 提供给路由函数使用。
        # 当路由函数执行结束后，控制流会回到 finally，自动关闭会话。
        yield db
    finally:
        # 关闭会话，释放连接资源，防止连接泄漏。
        db.close()


def verify_api_key(x_api_key: str = Header(default="")) -> None:
    # 从请求头读取 X-API-KEY。
    # 在 FastAPI 中，Header(...) 会自动把 HTTP Header 注入参数。
    expected_api_key = settings.api_key.strip()
    if not expected_api_key or expected_api_key == "CHANGE_ME_TO_A_STRONG_KEY":
        return
    if x_api_key != expected_api_key:
        # 如果 key 不匹配，抛出 401，阻止写入接口被随意调用。
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@app.get("/")
async def healthcheck() -> dict:
    # async def 表示“异步协程函数”：
    # Python 会在 I/O 等待（如网络、数据库）期间让出执行权，提高并发能力。
    # 这和 C++20 协程思想接近：不是开更多线程，而是在等待时切走任务。
    return {"message": "CppTemplate-Cloud API is running"}


@app.post("/api/upload", dependencies=[Depends(verify_api_key)])
async def upload_snippet(payload: UploadSnippetRequest, db: Session = Depends(get_db)) -> dict:
    # 路由配置解释：
    # - @app.post("/api/upload") 表示 HTTP POST + 路径匹配。
    # - dependencies=[Depends(verify_api_key)] 表示先执行鉴权函数。
    # - payload 会自动解析 JSON 请求体并做 Pydantic 校验。
    # - db 通过 Depends(get_db) 注入数据库会话。

    # 把请求数据映射为 ORM 实体对象。
    snippet = Snippet(
        title=payload.title.strip(),
        category=payload.category.strip(),
        content=payload.content,
    )

    # add: 把对象加入当前事务会话。
    db.add(snippet)
    # commit: 提交事务，真正写入数据库文件。
    db.commit()
    # refresh: 重新从数据库拉取该对象，拿到 id / created_at 等最终值。
    db.refresh(snippet)

    # 返回最小响应，告诉前端写入成功。
    return {"ok": True, "id": snippet.id}


@app.get("/api/snippets", response_model=List[SnippetOut])
async def list_snippets(category: Optional[str] = None, db: Session = Depends(get_db)) -> List[Snippet]:
    # category 是可选查询参数：
    # - 不传时返回全部代码
    # - 传入时仅返回指定分类
    query = db.query(Snippet)
    if category:
        query = query.filter(Snippet.category == category.strip())

    # 按 created_at 倒序查询，最新上传的代码排在最前面。
    snippets = query.order_by(Snippet.created_at.desc()).all()
    # FastAPI 会按 response_model 自动把 ORM 对象序列化为 JSON。
    return snippets


@app.get("/api/snippets/{snippet_id}", response_model=SnippetOut)
async def get_snippet(snippet_id: int, db: Session = Depends(get_db)) -> Snippet:
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snippet not found")
    return snippet


@app.get("/api/categories", response_model=List[str])
async def list_categories(db: Session = Depends(get_db)) -> List[str]:
    # distinct 返回去重后的分类名，order_by 让结果稳定且可预测。
    rows = db.query(Snippet.category).distinct().order_by(Snippet.category.asc()).all()
    return [row[0] for row in rows if row[0]]
