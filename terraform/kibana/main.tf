
# Run before apply:
# terraform import kubectl_manifest.kibana "kibana.k8s.elastic.co/v1//Kibana//kibana//default"
#
# Access with:
# https://<kibana_fqdn>/app/dashboards?auth_provider_hint=anonymous1#/view/<dashboard>

terraform {
  required_providers {
    elasticstack = {
      source  = "elastic/elasticstack"
      version = "~> 0.12"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.14.0"
    }
  }
}

provider "elasticstack" {
  elasticsearch {
    endpoints = [var.es_url]
    api_key   = var.es_api_key
  }

  kibana {
    endpoints = [var.kb_url]
    api_key   = var.es_api_key
  }
}

provider "kubectl" {
  config_path = "~/.kube/config"
}

resource "kubectl_manifest" "kibana" {
  yaml_body = yamlencode({
    apiVersion = "kibana.k8s.elastic.co/v1"
    kind       = "Kibana"

    metadata = {
      name      = "kibana"
      namespace = "default"
    }

    spec = {
      version = "9.1.0"

      count = 1

      elasticsearchRef = {
        name = "elasticsearch"
      }

      config = {
        "xpack.security.authc.providers.basic.basic1.order"           = 0
        "xpack.security.authc.providers.basic.basic1.icon"            = "logoElasticsearch"
        "xpack.security.authc.providers.basic.basic1.hint"            = "Typically for end users"
        "xpack.security.authc.providers.anonymous.anonymous1.order"   = 1
        "xpack.security.authc.providers.anonymous.anonymous1.credentials.username" = var.kb_anonymous_username
        "xpack.security.authc.providers.anonymous.anonymous1.credentials.password" = var.kb_anonymous_password
        "xpack.security.authc.providers.anonymous.anonymous1.showInSelector" = false
        "xpack.security.sameSiteCookies" = "None"
      }
    }
  })
}

resource "elasticstack_elasticsearch_security_role" "anonymous_dashboard_role" {
  name = "anonymous_dashboard_role"

  indices {
    names      = ["*"]
    privileges = ["read", "view_index_metadata"]
  }

  applications {
    application = "kibana-.kibana"
    privileges  = ["feature_dashboard.read"]
    resources   = ["*"]
  }

  depends_on = [kubectl_manifest.kibana]

}

resource "elasticstack_elasticsearch_security_user" "anonymous_user" {
  username = var.kb_anonymous_username
  password = var.kb_anonymous_password
  roles    = [elasticstack_elasticsearch_security_role.anonymous_dashboard_role.name]

  depends_on = [elasticstack_elasticsearch_security_role.anonymous_dashboard_role]
}

data "local_file" "stocks_eod_data_view_ndjson" {
  filename = "${path.module}/stocks_eod_data_view.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "data_view" {
  file_contents = data.local_file.stocks_eod_data_view_ndjson.content
  space_id  = "default"
  overwrite = true
}

data "local_file" "stocks_eod_visualizations_ndjson" {
  filename = "${path.module}/stocks_eod_visualizations.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "visualizations" {
  file_contents = data.local_file.stocks_eod_visualizations_ndjson.content
  space_id  = "default"
  overwrite = true
}

data "local_file" "stocks_eod_dashboard_ndjson" {
  filename = "${path.module}/stocks_eod_dashboard.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "dashboard" {
  file_contents = data.local_file.stocks_eod_dashboard_ndjson.content
  space_id  = "default"
  overwrite = true
}
