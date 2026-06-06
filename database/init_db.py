from __future__ import annotations

import logging
from pathlib import Path

from config import DATABASE_PATH
from database.models import Base
from database.session import get_engine

logger = logging.getLogger(__name__)


def init_database(db_path: str | Path = DATABASE_PATH) -> None:
    """统一数据库初始化入口。"""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    logger.info("数据库初始化完成: %s", db_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
