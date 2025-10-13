import json
import os
from pathlib import Path

import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.keycloak import KeycloakContainer
from testcontainers.ollama import OllamaContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.vault import VaultContainer

os.environ["TESTING"] = "1"
os.environ["OLLAMA_ENDPOINT"] = "http://localhost:21434"

llm_tag = "bge-m3"

keycloak = KeycloakContainer(username="admin", password="admin").with_bind_ports(
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


def setup_postgres():
    # setup databases
    psql_command = "PGPASSWORD='postgres' psql --username postgres --host 127.0.0.1"
    create_database_command = f"{psql_command} -c 'create database ?;'"
    main_db_command = create_database_command.replace("?", "agent_lab")
    checkpoints_db_command = create_database_command.replace(
        "?", "agent_lab_checkpoints"
    )
    vectors_db_command = create_database_command.replace("?", "agent_lab_vectors")
    copy_dump_command = "cp /mnt/integration/pgvector_dump.sql.gz /tmp/ && gunzip /tmp/pgvector_dump.sql.gz"
    restore_dump_command = (
        f"{psql_command} -d agent_lab_vectors < /tmp/pgvector_dump.sql"
    )

    postgres.exec(
        [
            "sh",
            "-c",
            f"""
                {main_db_command} &&
                {checkpoints_db_command} &&
                {vectors_db_command} &&
                {copy_dump_command} &&
                {restore_dump_command}
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

    def remove_container():
        keycloak.stop()
        ollama.stop()
        postgres.stop()
        redis.stop()
        vault.stop()
        cdp.stop()

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

    yield
