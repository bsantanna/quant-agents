from airflow import DAG
from airflow.decorators import task
from kubernetes.client import (
    V1Volume,
    V1VolumeMount,
    V1PersistentVolumeClaimVolumeSource,
)
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 0,
}

dag = DAG(
    "static_document_data",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
)

volume = V1Volume(
    name="network-data",
    persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
        claim_name="nfs-data-claim"  # on minikube with https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner/
    ),
)

volume_mount = V1VolumeMount(
    name="network-data", mount_path="/mnt/data", sub_path=None, read_only=False
)


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_pptx_files():
    import os
    import subprocess

    # map pptx files
    pptx_files = []
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext == "pptx":
                pptx_files.append(os.path.join(root, filename))

    # convert files using subprocess
    input_data = "\n".join(pptx_files) + "\n"
    try:
        result = subprocess.run(
            ["convert_to_pdf"],
            input=input_data,
            text=True,
            capture_output=True,
            check=True,
        )
        print("Result:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e.stderr)


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_docx_files():
    import os
    import subprocess

    # map docx files
    docx_files = []
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext == "docx":
                docx_files.append(os.path.join(root, filename))

    # convert files using subprocess
    input_data = "\n".join(docx_files) + "\n"
    try:
        result = subprocess.run(
            ["convert_to_pdf"],
            input=input_data,
            text=True,
            capture_output=True,
            check=True,
        )
        print("Result:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e.stderr)


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_pdf_files():
    import os
    import subprocess

    # map pdf files
    pdf_files = []
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext == "pdf":
                pdf_files.append(os.path.join(root, filename))

    # convert files using subprocess
    input_data = "\n".join(pdf_files) + "\n"
    try:
        result = subprocess.run(
            ["extract_images"],
            input=input_data,
            text=True,
            capture_output=True,
            check=True,
        )
        print("Result:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e.stderr)


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_jpg_files():
    import os
    import json
    import requests
    from uuid import uuid4
    from itertools import cycle
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # constants
    agent_lab_endpoint = "http://btech-agent-lab.compute.svc.cluster.local:8000"
    integration_endpoints = ["http://moon.btech.software:11434"]
    model_tag = "granite3.2-vision:latest"
    instructions = (
        "You are studying this material, please generate a comprehensive overview, explain with details. "
        "Make sure your analysis does not overlook details."
    )

    # internal functions
    def create_task_agent(api_endpoint: str):
        integration_response = requests.post(
            url=f"{agent_lab_endpoint}/integrations/create",
            json={
                "api_endpoint": api_endpoint,
                "api_key": "ollama",
                "integration_type": "ollama_api_v1",
            },
            verify=False,
        )
        integration_id = integration_response.json()["id"]

        llm_creation_response = requests.post(
            url=f"{agent_lab_endpoint}/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": model_tag,
            },
            verify=False,
        )
        language_model_id = llm_creation_response.json()["id"]

        agent_creation_response = requests.post(
            url=f"{agent_lab_endpoint}/agents/create",
            json={
                "language_model_id": language_model_id,
                "agent_type": "vision_document",
                "agent_name": f"agent-{uuid4()}",
            },
            verify=False,
        )
        return agent_creation_response.json()["id"]

    def process_jpg_file(file_path: str, task_agent_iterator):
        task_agent = next(task_agent_iterator)
        json_file_path = f"{os.path.splitext(file_path)[0]}.json"
        try:
            if not os.path.exists(json_file_path):
                with open(file_path, "rb") as jpg_file:
                    upload_response = requests.post(
                        url=f"{agent_lab_endpoint}/attachments/upload",
                        files={
                            "file": (
                                os.path.basename(file_path),
                                jpg_file,
                                "image/jpeg",
                            )
                        },
                        verify=False,
                    )
                    attachment_id = upload_response.json()["id"]

                    message_response = requests.post(
                        url=f"{agent_lab_endpoint}/messages/post",
                        json={
                            "message_role": "human",
                            "message_content": instructions,
                            "agent_id": task_agent,
                            "attachment_id": attachment_id,
                        },
                        verify=False,
                    )
                    if message_response.status_code == 200:
                        with open(json_file_path, "w") as json_file:
                            json.dump(message_response.json(), json_file)

                    return (True, file_path, None, task_agent)
            else:
                return (False, file_path, f"File {json_file_path} in place", task_agent)

        except Exception as e:
            print(f"Error while processing {file_path}: {e}")

        return (False, file_path, f"Error processing: {file_path}", task_agent)

    # map jpg files
    jpg_files = []
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext == "jpg":
                jpg_files.append(os.path.join(root, filename))

    if len(jpg_files) > 0:
        # Create task agents
        task_agents = []
        for integration_endpoint in integration_endpoints:
            task_agents.append(create_task_agent(integration_endpoint))

        # Results tracking
        results = {
            "total_files": len(jpg_files),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "agent_usage": {task_agent: 0 for task_agent in task_agents},
        }

        # Create a cyclic iterator for round-robin agent selection
        task_agent_cycle = cycle(task_agents)

        # Execute in parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(integration_endpoints)) as executor:
            future_to_file = {
                executor.submit(process_jpg_file, jpg_file, task_agent_cycle): jpg_file
                for jpg_file in jpg_files
            }

            for future in as_completed(future_to_file):
                success, jpg_file, error_msg, used_agent = future.result()

                results["agent_usage"][used_agent] += 1

                if success:
                    results["successful"] += 1
                    print(f"Successfully processed: {jpg_file} using {used_agent}")
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {"jpg_file": jpg_file, "error": error_msg, "agent": used_agent}
                    )
                    print(
                        f"Failed to process {jpg_file} using {used_agent}: {error_msg}"
                    )

        # Log summary
        print(
            f"Processing complete - Successful: {results['successful']}, Failed: {results['failed']}"
        )
        print(f"Endpoint usage: {results['agent_usage']}")


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_zip_files():
    import os
    import zipfile

    source_dir = "/mnt/data"
    output_dir = "/mnt/data/static_document_result"
    max_zip_size = 14 * 1024 * 1024  # 14MB

    def get_files_sorted_by_size(directory):
        file_list = []
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_list.append((file_size, file_path))

        return sorted(file_list)

    def process_files(files, output_dir, max_zip_size):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        current_zip_index = 1
        current_zip_size = 0
        zip_file_list = []

        for file_size, file_path in files:
            if current_zip_size + file_size > max_zip_size:
                # Create a new zip file when limit is reached
                zip_filename = os.path.join(
                    output_dir, f"archive_{current_zip_index}.zip"
                )
                with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for f in zip_file_list:
                        arcname = os.path.relpath(
                            f, os.path.commonpath(zip_file_list)
                        )  # Preserve folder structure
                        zipf.write(f, arcname)
                print(f"Created: {zip_filename}")

                # Reset for next zip
                current_zip_index += 1
                current_zip_size = 0
                zip_file_list = []

            # Add the current file to the zip batch
            zip_file_list.append(file_path)
            current_zip_size += file_size

        # Zip remaining files (if any)
        if zip_file_list:
            zip_filename = os.path.join(output_dir, f"archive_{current_zip_index}.zip")
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                for f in zip_file_list:
                    arcname = os.path.relpath(f, os.path.commonpath(zip_file_list))
                    zipf.write(f, arcname)

            print(f"Created: {zip_filename}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        files = get_files_sorted_by_size(source_dir)
        process_files(files, output_dir, max_zip_size)


with dag:
    pptx_task = process_pptx_files()
    docx_task = process_docx_files()
    pdf_task = process_pdf_files()
    jpg_task = process_jpg_files()
    zip_task = process_zip_files()

    [pptx_task, docx_task] >> pdf_task >> jpg_task >> zip_task
