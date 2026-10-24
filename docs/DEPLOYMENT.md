# Public demo deployment

Live site: **https://mercyhouse.abhi07.xyz**. It opens without a username or password. The source is public at **https://github.com/Abhishek-Punhani/mercy-house**.

Recorded investigations are available without an account or API key. To start a new live case, enter your own key for the provider shown in the form. That key powers the detective and characters for that run. The viewer does not save it in browser storage or application files. The public host stores no team API key. This website mode is separate from the official judging configuration, where character credentials remain separately configured.

## Infrastructure

Terraform reused the existing GCP project, region, zone, machine type and Cloudflare credentials from `/home/manav/dev_ws/N8N-Agent /terraform/.env` (the directory name contains a trailing space). App-specific names and the domain changed. State is separate; the n8n resources and state were not modified.

Eight dedicated resources were created: VPC, subnet, web firewall, restricted SSH firewall, static IP, a service account without project roles, Debian12 VM and Cloudflare DNS record. VM: `mercy-house-viewer`, project `rank-tracker-473910`, zone `asia-south1-c`, type `e2-medium`,30GBpd-ssd. Caddy serves HTTPS directly using the unproxied DNS record. The VM/disk remain provisioned until explicitly removed.

The Python viewer binds only to127.0.0.1:8787 under systemd. Caddy forwards the public HTTPS site without an authentication challenge. Firewall ingress is80/443, with SSH restricted to the administrator’s IPv4/32. No world, gateway, controller or detective-workspace port is published.

## Public live-run controls

`MERCY_PUBLIC_ORIGIN=https://mercyhouse.abhi07.xyz` restricts the Host and browser Origin. `MERCY_PUBLIC_DEMO=1` requires a visitor key, refuses server-key use and restricts calls to the configured provider URL. The browser explains that this key powers both model roles for the public demonstration. The original local/judging mode still separates detective and character credentials.

Only one live run executes at a time. The creator receives a random control token held in browser memory; stopping that run requires the token. It is absent from shared replay responses and saved metadata. Recorded public actions and dialogue remain viewable by other visitors. Private world files, raw private model context and credentials are not served.

The service user has trusted Docker orchestration authority. Detective containers retain the documented separation and do not have a Docker socket or host secrets. This is a public demonstration with a shared run library, not private visitor accounts or a multi-tenant investigation service.

## Reproduce or update

Configure `terraform/.env` from its example. Keep GCP Application Default Credentials and the administrator SSH key local; never copy the n8n Terraform state.

```bash
./deploy/terraform.sh init
./deploy/terraform.sh fmt -check
./deploy/terraform.sh validate
./deploy/terraform.sh plan
# Inspect the dedicated Mercy changes before applying.
./deploy/terraform.sh apply
python deploy/publish.py
python deploy/publish.py --checks-only
```

`deploy/publish.py` uploads a sanitized archive over SSH, writes only public model/provider settings to the remote app environment, validates Caddy and starts the service. It refuses to interrupt an active investigation. The release manifest records commit and runtime hashes. Local `.env`, `.deployment/`, Terraform state, plans and real variable files stay ignored. Preserve the protected local state for future management.

The previous HTTP login was removed at the user’s request. Old local `.deployment/access.json` is obsolete and is not needed to use the site. No password or API key appears in either presentation QR code.

## Verification

Terraform format and validation passed; eight resources were created, with no changes or deletions to existing resources. A later plan reports no changes. HTTPS certificates validate through the system trust store. Anonymous homepage/config/replay requests return200 with no login challenge. Private paths return404, cross-origin writes403 and missing visitor keys/server-key requests/wrong providers400 without creating runs. Replay events stream through Caddy.

A hosted native detective test completed Lantern Room seed7 with score1.0 before the public-access change. The separate public visitor-key test also scored1.0 with no false or unsupported findings; its graded investigation took46.048 seconds. Current public HTTP checks and both test records are in DEPLOYMENT_RESULT.json. These are bounded deployment checks, not a general solving estimate. No scores from historical runs were changed when site access changed.
