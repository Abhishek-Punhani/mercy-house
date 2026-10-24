resource "google_compute_network" "mercy" {
  name                    = "${var.app_name}-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "mercy" {
  name          = "${var.app_name}-subnet"
  region        = var.region
  network       = google_compute_network.mercy.id
  ip_cidr_range = "10.191.0.0/24"
}

resource "google_compute_firewall" "web" {
  name          = "${var.app_name}-https"
  network       = google_compute_network.mercy.name
  target_tags   = ["${var.app_name}-web"]
  source_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }
}

resource "google_compute_firewall" "ssh" {
  name          = "${var.app_name}-admin-ssh"
  network       = google_compute_network.mercy.name
  target_tags   = ["${var.app_name}-web"]
  source_ranges = [var.admin_cidr]
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_address" "mercy" {
  name   = "${var.app_name}-ip"
  region = var.region
}

resource "google_service_account" "runtime" {
  account_id   = "${var.app_name}-runtime"
  display_name = "Mercy House host (no project IAM roles)"
}

resource "google_compute_instance" "mercy" {
  name         = "${var.app_name}-viewer"
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["${var.app_name}-web"]
  labels       = { app = var.app_name, managed_by = "terraform" }
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 30
      type  = "pd-ssd"
    }
  }
  network_interface {
    subnetwork = google_compute_subnetwork.mercy.id
    access_config {
      nat_ip = google_compute_address.mercy.address
    }
  }
  metadata = {
    ssh-keys               = "${var.ssh_user}:${trimspace(file(pathexpand(var.ssh_public_key_path)))}"
    enable-oslogin         = "FALSE"
    block-project-ssh-keys = "TRUE"
  }
  # This bootstrap contains packages and service-user setup only. Never
  # interpolate API keys, HTTP passwords or repository tokens into metadata.
  metadata_startup_script = file("${path.module}/../deploy/bootstrap.sh")
  service_account {
    email  = google_service_account.runtime.email
    scopes = []
  }
  shielded_instance_config {
    enable_secure_boot = true
  }
}

resource "cloudflare_record" "mercy" {
  zone_id         = var.cloudflare_zone_id
  name            = var.domain_name
  content         = google_compute_address.mercy.address
  type            = "A"
  ttl             = 300
  proxied         = false
  allow_overwrite = false
}
