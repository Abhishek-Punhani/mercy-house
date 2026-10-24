output "instance_ip" {
  value = google_compute_address.mercy.address
}
output "instance_name" {
  value = google_compute_instance.mercy.name
}
output "domain_name" {
  value = var.domain_name
}
output "app_url" {
  value = "https://${var.domain_name}"
}
output "region" {
  value = var.region
}
output "zone" {
  value = var.zone
}
output "project_id" {
  value = var.project_id
}
