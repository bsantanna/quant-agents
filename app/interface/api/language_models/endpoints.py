from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Response, status
from fastapi.security import HTTPBearer
from fastapi_keycloak_middleware import get_user
from typing_extensions import List

from app.core.container import Container
from app.domain.models import LanguageModel as DomainLanguageModel
from app.infrastructure.auth.schema import User
from app.interface.api.language_models.schema import (
    LanguageModelCreateRequest,
    LanguageModelExpanded,
    LanguageModel,
    LanguageModelSetting,
    LanguageModelSettingUpdateRequest,
    LanguageModelUpdateRequest,
)
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.get(
    "/list",
    dependencies=[Depends(bearer_scheme)],
    response_model=List[LanguageModel],
    summary="List all language models",
    description="""
    Retrieve a complete list of all configured language models in the system.

    This endpoint returns all language models regardless of their integration type
    or current status. Each model includes basic information like ID, tag, and
    integration details.

    **Use cases:**
    - Display available models in UI dropdowns
    - System administration and monitoring
    - Model selection for agents
    - Integration health checks
    """,
    response_description="List of all configured language models",
    responses={
        200: {
            "description": "Successfully retrieved language models",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "lm_123",
                            "integration_id": "openai_int_456",
                            "language_model_tag": "gpt-4",
                            "is_active": True,
                            "created_at": "2024-01-15T10:00:00Z",
                        },
                        {
                            "id": "lm_789",
                            "integration_id": "anthropic_int_012",
                            "language_model_tag": "claude-3-sonnet",
                            "is_active": True,
                            "created_at": "2024-01-15T11:00:00Z",
                        },
                    ]
                }
            },
        }
    },
)
@inject
async def get_list(
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    user: User = Depends(get_user),
):
    """
    Get all configured language models.

    Returns:
        List[LanguageModel]: All language models in the system
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_models = language_model_service.get_language_models(schema)
    return [LanguageModel.model_validate(lm) for lm in language_models]


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(bearer_scheme)],
    response_model=LanguageModel,
    summary="Create a new language model",
    description="""
    Create a new language model configuration linked to an existing integration.

    This endpoint creates a new language model entry that references an existing
    integration (OpenAI, Anthropic, etc.) and specifies which model to use
    (gpt-4, claude-3, etc.).

    **Prerequisites:**
    - Integration must already exist and be properly configured
    - Model tag must be supported by the integration
    - Integration must have valid API credentials

    **Post-Creation Steps:**
    - Configure model settings (temperature, max_tokens, etc.)
    - Test model connectivity
    - Assign to agents as needed

    **Example Model Tags by Integration:**
    - OpenAI: gpt-4, gpt-3.5-turbo, gpt-4-turbo
    - Anthropic: claude-3-opus, claude-3-sonnet, claude-3-haiku
    - xAI: grok-3, grok-2-vision,
    """,
    response_description="Newly created language model",
    responses={
        201: {
            "description": "Language model created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_new_123",
                        "integration_id": "openai_int_456",
                        "language_model_tag": "gpt-4",
                        "is_active": True,
                        "created_at": "2024-01-15T12:00:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid request data unsupported model tag"},
        404: {"description": "Integration not found"},
        422: {"description": "Invalid request data format"},
    },
)
@inject
async def add(
    language_model_data: LanguageModelCreateRequest = Body(
        ...,
        description="Language model creation data",
        example={"integration_id": "openai_int_456", "language_model_tag": "gpt-4"},
    ),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    user: User = Depends(get_user),
):
    """
    Create a new language model configuration.

    Returns:
        LanguageModel: Newly created language model

    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model = language_model_service.create_language_model(
        integration_id=language_model_data.integration_id,
        language_model_tag=language_model_data.language_model_tag,
        schema=schema,
    )
    return LanguageModel.model_validate(language_model)


@router.get(
    "/{language_model_id}",
    dependencies=[Depends(bearer_scheme)],
    response_model=LanguageModelExpanded,
    summary="Get language model details",
    description="""
    Retrieve detailed information about a specific language model including
    all its configuration settings.

    This endpoint returns an expanded view that includes:
    - Basic model information (ID, tag, integration)
    - All configuration settings (temperature, max_tokens, etc.)
    - Integration-specific parameters
    - Model capabilities and limitations

    **Use cases:**
    - Display model configuration in admin interface
    - Debug model behavior and settings
    - Export model configurations
    - Validate model setup before agent creation
    """,
    response_description="Detailed language model information with all settings",
    responses={
        200: {
            "description": "Language model details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "integration_id": "openai_int_456",
                        "language_model_tag": "gpt-4",
                        "is_active": True,
                        "created_at": "2024-01-15T10:00:00Z",
                        "lm_settings": [
                            {
                                "id": "setting_001",
                                "setting_key": "temperature",
                                "setting_value": "0.7",
                                "language_model_id": "lm_123",
                            },
                            {
                                "id": "setting_002",
                                "setting_key": "max_tokens",
                                "setting_value": "2048",
                                "language_model_id": "lm_123",
                            },
                        ],
                    }
                }
            },
        },
        404: {"description": "Language model not found"},
    },
)
@inject
async def get_by_id(
    language_model_id: str,
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    language_model_setting_service: LanguageModelSettingService = Depends(
        Provide[Container.language_model_setting_service]
    ),
    user: User = Depends(get_user),
):
    """
    Get detailed information about a specific language model.

    Returns:
        LanguageModelExpanded: Complete model details with settings

    Raises:
        HTTPException: If model not found or invalid ID
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model = language_model_service.get_language_model_by_id(
        language_model_id, schema
    )
    return _format_expanded_response(
        language_model, language_model_setting_service, schema
    )


@router.delete(
    "/delete/{language_model_id}",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a language model",
    description="""
    Permanently delete a language model configuration from the system.

    **Warning:** This action cannot be undone and will:
    - Remove the language model and all its settings
    - Disable any agents currently using this model
    - Break existing conversations that reference this model

    **Before deletion, ensure:**
    - No active agents are using this model
    - Important conversations are backed up
    - Alternative models are configured for affected agents

    **Safe Deletion Process:**
    1. Identify agents using this model
    2. Migrate agents to alternative models
    3. Test agent functionality with new models
    4. Proceed with deletion
    """,
    response_description="Language model successfully deleted (no content returned)",
    responses={
        204: {"description": "Language model successfully deleted"},
        404: {"description": "Language model not found"},
    },
)
@inject
async def remove(
    language_model_id: str,
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    user: User = Depends(get_user),
):
    """
    Delete a language model by ID.

    Returns:
        Response: 204 No Content on success

    Raises:
        HTTPException: If model not found or deletion fails
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model_service.delete_language_model_by_id(language_model_id, schema)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/update",
    dependencies=[Depends(bearer_scheme)],
    response_model=LanguageModel,
    summary="Update language model configuration",
    description="""
    Update the basic configuration of an existing language model.

    Currently supports updating the language model tag, which changes
    which specific model is used within the same integration.

    **Use cases:**
    - Upgrade to newer model versions (gpt-3.5 → gpt-4)
    - Switch between model variants (claude-3-sonnet → claude-3-opus)
    - Test different models without recreating the entire configuration

    **Important Notes:**
    - Model settings (temperature, max_tokens) are preserved
    - Existing conversations remain linked to the model
    - Agent configurations automatically use the new model
    - Ensure the new model tag is supported by the integration
    """,
    response_description="Updated language model configuration",
    responses={
        200: {
            "description": "Language model updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "integration_id": "openai_int_456",
                        "language_model_tag": "gpt-4-turbo",
                        "is_active": True,
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T15:30:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid request data unsupported model tag"},
        404: {"description": "Language model or integration not found"},
        422: {"description": "Invalid request data unprocessable entity"},
    },
)
@inject
async def update(
    language_model_data: LanguageModelUpdateRequest = Body(
        ...,
        description="Language model update data",
        example={"language_model_id": "lm_123", "language_model_tag": "gpt-4-turbo"},
    ),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    user: User = Depends(get_user),
):
    """
    Update an existing language model configuration.

    Returns:
        LanguageModel: Updated language model

    Raises:
        HTTPException: If model not found or update fails
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model = language_model_service.update_language_model(
        language_model_id=language_model_data.language_model_id,
        language_model_tag=language_model_data.language_model_tag,
        integration_id=language_model_data.integration_id,
        schema=schema,
    )
    return LanguageModel.model_validate(language_model)


@router.post(
    "/update_setting",
    dependencies=[Depends(bearer_scheme)],
    response_model=LanguageModelExpanded,
    summary="Update language model setting",
    description="""
    Update a specific configuration setting for a language model.

    Language models support various settings that control their behavior:

    **Common Settings:**
    - `temperature`: Controls randomness (0.0-1.0)
    - `max_tokens`: Maximum response length (1-4096+)
    - `top_p`: Nucleus sampling parameter (0.0-1.0)
    - `frequency_penalty`: Reduces repetition (-2.0 to 2.0)
    - `presence_penalty`: Encourages topic diversity (-2.0 to 2.0)

    **Best Practices:**
    - Test setting changes with sample conversations
    - Document setting purposes for team members
    - Use conservative values for production environments
    - Monitor token usage after max_tokens changes
    """,
    response_description="Updated language model with all settings",
    responses={
        200: {
            "description": "Setting updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lm_123",
                        "integration_id": "openai_int_456",
                        "language_model_tag": "gpt-4",
                        "is_active": True,
                        "created_at": "2024-01-15T10:00:00Z",
                        "lm_settings": [
                            {
                                "id": "setting_001",
                                "setting_key": "temperature",
                                "setting_value": "0.9",
                                "language_model_id": "lm_123",
                                "updated_at": "2024-01-15T16:00:00Z",
                            }
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid setting key or value"},
        404: {"description": "Language model not found"},
        422: {"description": "Invalid request data unprocessable entity"},
    },
)
@inject
async def update_setting(
    language_model_data: LanguageModelSettingUpdateRequest = Body(
        ...,
        description="Language model setting update data",
        example={
            "language_model_id": "lm_123",
            "setting_key": "temperature",
            "setting_value": "0.9",
        },
    ),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    language_model_setting_service: LanguageModelSettingService = Depends(
        Provide[Container.language_model_setting_service]
    ),
    user: User = Depends(get_user),
):
    """
    Update a specific setting for a language model.

    Returns:
        LanguageModelExpanded: Updated model with all settings

    Raises:
        HTTPException: If model not found or setting update fails
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    language_model_setting_service.update_by_key(
        language_model_id=language_model_data.language_model_id,
        setting_key=language_model_data.setting_key,
        setting_value=language_model_data.setting_value,
        schema=schema,
    )

    language_model = language_model_service.get_language_model_by_id(
        language_model_id=language_model_data.language_model_id,
        schema=schema,
    )

    return _format_expanded_response(
        language_model, language_model_setting_service, schema
    )


def _format_expanded_response(
    language_model: DomainLanguageModel,
    language_model_setting_service: LanguageModelSettingService,
    schema: str,
) -> LanguageModelExpanded:
    """
    Format an expanded language model response with all settings.

    Args:
        language_model: The language model domain object
        language_model_setting_service: Service to retrieve settings

    Returns:
        LanguageModelExpanded: Complete model data with settings
    """
    settings = language_model_setting_service.get_language_model_settings(
        language_model.id, schema
    )
    response = LanguageModelExpanded.model_validate(language_model)
    response.lm_settings = [
        LanguageModelSetting.model_validate(setting) for setting in settings
    ]
    return response
