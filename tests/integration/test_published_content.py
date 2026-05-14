import uuid

import pytest
from elasticsearch import Elasticsearch

from app.domain.exceptions.base import DuplicateEntryError, UnauthorizedSkillError
from app.services.published_content import PublishedContentService


@pytest.fixture
def es_client():
    return Elasticsearch(hosts=["http://localhost:19200"])


@pytest.fixture
def service(es_client):
    return PublishedContentService(es=es_client)


def test_publish_content_creates_document(service, es_client):
    unique = uuid.uuid4().hex[:8]
    service.publish(
        executive_summary=f"Test summary {unique}",
        report_html=f"<h1>Test report {unique}</h1>",
        skill_name="/news-analyst",
        author_username=f"testuser-{unique}",
        language_model_name="some-model-id",
    )

    es_client.indices.refresh(index="quaks_published-content_latest")
    result = es_client.search(
        index="quaks_published-content_latest",
        body={"query": {"term": {"key_author_username": f"testuser-{unique}"}}},
    )
    hits = result["hits"]["hits"]
    assert len(hits) == 1
    src = hits[0]["_source"]
    assert src["text_executive_summary"] == f"Test summary {unique}"
    assert src["text_report_html"] == f"<h1>Test report {unique}</h1>"
    assert src["key_skill_name"] == "news_analyst"
    assert src["key_language_model_name"] == "some-model-id"
    assert src["flag_processed"] is False


def test_publish_content_canonicalizes_hermes_prefixed_skill(service, es_client):
    unique = uuid.uuid4().hex[:8]
    service.publish(
        executive_summary=f"Hermes prefix {unique}",
        report_html="<p>hermes</p>",
        skill_name="quaks:financial-analyst-v1",
        author_username=f"hermesuser-{unique}",
        language_model_name="some-model-id",
    )

    es_client.indices.refresh(index="quaks_published-content_latest")
    result = es_client.search(
        index="quaks_published-content_latest",
        body={"query": {"term": {"key_author_username": f"hermesuser-{unique}"}}},
    )
    hits = result["hits"]["hits"]
    assert len(hits) == 1
    assert hits[0]["_source"]["key_skill_name"] == "financial_analyst_v1"


def test_publish_content_duplicate_raises_error(service):
    unique = uuid.uuid4().hex[:8]
    service.publish(
        executive_summary=f"Dup summary {unique}",
        report_html="<p>dup</p>",
        skill_name="/news_analyst",
        author_username=f"dupuser-{unique}",
        language_model_name="claude-opus-4-7",
    )
    with pytest.raises(DuplicateEntryError):
        service.publish(
            executive_summary=f"Dup summary {unique}",
            report_html="<p>different html</p>",
            skill_name="/news_analyst",
            author_username=f"dupuser-{unique}",
            language_model_name="claude-opus-4-7",
        )


def test_publish_content_rejects_unauthorized_skill(service):
    unique = uuid.uuid4().hex[:8]
    with pytest.raises(UnauthorizedSkillError):
        service.publish(
            executive_summary=f"Unauthorized {unique}",
            report_html="<p>nope</p>",
            skill_name="/quant_analyst",
            author_username=f"user-{unique}",
            language_model_name="claude-opus-4-7",
        )


def test_publish_content_sets_alias(service, es_client):
    unique = uuid.uuid4().hex[:8]
    service.publish(
        executive_summary=f"Alias test {unique}",
        report_html="<p>alias</p>",
        skill_name="/news_analyst",
        author_username=f"aliasuser-{unique}",
        language_model_name="claude-opus-4-7",
    )
    assert es_client.indices.exists_alias(name="quaks_published-content_latest")
