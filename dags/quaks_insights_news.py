from airflow.sdk import DAG, task
from airflow.providers.cncf.kubernetes.secret import Secret
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 0,
}

dag = DAG(
    "quaks_insights_news",
    default_args=default_args,
    schedule="0 8,20 * * *",
    catchup=False,
)


@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="airflow",
    secrets=[Secret('env', None, 'quaks-dags-secrets')],
)
def generate_insights_news():
    import hashlib
    import json
    import os
    import requests
    from datetime import datetime
    from uuid import uuid4


    INTEGRATION_ENDPOINTS = {
        "xai_api_v1": "https://api.x.ai/v1/",
        "openai_api_v1": "https://api.openai.com/v1/",
        "anthropic_api_v1": "https://api.anthropic.com",
    }

    api_url = os.environ.get("QUAKS_API_URL")
    username = os.environ.get("QUAKS_SERVICE_ACCOUNT_USERNAME")
    password = os.environ.get("QUAKS_SERVICE_ACCOUNT_SECRET")
    language_model_tag = os.environ.get("QUAKS_LANGUAGE_MODEL_TAG", "grok-4-1-fast-non-reasoning")
    integration_type = os.environ.get("QUAKS_INTEGRATION_TYPE", "xai_api_v1")
    integration_api_key = os.environ.get("QUAKS_INTEGRATION_API_KEY")
    es_url = os.environ.get("ELASTICSEARCH_URL")
    es_api_key = os.environ.get("ELASTICSEARCH_API_KEY")

    # 1. Authenticate
    print("Authenticating with service account...")
    login_response = requests.post(
        f"{api_url}/auth/login",
        json={"username": username, "password": password},
    )
    login_response.raise_for_status()
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("Authentication successful.")

    # 2. Create integration
    print(f"Creating integration ({integration_type})...")
    api_endpoint = INTEGRATION_ENDPOINTS.get(integration_type, "http://localhost:11434")
    integration_response = requests.post(
        f"{api_url}/integrations/create",
        json={
            "integration_type": integration_type,
            "api_endpoint": api_endpoint,
            "api_key": integration_api_key,
        },
        headers=headers,
    )
    integration_response.raise_for_status()
    integration_id = integration_response.json()["id"]
    print(f"Integration created: {integration_id}")

    # 3. Create language model
    print(f"Creating language model ({language_model_tag})...")
    llm_response = requests.post(
        f"{api_url}/llms/create",
        json={
            "integration_id": integration_id,
            "language_model_tag": language_model_tag,
        },
        headers=headers,
    )
    llm_response.raise_for_status()
    language_model_id = llm_response.json()["id"]
    print(f"Language model created: {language_model_id}")

    # 4. Create agent
    agent_name = f"insights_news_{uuid4()}"
    print(f"Creating agent ({agent_name})...")
    agent_response = requests.post(
        f"{api_url}/agents/create",
        json={
            "agent_name": agent_name,
            "agent_type": "quaks_news_analyst",
            "language_model_id": language_model_id,
        },
        headers=headers,
    )
    agent_response.raise_for_status()
    agent_id = agent_response.json()["id"]
    print(f"Agent created: {agent_id}")

    # 5. Send BATCH_ETL message
    print("Sending BATCH_ETL message...")
    message_response = requests.post(
        f"{api_url}/messages/post",
        json={
            "agent_id": agent_id,
            "message_role": "human",
            "message_content": "BATCH_ETL",
        },
        headers=headers,
        timeout=600,
    )
    message_response.raise_for_status()
    result = message_response.json()
    print("BATCH_ETL message processed successfully.")

    response_data = result.get("response_data", {})
    report_html = response_data.get("report_html", result.get("message_content", ""))
    executive_summary = response_data.get("executive_summary", "")

    # 6. Index into Elasticsearch
    if not executive_summary or not executive_summary.strip():
        print("WARNING: Executive summary is empty. Skipping Elasticsearch indexing and X post.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    doc_id = hashlib.md5(f"insights_news_{today}_{agent_id}".encode("utf-8")).hexdigest()
    index_name = "quaks_insights-news"

    doc = {
        "date_reference": today,
        "text_executive_summary": executive_summary,
        "text_report_html": report_html,
        "key_language_model_name": language_model_tag,
    }

    bulk_body = json.dumps({"index": {"_index": index_name, "_id": doc_id}}) + "\n" + json.dumps(doc) + "\n"

    print(f"Indexing insights into {index_name} (doc_id: {doc_id})...")
    es_response = requests.post(
        f"{es_url}/_bulk",
        headers={
            "Authorization": f"ApiKey {es_api_key}",
            "Content-Type": "application/x-ndjson",
        },
        data=bulk_body.encode("utf-8"),
    )
    es_response.raise_for_status()
    print(f"Indexing complete: {es_response.json()}")

    # 7. Post to X (@quaksai)
    try:
        from requests_oauthlib import OAuth1Session

        x_consumer_key = os.environ.get("X_CONSUMER_KEY")
        x_consumer_secret = os.environ.get("X_CONSUMER_SECRET")
        x_access_token = os.environ.get("X_ACCESS_TOKEN")
        x_access_token_secret = os.environ.get("X_ACCESS_TOKEN_SECRET")
        article_url_pattern = os.environ.get("QUAKS_ARTICLE_URL_PATTERN")

        if not all([x_consumer_key, x_consumer_secret, x_access_token, x_access_token_secret, article_url_pattern]):
            print("WARNING: X credentials or article URL pattern not configured. Skipping X post.")
        else:
            article_url = f"{article_url_pattern}/{index_name}/{doc_id}"

            tweet_text = (
                f"{executive_summary.strip()}\n\n"
                f"See more: {article_url}"
            )

            max_chars = 280
            if len(tweet_text) > max_chars:
                available = max_chars - len(f"Executive Summary:\n\n\n\nSee more: {article_url}") - 3
                tweet_text = (
                    f"{executive_summary.strip()[:available]}...\n\n"
                    f"See more: {article_url}"
                )

            oauth = OAuth1Session(
                x_consumer_key,
                client_secret=x_consumer_secret,
                resource_owner_key=x_access_token,
                resource_owner_secret=x_access_token_secret,
            )

            print("Posting to X...")
            x_response = oauth.post("https://api.x.com/2/tweets", json={"text": tweet_text})

            if x_response.status_code == 201:
                post_id = x_response.json()["data"]["id"]
                print(f"Posted to X successfully. Post ID: {post_id}")
            else:
                print(f"WARNING: X post failed. Status: {x_response.status_code}, Response: {x_response.text}")
    except Exception as e:
        print(f"WARNING: Failed to post to X: {e}")


with dag:
    generate_insights_news()
