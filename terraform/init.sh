#!/usr/bin/env bash
#
# Idempotent Terraform init + import script for Quaks infrastructure.
# Initializes all modules and imports existing resources from the live environment.
#
# Usage:
#   TFVARS_FILE=/path/to/vars ./init.sh 
#
# Prerequisites: terraform, kubectl, curl, jq
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }
log_section() { echo -e "\n${CYAN}=== $* ===${NC}"; }

# ── Prerequisites ─────────────────────────────────────────────────────────────

check_prerequisites() {
  local missing=0
  for cmd in terraform kubectl curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
      log_error "Required command not found: $cmd"
      missing=1
    fi
  done

  if [[ ! -f "$TFVARS_FILE" ]]; then
    log_error "tfvars file not found: $TFVARS_FILE"
    log_error "Set TFVARS_FILE env var to the correct path."
    exit 1
  fi

  if [[ $missing -eq 1 ]]; then
    exit 1
  fi
}

# ── Helpers ───────────────────────────────────────────────────────────────────

# Parse a scalar variable value from the tfvars file
parse_tfvar() {
  local var_name="$1"
  local line
  line=$(grep -E "^\s*${var_name}\s*=" "$TFVARS_FILE" | head -1) || true
  if [[ -z "$line" ]]; then
    return 0
  fi
  # Extract value between quotes: var = "value"
  echo "$line" | sed -n 's/^[^=]*=[[:space:]]*"\([^"]*\)".*/\1/p'
}

# Import a resource if not already in state
tf_import() {
  local resource_addr="$1"
  local resource_id="$2"

  if terraform state list 2>/dev/null | grep -qF "$resource_addr"; then
    log_info "  Already in state: $resource_addr"
    return 0
  fi

  log_info "  Importing: $resource_addr -> $resource_id"
  if terraform import -var-file="$TFVARS_FILE" -compact-warnings "$resource_addr" "$resource_id" 2>&1; then
    log_info "  Imported: $resource_addr"
  else
    log_warn "  Failed to import: $resource_addr (will be reconciled on next apply)"
  fi
}

# Initialize a terraform module directory
tf_init_module() {
  local module_dir="$1"
  log_section "$(basename "$module_dir")"
  cd "$module_dir"

  log_info "Running terraform init..."
  terraform init -input=false
}

# ── Module 01: Elasticsearch ─────────────────────────────────────────────────

init_01_elasticsearch() {
  local module_dir="$SCRIPT_DIR/01_elasticsearch"

  # This module uses username/password auth — unset env vars that conflict
  # (the elasticstack provider auto-reads ELASTICSEARCH_API_KEY from the env)
  local saved_es_api_key="${ELASTICSEARCH_API_KEY:-}"
  local saved_es_url="${ELASTICSEARCH_URL:-}"
  unset ELASTICSEARCH_API_KEY ELASTICSEARCH_URL

  # Clean existing state as requested
  log_info "Cleaning existing state for 01_elasticsearch..."
  rm -rf "$module_dir/.terraform" "$module_dir/.terraform.lock.hcl"
  rm -f "$module_dir/terraform.tfstate" "$module_dir/terraform.tfstate.backup"

  tf_init_module "$module_dir"

  # Get ES credentials and cluster UUID via kubectl + REST API
  local es_password
  es_password=$(kubectl get secret elasticsearch-es-elastic-user -n elastic -o jsonpath='{.data.elastic}' | base64 -d)
  local es_url
  es_url=$(parse_tfvar "es_url")

  log_info "  Looking up ES cluster UUID..."
  local cluster_uuid
  cluster_uuid=$(curl -sf -u "elastic:${es_password}" "${es_url}" | jq -r '.cluster_uuid')
  log_info "  ES cluster UUID: ${cluster_uuid}"

  # Import index lifecycle policy
  tf_import "elasticstack_elasticsearch_index_lifecycle.quaks_policy" "${cluster_uuid}/quaks_policy"
  tf_import "elasticstack_elasticsearch_index_lifecycle.quaks_ephemeral_policy" "${cluster_uuid}/quaks_ephemeral_policy"

  # Import index templates
  local templates=(
    "quaks_markets-news_template"
    "quaks_stocks-eod_template"
    "quaks_stocks-insider-trades_template"
    "quaks_stocks-metadata_template"
    "quaks_stocks-fundamental-income-statement_template"
    "quaks_stocks-fundamental-balance-sheet_template"
    "quaks_stocks-fundamental-cash-flow_template"
    "quaks_stocks-fundamental-estimated-earnings_template"
    "quaks_insights-news_template"
    "quaks_insights-finance_template"
    "quaks_waiting-list_template"
    "quaks_published-content_template"
  )
  for tpl in "${templates[@]}"; do
    tf_import "elasticstack_elasticsearch_index_template.${tpl}" "${cluster_uuid}/${tpl}"
  done

  # Import indices (tf_resource_name:es_index_name pairs)
  local index_pairs=(
    "stocks_eod_nyse:quaks_stocks-eod_nyse"
    "stocks_eod_nasdaq:quaks_stocks-eod_nasdaq"
    "stocks_eod_amex:quaks_stocks-eod_amex"
    "markets_news_nyse:quaks_markets-news_nyse"
    "markets_news_nasdaq:quaks_markets-news_nasdaq"
    "markets_news_amex:quaks_markets-news_amex"
    "stocks_metadata_nyse:quaks_stocks-metadata_nyse"
    "stocks_metadata_nasdaq:quaks_stocks-metadata_nasdaq"
    "stocks_metadata_amex:quaks_stocks-metadata_amex"
    "insights_news:quaks_insights-news"
    "insights_finance:quaks_insights-finance"
    "waiting_list_initial:quaks_waiting-list_initial"
    "published_content_initial:quaks_published-content_initial"
  )
  for pair in "${index_pairs[@]}"; do
    local tf_name="${pair%%:*}"
    local es_name="${pair#*:}"
    tf_import "elasticstack_elasticsearch_index.${tf_name}" "${cluster_uuid}/${es_name}"
  done

  # Import search templates (for_each resources)
  local search_templates=(
    "get_eod_ohlcv_template"
    "get_eod_indicator_ad_template"
    "get_eod_indicator_adx_template"
    "get_eod_indicator_cci_template"
    "get_eod_indicator_ema_template"
    "get_eod_indicator_macd_template"
    "get_eod_indicator_obv_template"
    "get_eod_indicator_rsi_template"
    "get_eod_indicator_stoch_template"
    "get_markets_news_template"
    "get_stats_close_template"
    "get_stats_close_bulk_template"
    "get_metadata_market_caps_template"
    "get_metadata_profile_template"
    "get_insights_news_template"
    "get_waiting_list_unprocessed_template"
    "get_published_content_unprocessed_template"
  )
  for st in "${search_templates[@]}"; do
    tf_import "elasticstack_elasticsearch_script.search_templates[\"${st}\"]" "${cluster_uuid}/${st}"
  done

  # Import ES API key (lookup internal ID via ES REST API)
  log_info "  Looking up ES API key ID..."
  local api_key_id
  api_key_id=$(curl -sf -u "elastic:${es_password}" "${es_url}/_security/api_key?name=quaks-api-key" | jq -r '.api_keys[0].id // empty')
  if [[ -n "$api_key_id" ]]; then
    tf_import "elasticstack_elasticsearch_security_api_key.quaks_api_key" "${cluster_uuid}/${api_key_id}"
    log_warn "  ES API key 'encoded' field is write-only and will be empty after import."
    log_warn "  Run: terraform taint elasticstack_elasticsearch_security_api_key.quaks_api_key"
    log_warn "  Then: terraform apply -var-file=$TFVARS_FILE"
    log_warn "  This recreates the API key and updates the k8s secret."
  else
    log_warn "  ES API key 'quaks-api-key' not found. It will be created on next apply."
  fi

  # Import k8s secret
  tf_import "kubernetes_secret_v1.quaks_elastic_api_secret" "quaks/quaks-elastic-api-secret"

  # Restore env vars for modules that need them (e.g. 06_kibana uses api_key)
  if [[ -n "$saved_es_api_key" ]]; then export ELASTICSEARCH_API_KEY="$saved_es_api_key"; fi
  if [[ -n "$saved_es_url" ]]; then export ELASTICSEARCH_URL="$saved_es_url"; fi
}

# ── Module 02: Airflow Instance ──────────────────────────────────────────────

init_02_airflow() {
  tf_init_module "$SCRIPT_DIR/02_airflow-instance"

  local ns
  ns=$(parse_tfvar "airflow_namespace")
  ns="${ns:-airflow}"

  tf_import "kubernetes_namespace_v1.airflow"           "$ns"
  tf_import "helm_release.pg_quaks-dags"                "${ns}/pg-quaks-dags"
  tf_import "helm_release.redis_quaks_dags"             "${ns}/redis-quaks-dags"
  tf_import "kubernetes_secret_v1.quaks_dags_secrets"   "${ns}/quaks-dags-secrets"
  tf_import "helm_release.airflow"                      "${ns}/quaks-airflow"

  # time_sleep resources are not importable — next apply creates them (no-op delay)
  log_info "  Skipping time_sleep resources (not importable, harmless on next apply)"
}

# ── Module 03: Quaks Auth Realm ──────────────────────────────────────────────

init_03_auth_realm() {
  tf_init_module "$SCRIPT_DIR/03_quaks-auth-realm"

  local quaks_ns
  quaks_ns=$(parse_tfvar "quaks_namespace")
  quaks_ns="${quaks_ns:-quaks}"

  # Import realm (import ID is the realm name)
  tf_import "keycloak_realm.quaks" "quaks"

  # Look up Keycloak UUIDs via REST API
  local auth_url auth_user auth_pass
  auth_url=$(parse_tfvar "auth_url")
  auth_user=$(parse_tfvar "auth_admin_username")
  auth_pass=$(parse_tfvar "auth_admin_secret")

  log_info "  Obtaining Keycloak admin token..."
  local token
  token=$(curl -sf -X POST "${auth_url}/realms/master/protocol/openid-connect/token" \
    -d "client_id=admin-cli" \
    -d "username=${auth_user}" \
    -d "password=${auth_pass}" \
    -d "grant_type=password" | jq -r '.access_token // empty')

  if [[ -z "$token" ]]; then
    log_warn "  Could not obtain Keycloak token. Skipping keycloak resource imports."
    log_warn "  You will need to import these manually."
  else
    # Look up client UUID by client_id
    local auth_client_id
    auth_client_id=$(parse_tfvar "auth_client_id")
    auth_client_id="${auth_client_id:-quaks-client}"

    local client_uuid
    client_uuid=$(curl -sf -H "Authorization: Bearer $token" \
      "${auth_url}/admin/realms/quaks/clients?clientId=${auth_client_id}" | jq -r '.[0].id // empty')

    if [[ -n "$client_uuid" ]]; then
      tf_import "keycloak_openid_client.quaks_client" "quaks/${client_uuid}"

      # Look up service account user ID (the client's service account)
      local sa_user_id
      sa_user_id=$(curl -sf -H "Authorization: Bearer $token" \
        "${auth_url}/admin/realms/quaks/clients/${client_uuid}/service-account-user" | jq -r '.id // empty')

      # Look up realm-management client UUID
      local rm_client_uuid
      rm_client_uuid=$(curl -sf -H "Authorization: Bearer $token" \
        "${auth_url}/admin/realms/quaks/clients?clientId=realm-management" | jq -r '.[0].id // empty')

      if [[ -n "$sa_user_id" && -n "$rm_client_uuid" ]]; then
        # Look up manage-users role UUID — import requires the UUID, not the name
        local role_uuid
        role_uuid=$(curl -sf -H "Authorization: Bearer $token" \
          "${auth_url}/admin/realms/quaks/clients/${rm_client_uuid}/roles/manage-users" | jq -r '.id // empty')

        if [[ -n "$role_uuid" ]]; then
          tf_import "keycloak_openid_client_service_account_role.quaks_manage_users" \
            "quaks/${sa_user_id}/${rm_client_uuid}/${role_uuid}"
        else
          log_warn "  Could not find manage-users role UUID. Skipping service account role import."
        fi
      fi
    else
      log_warn "  Could not find client '${auth_client_id}'. Skipping client imports."
    fi

    # Look up service account user UUID
    local sa_username
    sa_username=$(parse_tfvar "auth_service_account_username")
    sa_username="${sa_username:-quaks-service-account}"

    local user_uuid
    user_uuid=$(curl -sf -H "Authorization: Bearer $token" \
      "${auth_url}/admin/realms/quaks/users?username=${sa_username}&exact=true" | jq -r '.[0].id // empty')

    if [[ -n "$user_uuid" ]]; then
      tf_import "keycloak_user.service_account" "quaks/${user_uuid}"
    else
      log_warn "  Could not find user '${sa_username}'. Skipping user import."
    fi
  fi

  # Import k8s secret
  tf_import "kubernetes_secret_v1.quaks_auth" "${quaks_ns}/quaks-auth"
}

# ── Module 04: Quaks Dependencies ────────────────────────────────────────────

init_04_dependencies() {
  tf_init_module "$SCRIPT_DIR/04_quaks-dependencies"

  local quaks_ns
  quaks_ns=$(parse_tfvar "quaks_namespace")
  quaks_ns="${quaks_ns:-quaks}"

  tf_import "helm_release.pg_quaks-app"          "${quaks_ns}/pg-quaks-app"
  tf_import "helm_release.pg_quaks-vectors"       "${quaks_ns}/pg-quaks-vectors"
  tf_import "helm_release.pg_quaks-checkpoints"   "${quaks_ns}/pg-quaks-checkpoints"
  tf_import "helm_release.redis_quaks"            "${quaks_ns}/redis-quaks"
  tf_import "kubernetes_secret_v1.quaks_secret"   "${quaks_ns}/quaks-secret"

  # Vault resources
  local vault_engine_path
  vault_engine_path=$(parse_tfvar "vault_engine_path")
  vault_engine_path="${vault_engine_path:-quaks_engine}"

  local vault_secret_path
  vault_secret_path=$(parse_tfvar "vault_secret_path")
  vault_secret_path="${vault_secret_path:-app_secrets}"

  tf_import "vault_mount.kv" "$vault_engine_path"
  tf_import "vault_kv_secret_v2.app_secrets" "${vault_engine_path}/data/${vault_secret_path}"

  # time_sleep resources are not importable
  log_info "  Skipping time_sleep resources (not importable, harmless on next apply)"
}

# ── Module 05: Quaks Instance ────────────────────────────────────────────────

init_05_quaks_instance() {
  tf_init_module "$SCRIPT_DIR/05_quaks-instance"

  local quaks_ns
  quaks_ns=$(parse_tfvar "quaks_namespace")
  quaks_ns="${quaks_ns:-quaks}"

  tf_import "helm_release.quaks" "${quaks_ns}/quaks"
}

# ── Module 06: Kibana ────────────────────────────────────────────────────────

init_06_kibana() {
  tf_init_module "$SCRIPT_DIR/06_kibana"

  local quaks_ns
  quaks_ns=$(parse_tfvar "quaks_namespace")
  quaks_ns="${quaks_ns:-quaks}"

  tf_import "helm_release.kibana" "${quaks_ns}/kibana"

  # Elasticsearch security resources — need cluster UUID prefix
  local es_password
  es_password=$(kubectl get secret elasticsearch-es-elastic-user -n elastic -o jsonpath='{.data.elastic}' | base64 -d)
  local es_url
  es_url=$(parse_tfvar "es_url")
  local cluster_uuid
  cluster_uuid=$(curl -sf -u "elastic:${es_password}" "${es_url}" | jq -r '.cluster_uuid')

  local kb_anonymous_username
  kb_anonymous_username=$(parse_tfvar "kb_anonymous_username")

  tf_import "elasticstack_elasticsearch_security_role.anonymous_dashboard_role" "${cluster_uuid}/anonymous_dashboard_role"

  if [[ -n "$kb_anonymous_username" ]]; then
    tf_import "elasticstack_elasticsearch_security_user.anonymous_user" "${cluster_uuid}/${kb_anonymous_username}"
  else
    log_warn "  Could not determine kb_anonymous_username. Skipping user import."
  fi

  # kibana_import_saved_objects resources don't support import — next apply re-imports them
  log_info "  Skipping kibana_import_saved_objects resources (not importable, re-applied on next apply)"
}

# ── Plan verification ────────────────────────────────────────────────────────

verify_module() {
  local module_dir="$1"
  local module_name
  module_name=$(basename "$module_dir")

  cd "$module_dir"
  log_info "Verifying ${module_name}..."

  # 01_elasticsearch uses username/password — env var ELASTICSEARCH_API_KEY conflicts
  local restore_api_key=""
  if [[ "$module_name" == "01_elasticsearch" && -n "${ELASTICSEARCH_API_KEY:-}" ]]; then
    restore_api_key="$ELASTICSEARCH_API_KEY"
    unset ELASTICSEARCH_API_KEY ELASTICSEARCH_URL
  fi

  if terraform plan -var-file="$TFVARS_FILE" -compact-warnings -detailed-exitcode -input=false >/dev/null 2>&1; then
    log_info "  ${module_name}: State is in sync (no changes)"
  else
    log_warn "  ${module_name}: Drift detected — review with: cd ${module_dir} && terraform plan -var-file=${TFVARS_FILE}"
  fi

  if [[ -n "$restore_api_key" ]]; then export ELASTICSEARCH_API_KEY="$restore_api_key"; fi
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
  log_section "Checking prerequisites"
  check_prerequisites

  log_info "Using tfvars: $TFVARS_FILE"

  init_01_elasticsearch
  init_02_airflow
  init_03_auth_realm
  init_04_dependencies
  init_05_quaks_instance
  init_06_kibana

  log_section "Verification"
  for module_dir in "$SCRIPT_DIR"/0*; do
    verify_module "$module_dir"
  done

  log_section "Done"
  log_info "All modules initialized."
  log_info "For modules with drift, run: terraform apply -var-file=$TFVARS_FILE"
  log_warn "Note: time_sleep and kibana_import_saved_objects resources will be"
  log_warn "created/re-applied on the first 'terraform apply' per module."
}

main "$@"
