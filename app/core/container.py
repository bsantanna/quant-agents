import os

import hvac
from dependency_injector import containers, providers

from app.domain.repositories.agents import AgentRepository, AgentSettingRepository
from app.domain.repositories.attachments import AttachmentRepository
from app.domain.repositories.integrations import IntegrationRepository
from app.domain.repositories.language_models import (
    LanguageModelRepository,
    LanguageModelSettingRepository,
)
from app.domain.repositories.messages import MessageRepository
from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.sql import Database
from app.infrastructure.database.vectors import DocumentRepository
from app.infrastructure.metrics.tracer import Tracer
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.adaptive_rag.agent import AdaptiveRagAgent
from app.services.agent_types.base import AgentUtils
from app.services.agent_types.business.voice_memos.agent import (
    VoiceMemosAgent,
    AzureEntraIdVoiceMemosAgent,
    FastVoiceMemosAgent,
)
from app.services.agent_types.coordinator_planner_supervisor.agent import (
    CoordinatorPlannerSupervisorAgent,
)
from app.services.agent_types.react_rag.agent import ReactRagAgent
from app.services.agent_types.registry import AgentRegistry
from app.services.agent_types.test_echo.test_echo_agent import TestEchoAgent
from app.services.agent_types.vision_document.agent import VisionDocumentAgent
from app.services.agents import AgentService
from app.services.attachments import AttachmentService
from app.services.auth import AuthService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService
from app.services.messages import MessageService
from app.services.tasks import TaskNotificationService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.interface.api.agents.endpoints",
            "app.interface.api.attachments.endpoints",
            "app.interface.api.auth.endpoints",
            "app.interface.api.integrations.endpoints",
            "app.interface.api.language_models.endpoints",
            "app.interface.api.messages.endpoints",
        ]
    )

    config_file = None
    if os.getenv("DOCKER"):
        config_file = "config-docker.yml"
    elif os.getenv("TESTING"):
        config_file = "config-test.yml"
    elif os.getenv("DEVELOPING"):
        config_file = "config-dev.yml"

    if config_file is not None:
        config = providers.Configuration(yaml_files=[config_file])
    else:
        vault_url = os.getenv("VAULT_URL")
        vault_token = os.getenv("VAULT_TOKEN")
        vault_client = hvac.Client(url=vault_url, token=vault_token, verify=False)
        app_secrets = vault_client.secrets.kv.read_secret_version(
            raise_on_deleted_version=False, path="app_secrets"
        )

        config = providers.Configuration()
        config.set("api_base_url", app_secrets["data"]["data"]["api_base_url"])
        config.set("auth.enabled", app_secrets["data"]["data"]["auth_enabled"])
        config.set("auth.url", app_secrets["data"]["data"]["auth_url"])
        config.set("auth.realm", app_secrets["data"]["data"]["auth_realm"])
        config.set("auth.client_id", app_secrets["data"]["data"]["auth_client_id"])
        config.set(
            "auth.client_secret", app_secrets["data"]["data"]["auth_client_secret"]
        )
        config.set("cdp_url", app_secrets["data"]["data"]["cdp_url"])
        config.set("vault.url", vault_url)
        config.set("vault.token", vault_token)
        config.set("broker.url", app_secrets["data"]["data"]["broker_url"])
        config.set("db.url", app_secrets["data"]["data"]["db_url"])
        config.set("db.vectors", app_secrets["data"]["data"]["db_vectors"])
        config.set("db.checkpoints", app_secrets["data"]["data"]["db_checkpoints"])

        # dependencies environment variables
        os.environ["TAVILY_API_KEY"] = app_secrets["data"]["data"]["tavily_api_key"]

    db = providers.Singleton(Database, db_url=config.db.url)

    graph_persistence_factory = providers.Singleton(
        GraphPersistenceFactory, db_checkpoints=config.db.checkpoints
    )

    vault_client = providers.Singleton(
        hvac.Client, url=config.vault.url, token=config.vault.token, verify=False
    )

    document_repository = providers.Factory(
        DocumentRepository, db_url=config.db.vectors
    )

    auth_service = providers.Factory(
        AuthService,
        enabled=config.auth.enabled,
        url=config.auth.url,
        realm=config.auth.realm,
        client_id=config.auth.client_id,
        client_secret=config.auth.client_secret,
    )

    integration_repository = providers.Factory(
        IntegrationRepository,
        db=db,
        vault_client=vault_client,
    )

    integration_service = providers.Factory(
        IntegrationService,
        integration_repository=integration_repository,
    )

    task_notification_service = providers.Factory(
        TaskNotificationService,
        redis_url=config.broker.url,
    )

    language_model_setting_repository = providers.Factory(
        LanguageModelSettingRepository,
        db=db,
    )

    language_model_setting_service = providers.Factory(
        LanguageModelSettingService,
        language_model_setting_repository=language_model_setting_repository,
    )

    language_model_repository = providers.Factory(LanguageModelRepository, db=db)

    language_model_service = providers.Factory(
        LanguageModelService,
        language_model_repository=language_model_repository,
        language_model_setting_service=language_model_setting_service,
        integration_service=integration_service,
    )

    attachment_repository = providers.Factory(AttachmentRepository, db=db)

    attachment_service = providers.Factory(
        AttachmentService,
        attachment_repository=attachment_repository,
        document_repository=document_repository,
        language_model_service=language_model_service,
        language_model_setting_service=language_model_setting_service,
        integration_service=integration_service,
        vault_client=vault_client,
    )

    agent_setting_repository = providers.Factory(AgentSettingRepository, db=db)

    agent_setting_service = providers.Factory(
        AgentSettingService,
        agent_setting_repository=agent_setting_repository,
    )

    agent_repository = providers.Factory(AgentRepository, db=db)

    agent_service = providers.Factory(
        AgentService,
        agent_repository=agent_repository,
        agent_setting_service=agent_setting_service,
        language_model_service=language_model_service,
    )

    message_repository = providers.Factory(MessageRepository, db=db)

    message_service = providers.Factory(
        MessageService,
        message_repository=message_repository,
        agent_service=agent_service,
        attachment_service=attachment_service,
    )

    agent_utils = providers.Factory(
        AgentUtils,
        config=config,
        agent_service=agent_service,
        agent_setting_service=agent_setting_service,
        attachment_service=attachment_service,
        language_model_service=language_model_service,
        language_model_setting_service=language_model_setting_service,
        integration_service=integration_service,
        vault_client=vault_client,
        graph_persistence_factory=graph_persistence_factory,
        document_repository=document_repository,
        task_notification_service=task_notification_service,
    )

    adaptive_rag_agent = providers.Factory(AdaptiveRagAgent, agent_utils=agent_utils)

    coordinator_planner_supervisor_agent = providers.Factory(
        CoordinatorPlannerSupervisorAgent, agent_utils=agent_utils
    )

    react_rag_agent = providers.Factory(ReactRagAgent, agent_utils=agent_utils)

    test_echo_agent = providers.Factory(TestEchoAgent, agent_utils=agent_utils)

    vision_document_agent = providers.Factory(
        VisionDocumentAgent, agent_utils=agent_utils
    )

    voice_memos_agent = providers.Factory(
        VoiceMemosAgent,
        agent_utils=agent_utils,
    )

    azure_entra_id_voice_memos_agent = providers.Factory(
        AzureEntraIdVoiceMemosAgent,
        agent_utils=agent_utils,
    )

    fast_voice_memos_agent = providers.Factory(
        FastVoiceMemosAgent, agent_utils=agent_utils
    )

    agent_registry = providers.Singleton(
        AgentRegistry,
        adaptive_rag_agent=adaptive_rag_agent,
        coordinator_planner_supervisor_agent=coordinator_planner_supervisor_agent,
        react_rag_agent=react_rag_agent,
        test_echo_agent=test_echo_agent,
        vision_document_agent=vision_document_agent,
        voice_memos_agent=voice_memos_agent,
        azure_entra_id_voice_memos_agent=azure_entra_id_voice_memos_agent,
        fast_voice_memos_agent=fast_voice_memos_agent,
    )

    tracer = providers.Singleton(Tracer)
