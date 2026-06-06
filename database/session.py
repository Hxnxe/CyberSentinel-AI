from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import DATABASE_PATH


def get_engine(db_path: str | Path = DATABASE_PATH) -> Engine:
    """创建数据库引擎。"""
    path = Path(db_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", future=True)


def SessionFactory(engine: Engine) -> sessionmaker[Session]:
    """创建 Session 工厂。"""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def get_session(factory: sessionmaker[Session]) -> Iterator[Session]:
    """统一事务管理：自动提交、异常回滚、始终关闭。"""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
