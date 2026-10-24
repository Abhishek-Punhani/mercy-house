# Mercy House hosted deployment

Live address: **https://mercyhouse.abhi07.xyz**. The entire site, JSON API, replay streams and live-run controls require a browser login. The repository is private at **https://github.com/Abhishek-Punhani/mercy-house**.

The unique demo username and password are in the ignored local file `.deployment/access.json` (mode0600). Open that file locally to sign in; do not commit it or include its contents in slides or QR codes. The final presentation QR codes encode only the ordinary repository/demo URLs. Repository viewers need GitHub access separately.

## Infrastructure and separation

Terraform reused the GCP project, region, zone, machine type, provider credentials and Cloudflare zone from the existing reference environment at `/home/manav/dev_ws/N8N-Agent /terraform/.env` (the directory name contains a trailing space). Application-specific names and domain changed. It uses a separate Terraform directory/state and does not reference or modify n8n infrastructure.

Eight resources were created in project `rank-tracker-473910`: a dedicated VPC/subnet, HTTPS firewall, restricted SSH firewall, static IP, role-free runtime service account, Debian12 VM and new Cloudflare DNS A record. VM: `mercy-house-viewer`, `asia-south1-c`, `e2-medium`,30GBpd-ssd. DNS is unproxied so Caddy obtains and serves HTTPS directly without changing Cloudflare zone-wide SSL settings. The VM and disk remain provisioned until explicitly removed.

Caddy protects every route with a hashed BasicAuth password. Python listens only on127.0.0.1:8787 under systemd; no world, model-gateway, harness or workspace port is published. Live investigations still use the isolated four-container architecture. A trusted service user runs the viewer and Docker orchestration; authorized operators share the run library and one concurrent live slot. This is not an anonymous multi-tenant service.

The application key is copied separately over SSH to `/opt/mercy-house/.env`, owned by the service user with mode0600. It is absent from Terraform metadata, state variables, Git and the presentation. `LOCAL_UID=1100` aligns container log ownership with the host service user. `MERCY_PUBLIC_ORIGIN=https://mercyhouse.abhi07.xyz` enables strict hosted Host/Origin/CSRF checks. The configured key cannot be forwarded to another provider URL; a provider override needs an operator-supplied key.

## Reproduce or update

Configure `terraform/.env` from its example using provider/project values; never copy the n8n Terraform state or unrelated service secrets. GCP Application Default Credentials and the administrator SSH key are local prerequisites.

```bash
./deploy/terraform.sh init
./deploy/terraform.sh fmt -check
./deploy/terraform.sh validate
./deploy/terraform.sh plan
# Inspect the resource changes, then apply the intended dedicated Mercy plan.
./deploy/terraform.sh apply
python deploy/publish.py
python deploy/publish.py --checks-only
```

`deploy/publish.py` uploads a sanitized application archive and app/auth files over SSH, validates Caddy, then enables the systemd viewer. It refuses to redeploy while an investigation is active. Source manifests identify deployed file hashes and source commit; release snapshots exclude Git credentials, local logs and author documents. `.deployment/`, Terraform state, plans, real variable files and real environment files stay ignored. Preserve the protected local state for future infrastructure management.

The public bootstrap installs Docker Compose, Python and Caddy. Terraform credentials are never sent to the VM. `deploy/mercy-house.service` and `deploy/Caddyfile.template` are the reviewable runtime configuration; the template contains placeholders, not a password.

## Verified behavior

Terraform format/validation passed. The saved apply created8 resources with0 changes and0 deletions. A subsequent refreshed plan reports no changes.

HTTPS certificates validate through the system trust store. Anonymous requests receive401; authenticated UI/config requests succeed. Private paths return404, cross-origin writes403, invalid provider settings400 without creating a run, and replay SSE streams through Caddy. Viewer, Caddy and Docker services are active; port8787 binds only to loopback.

One hosted native-tool detective run with live character agents completed Lantern Room seed7: score1.0, no false or unsupported findings, and an actual submitted report. The graded investigation took87.72 seconds; initial build/start plus stream observation took114.108 seconds. This is one deployment smoke, not an estimate of general solving reliability. See DEPLOYMENT_RESULT.json. Model calls were made only for that authorized smoke; the infrastructure/HTTP checks make no generation requests.

The final remote release is synchronized after commits and rechecked without another generation run. GitHub main and the deployment source manifest identify the handoff versions; local source and remote runtime hashes are checked before reporting completion.
