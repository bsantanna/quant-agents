import hashlib
from datetime import datetime, timezone

from elasticsearch import ConflictError, Elasticsearch
from elasticsearch import NotFoundError as ESNotFoundError

from app.domain.exceptions.base import (
    DuplicateEntryError,
    PublishedContentNotFoundError,
    UnauthorizedSkillError,
)


class PublishedContentService:
    INDEX_ALIAS = "quaks_published-content_latest"
    ALLOWED_SKILLS = frozenset({"news_analyst", "financial_analyst_v1"})

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    def _dated_index(self) -> str:
        return f"quaks_published-content_{datetime.now(timezone.utc).strftime('%d_%m_%Y')}"

    def publish(
        self,
        executive_summary: str,
        report_html: str,
        skill_name: str,
        author_username: str,
        language_model_name: str,
    ) -> str:
        if not any(skill_name.endswith(allowed) for allowed in self.ALLOWED_SKILLS):
            raise UnauthorizedSkillError(skill_name)
        doc_id = hashlib.sha256(
            (executive_summary + author_username + skill_name).encode()
        ).hexdigest()
        doc = {
            "text_executive_summary": executive_summary,
            "text_report_html": report_html,
            "key_skill_name": skill_name,
            "key_author_username": author_username,
            "key_language_model_name": language_model_name,
            "date_timestamp": datetime.now(timezone.utc).isoformat(),
            "flag_processed": False,
        }
        try:
            dated_index = self._dated_index()
            self.es.index(
                index=dated_index,
                id=doc_id,
                document=doc,
                op_type="create",
            )
            if not self.es.indices.exists_alias(
                index=dated_index, name=self.INDEX_ALIAS
            ):
                self.es.indices.update_aliases(
                    actions=[
                        {"remove": {"index": "quaks_published-content_*", "alias": self.INDEX_ALIAS}},
                        {"add": {"index": dated_index, "alias": self.INDEX_ALIAS}},
                    ]
                )
        except ConflictError:
            raise DuplicateEntryError("Content")
        return doc_id

    def get_by_id(self, doc_id: str) -> dict:
        try:
            resp = self.es.get(index=self.INDEX_ALIAS, id=doc_id)
            return resp["_source"]
        except ESNotFoundError:
            raise PublishedContentNotFoundError(doc_id)

    def cancel_publishing(self, doc_id: str) -> None:
        try:
            resp = self.es.get(index=self.INDEX_ALIAS, id=doc_id)
            concrete_index = resp["_index"]
            self.es.update(
                index=concrete_index,
                id=doc_id,
                doc={"flag_cancelled": True},
            )
        except ESNotFoundError:
            raise PublishedContentNotFoundError(doc_id)
