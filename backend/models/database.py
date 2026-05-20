"""
数据库连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import config
from pathlib import Path

# 确保数据库目录存在
db_path = Path(config.database.url.replace("sqlite:///", ""))
db_path.parent.mkdir(parents=True, exist_ok=True)

# 创建引擎
engine = create_engine(
    config.database.url,
    connect_args={"check_same_thread": False},  # SQLite 需要
    echo=config.debug,
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """获取数据库会话（用于 FastAPI 依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    from models.base import Base
    # 导入所有模型以确保它们被注册
    import models.company
    import models.jd
    import models.resume
    import models.optimization
    import models.interview
    Base.metadata.create_all(bind=engine)
