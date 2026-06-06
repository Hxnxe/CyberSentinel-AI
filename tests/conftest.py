from __future__ import annotations

import pytest

from database.models import Base
from database.session import SessionFactory, get_engine


@pytest.fixture()
def db_session_factory(tmp_path):
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine, SessionFactory(engine)
