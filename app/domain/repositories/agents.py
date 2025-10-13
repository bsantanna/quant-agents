from datetime import datetime
from uuid import uuid4

from typing_extensions import Iterator

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Agent, AgentSetting
from app.infrastructure.database.sql import Database


class AgentRepository:
    def __init__(
        self,
        db: Database,
    ) -> None:
        self.db = db

    def get_all(self, schema: str) -> Iterator[Agent]:
        with self.db.session(schema_name=schema) as session:
            return session.query(Agent).filter(Agent.is_active).all()

    def get_by_id(self, agent_id: str, schema: str) -> Agent:
        with self.db.session(schema_name=schema) as session:
            agent = (
                session.query(Agent)
                .filter(Agent.id == agent_id, Agent.is_active)
                .first()
            )
            if not agent:
                raise AgentNotFoundError(agent_id)
            return agent

    def add(
        self, agent_name: str, agent_type: str, language_model_id: str, schema: str
    ) -> Agent:
        gen_id = uuid4()
        with self.db.session(schema_name=schema) as session:
            agent = Agent(
                id=str(gen_id),
                is_active=True,
                created_at=datetime.now(),
                agent_name=agent_name,
                agent_type=agent_type,
                agent_summary="",
                language_model_id=language_model_id,
            )
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent

    def update_agent(
        self,
        agent_id: str,
        agent_name: str,
        language_model_id: str,
        schema: str,
        agent_summary: str = None,
    ) -> Agent:
        with self.db.session(schema_name=schema) as session:
            entity: Agent = (
                session.query(Agent)
                .filter(Agent.id == agent_id, Agent.is_active)
                .first()
            )
            if not entity:
                raise AgentNotFoundError(agent_id)

            entity.agent_name = agent_name
            entity.language_model_id = language_model_id
            if agent_summary is not None:
                entity.agent_summary = agent_summary
            session.commit()
            session.refresh(entity)
            return entity

    def delete_by_id(self, agent_id: str, schema: str) -> None:
        with self.db.session(schema_name=schema) as session:
            entity: Agent = (
                session.query(Agent)
                .filter(Agent.id == agent_id, Agent.is_active)
                .first()
            )
            if not entity:
                raise AgentNotFoundError(agent_id)

            entity.is_active = False
            session.commit()


class AgentNotFoundError(NotFoundError):
    entity_name: str = "Agent"


class AgentSettingRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_all(self, agent_id: str, schema: str) -> Iterator[AgentSetting]:
        with self.db.session(schema_name=schema) as session:
            return (
                session.query(AgentSetting)
                .filter(AgentSetting.agent_id == agent_id)
                .all()
            )

    def add(
        self, agent_id: str, setting_key: str, setting_value: str, schema: str
    ) -> AgentSetting:
        gen_id = uuid4()
        with self.db.session(schema_name=schema) as session:
            agent_setting = AgentSetting(
                id=str(gen_id),
                agent_id=agent_id,
                setting_key=setting_key,
                setting_value=setting_value,
            )
            session.add(agent_setting)
            session.commit()
            session.refresh(agent_setting)
            return agent_setting

    def update_by_key(
        self, agent_id: str, setting_key: str, setting_value: str, schema: str
    ) -> AgentSetting:
        with self.db.session(schema_name=schema) as session:
            entity: AgentSetting = (
                session.query(AgentSetting)
                .filter(
                    AgentSetting.agent_id == agent_id,
                    AgentSetting.setting_key == setting_key,
                )
                .first()
            )
            if not entity:
                raise AgentSettingNotFoundError(agent_id)

            entity.setting_value = setting_value
            session.commit()
            session.refresh(entity)
            return entity


class AgentSettingNotFoundError(NotFoundError):
    entity_name: str = "AgentSetting"
