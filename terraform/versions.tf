terraform {
  required_version = ">= 1.5, < 2.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "8.5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "4.52.9"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
