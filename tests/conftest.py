import gzip
import json
import os
from pathlib import Path

import pytest
import requests
from elasticsearch import Elasticsearch
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.elasticsearch import ElasticSearchContainer
from testcontainers.keycloak import KeycloakContainer
from testcontainers.ollama import OllamaContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.vault import VaultContainer

os.environ["TESTING"] = "1"
os.environ["OLLAMA_ENDPOINT"] = "http://localhost:21434"

llm_tag = "bge-m3"
es_image = "elasticsearch:9.3.1"

keycloak = KeycloakContainer(
    username="admin", password="admin", image="bsantanna/quaks-keycloak:v1.3.42"
).with_bind_ports(
    container=8080, host=18080
)

ollama = OllamaContainer(
    ollama_home=f"{Path.home()}/.ollama", image="ollama/ollama:latest"
).with_bind_ports(container=11434, host=21434)

postgres = (
    PostgresContainer(
        image="pgvector/pgvector:pg16", username="postgres", password="postgres"
    )
    .with_bind_ports(container=5432, host=15432)
    .with_volume_mapping(f"{Path.cwd()}/tests/integration", "/mnt/integration")
)

redis = RedisContainer(image="redis:alpine").with_bind_ports(container=6379, host=16379)

vault = (
    VaultContainer("hashicorp/vault:1.18.1")
    .with_bind_ports(container=8200, host=18200)
    .with_env("VAULT_DEV_ROOT_TOKEN_ID", "dev-only-token")
    .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
)

cdp = DockerContainer("chromedp/headless-shell:latest").with_bind_ports(
    container=9222, host=19222
)

elasticsearch = (
    ElasticSearchContainer(es_image, mem_limit="2G")
    .with_bind_ports(container=9200, host=19200)
    .with_env("discovery.type", "single-node")
    .with_env("xpack.security.enabled", "false")
)


def setup_postgres():
    # setup databases
    psql_command = "PGPASSWORD='postgres' psql --username postgres --host 127.0.0.1"
    create_database_command = f"{psql_command} -c 'create database ?;'"
    main_db_command = create_database_command.replace("?", "agent_lab")
    checkpoints_db_command = create_database_command.replace(
        "?", "agent_lab_checkpoints"
    )
    vectors_db_command = create_database_command.replace("?", "agent_lab_vectors")

    postgres.exec(
        [
            "sh",
            "-c",
            f"""
                {main_db_command} &&
                {checkpoints_db_command} &&
                {vectors_db_command}
            """,
        ]
    )


def setup_ollama():
    # pull llm from registry
    if llm_tag not in [e["name"] for e in ollama.list_models()]:
        print(f"Pulling {llm_tag} model")
        ollama.pull_model(llm_tag)


def setup_keycloak():
    keycloak.exec(
        [
            "/opt/keycloak/bin/kcadm.sh",
            "update",
            "realms/master",
            "-s",
            "sslRequired=NONE",
            "--server",
            "http://localhost:8080",
            "--realm",
            "master",
            "--user",
            "admin",
            "--password",
            "admin",
        ]
    )

    data = {
        "client_id": "admin-cli",
        "username": "admin",
        "password": "admin",
        "grant_type": "password",
    }
    response = requests.post(
        "http://localhost:18080/realms/master/protocol/openid-connect/token", data=data
    )
    response.raise_for_status()
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    requests.delete("http://localhost:18080/admin/realms/test-realm", headers=headers)

    realm_data = {"realm": "test-realm", "enabled": True}
    response = requests.post(
        "http://localhost:18080/admin/realms",
        headers=headers,
        data=json.dumps(realm_data),
    )
    response.raise_for_status()

    keycloak.exec(
        [
            "/opt/keycloak/bin/kcadm.sh",
            "update",
            "realms/test-realm",
            "-s",
            "sslRequired=NONE",
            "--server",
            "http://localhost:8080",
            "--realm",
            "master",
            "--user",
            "admin",
            "--password",
            "admin",
        ]
    )

    client_data = {
        "clientId": "test-client",
        "enabled": True,
        "protocol": "openid-connect",
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": True,
        "clientAuthenticatorType": "client-secret",
        "publicClient": False,
        "secret": "test-secret",
    }
    response = requests.post(
        "http://localhost:18080/admin/realms/test-realm/clients",
        headers=headers,
        data=json.dumps(client_data),
    )
    response.raise_for_status()

    # Grant realm-admin role to the service account so /auth/profile can use admin API
    base = "http://localhost:18080/admin/realms/test-realm"
    clients = requests.get(
        f"{base}/clients?clientId=test-client", headers=headers
    ).json()
    client_uuid = clients[0]["id"]

    sa_user = requests.get(
        f"{base}/clients/{client_uuid}/service-account-user", headers=headers
    ).json()
    sa_user_id = sa_user["id"]

    rm_clients = requests.get(
        f"{base}/clients?clientId=realm-management", headers=headers
    ).json()
    rm_client_uuid = rm_clients[0]["id"]

    roles = requests.get(
        f"{base}/clients/{rm_client_uuid}/roles", headers=headers
    ).json()
    realm_admin_role = next(r for r in roles if r["name"] == "realm-admin")

    requests.post(
        f"{base}/users/{sa_user_id}/role-mappings/clients/{rm_client_uuid}",
        headers=headers,
        data=json.dumps([realm_admin_role]),
    )

    user_data = {
        "username": "foo",
        "enabled": True,
        "email": "foo@bar.com",
        "firstName": "Test",
        "lastName": "User",
        "credentials": [{"type": "password", "value": "bar", "temporary": False}],
    }
    response = requests.post(
        "http://localhost:18080/admin/realms/test-realm/users",
        headers=headers,
        data=json.dumps(user_data),
    )
    response.raise_for_status()


def setup_elasticsearch():
    es_url = "http://localhost:19200"
    os.environ["ELASTICSEARCH_URL"] = es_url
    os.environ.pop("ELASTICSEARCH_API_KEY", None)

    es = Elasticsearch(hosts=[es_url])

    # Create indices with correct mappings
    news_mapping = {
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "key_ticker": {"type": "keyword"},
                "key_url": {"type": "keyword"},
                "key_source": {"type": "keyword"},
                "date_reference": {"type": "date", "format": "yyyy-MM-dd"},
                "obj_images": {"type": "object", "dynamic": "true"},
                "text_headline": {"type": "text"},
                "text_author": {"type": "text"},
                "text_summary": {"type": "text"},
                "text_content": {"type": "text"},
            },
        }
    }
    es.indices.create(index="quaks_markets-news_test", body=news_mapping)
    es.indices.put_alias(index="quaks_markets-news_test", name="quaks_markets-news_latest")

    insights_mapping = {
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "date_reference": {"type": "date", "format": "yyyy-MM-dd"},
                "text_executive_summary": {"type": "text"},
                "text_report_html": {"type": "text"},
                "key_language_model_name": {"type": "keyword"},
            },
        }
    }
    es.indices.create(index="quaks_insights-news", body=insights_mapping)

    # Register search templates from Mustache files
    templates_dir = Path.cwd() / "terraform" / "01_elasticsearch" / "search_templates"
    for template_file in templates_dir.glob("*.mustache"):
        template_id = f"{template_file.stem}_template"
        source = template_file.read_text()
        es.put_script(id=template_id, body={"script": {"lang": "mustache", "source": source}})

    # Load fixture data
    fixture_path = Path.cwd() / "tests" / "simulation" / "fixtures" / "es_fixture_data.json.gz"
    with gzip.open(fixture_path, "rt", encoding="utf-8") as f:
        fixture = json.load(f)

    for doc in fixture["markets_news"]:
        es.index(
            index="quaks_markets-news_test",
            id=doc["_id"],
            body=doc["_source"],
        )
    for doc in fixture["insights_news"]:
        es.index(
            index="quaks_insights-news",
            id=doc["_id"],
            body=doc["_source"],
        )

    published_content_mapping = {
        "dynamic": "strict",
        "properties": {
            "key_skill_name": {"type": "keyword"},
            "key_author_username": {"type": "keyword"},
            "key_language_model_name": {"type": "keyword"},
            "text_executive_summary": {"type": "text"},
            "text_report_html": {"type": "text"},
            "date_timestamp": {"type": "date", "format": "strict_date_optional_time"},
            "flag_processed": {"type": "boolean"},
        },
    }
    es.indices.put_index_template(
        name="quaks_published-content_template",
        body={
            "index_patterns": ["quaks_published-content_*"],
            "template": {"mappings": published_content_mapping},
        },
    )
    es.indices.create(index="quaks_published-content_initial", body={"mappings": published_content_mapping})
    es.indices.put_alias(
        index="quaks_published-content_initial", name="quaks_published-content_latest"
    )

    es.indices.refresh(index="quaks_markets-news_test")
    es.indices.refresh(index="quaks_insights-news")


@pytest.fixture(scope="function", autouse=True)
def set_access_token():
    user_credentials = {
        "client_id": "test-client",
        "client_secret": "test-secret",
        "grant_type": "password",
        "username": "foo",
        "password": "bar",
    }
    response = requests.post(
        "http://localhost:18080/realms/test-realm/protocol/openid-connect/token",
        data=user_credentials,
    )
    response.raise_for_status()
    os.environ["ACCESS_TOKEN"] = response.json()["access_token"]


@pytest.fixture(scope="session", autouse=True)
def test_config(request):
    keycloak.start()
    ollama.start()
    postgres.start()
    redis.start()
    vault.start()
    cdp.start()
    elasticsearch.start()

    def remove_container():
        keycloak.stop()
        ollama.stop()
        postgres.stop()
        redis.stop()
        vault.stop()
        cdp.stop()
        elasticsearch.stop()

    request.addfinalizer(remove_container)
    wait_for_logs(keycloak, "Listening on")
    wait_for_logs(ollama, "Listening on")
    wait_for_logs(postgres, "database system is ready to accept connections")
    wait_for_logs(redis, "Ready to accept connections")
    wait_for_logs(
        vault, "Development mode should NOT be used in production installations!"
    )
    wait_for_logs(cdp, "DevTools listening on")

    setup_keycloak()
    setup_ollama()
    setup_postgres()
    setup_elasticsearch()

    yield
