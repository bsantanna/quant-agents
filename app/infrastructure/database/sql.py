import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

Base = declarative_base()


class Database:
    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url, echo=False)
        self.session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            ),
        )
        # Store the default schema (public) for reference
        self.default_schema = "public"

    def sanitize_schema_name(self, schema_name: str) -> str:
        """Sanitize schema name by replacing invalid characters (e.g., hyphens)."""
        return schema_name.replace("-", "_")

    def create_database(self, schema_name: str = "public") -> None:
        sanitized_schema = self.sanitize_schema_name(schema_name)
        with self.engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {sanitized_schema}"))
            conn.execute(text(f"SET search_path TO {sanitized_schema}"))
            Base.metadata.create_all(bind=conn)

    @contextmanager
    def session(self, schema_name: str = "public"):
        sanitized_schema = self.sanitize_schema_name(schema_name)
        self.create_database(schema_name=sanitized_schema)
        session: Session = self.session_factory()
        try:
            # Set the search_path on the session's connection immediately.
            session.execute(text(f"SET search_path TO {sanitized_schema}"))
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.close()
            # Removed resetting of schema to default.
