from unittest.mock import MagicMock
import pytest
from elasticsearch import NotFoundError as ESNotFoundError
from app.services.published_content import PublishedContentService
from app.domain.exceptions.base import (
    PublishedContentNotFoundError,
    UnauthorizedSkillError,
)

@pytest.fixture
def mock_es():
    return MagicMock()

@pytest.fixture
def service(mock_es):
    return PublishedContentService(es=mock_es)

def test_publish_success(service, mock_es):
    mock_es.indices.exists_alias.return_value = False

    doc_id = service.publish(
        "summary", "html", "/news-analyst", "author", "some-model-id"
    )

    assert doc_id is not None
    mock_es.index.assert_called_once()
    indexed_doc = mock_es.index.call_args[1]["document"]
    assert indexed_doc["key_language_model_name"] == "some-model-id"
    assert indexed_doc["key_skill_name"] == "news_analyst"
    mock_es.indices.update_aliases.assert_called_once()

def test_publish_rejects_unauthorized_skill(service, mock_es):
    with pytest.raises(UnauthorizedSkillError):
        service.publish(
            "summary", "html", "/quant_analyst", "author", "some-model-id"
        )
    mock_es.index.assert_not_called()

@pytest.mark.parametrize("skill_name,expected_canonical", [
    ("news_analyst", "news_analyst"),
    ("news-analyst", "news_analyst"),
    ("financial_analyst_v1", "financial_analyst_v1"),
    ("financial-analyst-v1", "financial_analyst_v1"),
    ("/news_analyst", "news_analyst"),
    ("/news-analyst", "news_analyst"),
    ("/financial-analyst-v1", "financial_analyst_v1"),
    ("quaks-agents:news_analyst", "news_analyst"),
    ("quaks-agents:news-analyst", "news_analyst"),
    ("quaks-agents:financial-analyst-v1", "financial_analyst_v1"),
    ("quaks:news-analyst", "news_analyst"),
    ("quaks:financial-analyst-v1", "financial_analyst_v1"),
])
def test_publish_accepts_allowed_skill_suffixes(
    skill_name, expected_canonical, service, mock_es
):
    mock_es.indices.exists_alias.return_value = True
    doc_id = service.publish("summary", "html", skill_name, "author", "model")
    assert doc_id is not None
    mock_es.index.assert_called_once()
    indexed_doc = mock_es.index.call_args[1]["document"]
    assert indexed_doc["key_skill_name"] == expected_canonical

@pytest.mark.parametrize("skill_name", [
    "",
    "news_analyst_v2",
    "news-analyst-v2",
    "financial_analyst_v1_extended",
    "financial-analyst-v1-extended",
    "unknown",
])
def test_publish_rejects_non_matching_skill_suffixes(skill_name, service, mock_es):
    with pytest.raises(UnauthorizedSkillError):
        service.publish("summary", "html", skill_name, "author", "model")
    mock_es.index.assert_not_called()

def test_get_by_id_success(service, mock_es):
    mock_es.get.return_value = {"_source": {"content": "data"}}
    
    result = service.get_by_id("id1")
    assert result == {"content": "data"}

def test_get_by_id_not_found(service, mock_es):
    mock_es.get.side_effect = ESNotFoundError("not found", MagicMock(), MagicMock())
    
    with pytest.raises(PublishedContentNotFoundError):
        service.get_by_id("id1")

def test_cancel_publishing_success(service, mock_es):
    mock_es.get.return_value = {"_index": "index1"}
    
    service.cancel_publishing("id1")
    
    mock_es.update.assert_called_once()
    assert mock_es.update.call_args[1]["doc"] == {"flag_cancelled": True}
