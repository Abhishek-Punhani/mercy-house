variable "project_id" {
  description = "Existing GCP billing project; reused without changing its resources."
  type        = string
}
variable "region" {
  type    = string
  default = "asia-south1"
}
variable "zone" {
  type    = string
  default = "asia-south1-c"
}
variable "machine_type" {
  type    = string
  default = "e2-medium"
}
variable "app_name" {
  type    = string
  default = "mercy-house"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,35}$", var.app_name))
    error_message = "Use a short GCP-compatible dedicated resource prefix."
  }
}
variable "domain_name" {
  type    = string
  default = "mercyhouse.abhi07.xyz"
  validation {
    condition     = can(regex("^[a-z0-9.-]+$", var.domain_name))
    error_message = "Supply a plain DNS name without scheme, spaces, or paths."
  }
}
variable "ssh_user" {
  type    = string
  default = "manav"
  validation {
    condition     = can(regex("^[a-z_][a-z0-9_-]*$", var.ssh_user))
    error_message = "Supply a Linux login name."
  }
}
variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/google_compute_engine.pub"
}
variable "admin_cidr" {
  description = "Administrator public IPv4 /32; SSH is not public to the world."
  type        = string
  validation {
    condition     = can(cidrhost(var.admin_cidr, 0)) && endswith(var.admin_cidr, "/32")
    error_message = "SSH access must be restricted to one administrator IPv4 /32."
  }
}
variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}
variable "cloudflare_zone_id" {
  type = string
}
