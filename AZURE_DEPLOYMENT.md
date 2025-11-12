diff --git a/AZURE_DEPLOYMENT.md b/AZURE_DEPLOYMENT.md
new file mode 100644
index 0000000000000000000000000000000000000000..84cbd8bde000ab34bb9df36113f761c6b05623af
--- /dev/null
+++ b/AZURE_DEPLOYMENT.md
@@ -0,0 +1,244 @@
+# Docker & Azure Deployment Playbook
+
+This guide walks through deploying the Real-Estate Scraper to a local Docker environment first and then promoting the same container image to Azure Container Apps. Every step is written sequentially so you can copy/paste commands with the required settings.
+
+---
+
+## 1. Prerequisites
+
+| Requirement | Why it matters | How to check |
+|-------------|----------------|--------------|
+| Docker 24+ & Docker Compose V2 | Build/test containers locally | `docker --version`, `docker compose version` |
+| Azure CLI 2.53.0+ | Provision Azure resources | `az version` |
+| Azure CLI `containerapp` extension | Required for Container Apps commands | `az extension add --name containerapp` |
+| Azure subscription | Billing context for resources | `az account show` |
+| Git clone of this repo | Build context for Docker image | `git clone <repo>` |
+
+> **Tip:** Run `az login` before starting Azure-specific commands so the CLI has valid credentials.
+
+---
+
+## 2. Local Docker Deployment (Step-by-Step)
+
+1. **Create environment file**
+   ```bash
+   cat <<'EOF' > deployment/.env
+   FACEBOOK_EMAIL=
+   FACEBOOK_PASSWORD=
+   EOF
+   ```
+   Populate `deployment/.env` with the credentials the scrapers need:
+   ```dotenv
+   FACEBOOK_EMAIL=your_email@example.com
+   FACEBOOK_PASSWORD=super-secret
+   ```
+
+2. **Build the Docker image**
+   ```bash
+   docker build -f deployment/Dockerfile -t realestate-scraper:latest .
+   ```
+
+3. **Start with Docker Compose (recommended)**
+   ```bash
+   docker compose -f deployment/docker-compose.yml up -d
+   ```
+   * Exposes JupyterLab on `http://localhost:8888`
+   * Mounts the project directory for live code edits
+   * Loads variables from `deployment/.env`
+
+4. **Verify the container**
+   ```bash
+   docker compose ps
+   docker compose logs -f app
+   ```
+
+5. **Run a scraper task**
+   ```bash
+   docker compose exec app python run.py facebook_urls
+   ```
+
+6. **Stop the stack when finished**
+   ```bash
+   docker compose down
+   ```
+
+7. **Optional: Publish the image to a registry**
+   Tag and push the image if you use a centralized registry prior to Azure deployment.
+   ```bash
+   docker tag realestate-scraper:latest <registry>/realestate-scraper:latest
+   docker push <registry>/realestate-scraper:latest
+   ```
+
+---
+
+## 3. Azure Container Apps Deployment (Step-by-Step)
+
+### 3.1 Configure settings as environment variables
+
+Define all required values once so the deployment script and manual commands stay consistent.
+
+```bash
+export AZ_SUBSCRIPTION="<subscription-id>"
+export AZ_RESOURCE_GROUP="realestate-scraper-rg"
+export AZ_REGION="southeastasia"
+export AZ_ACR_NAME="<unique-acr-name>"
+export AZ_IMAGE_NAME="realestate-scraper:latest"
+export AZ_CONTAINERAPP_ENV="realestate-scraper-env"
+export AZ_CONTAINERAPP_NAME="realestate-scraper-app"
+export SCRAPER_FACEBOOK_EMAIL="your_email@example.com"
+export SCRAPER_FACEBOOK_PASSWORD="super-secret"
+```
+
+| Variable | Description |
+|----------|-------------|
+| `AZ_SUBSCRIPTION` | Subscription GUID or name that should own the resources |
+| `AZ_RESOURCE_GROUP` | Logical group for all deployment assets |
+| `AZ_REGION` | Azure region (e.g., `southeastasia`, `eastasia`, `eastus`) |
+| `AZ_ACR_NAME` | Globally unique name for Azure Container Registry (3-50 lowercase characters) |
+| `AZ_IMAGE_NAME` | Tag for the Docker image stored in ACR |
+| `AZ_CONTAINERAPP_ENV` | Container Apps managed environment name |
+| `AZ_CONTAINERAPP_NAME` | Name of the Container App exposed publicly |
+| `SCRAPER_FACEBOOK_EMAIL` | Value stored as secret in Container App |
+| `SCRAPER_FACEBOOK_PASSWORD` | Value stored as secret in Container App |
+
+### 3.2 Quick deploy with helper script
+
+From the repository root run:
+
+```bash
+./deployment/azure_cli_deploy.sh
+```
+
+The script performs the full provisioning flow:
+1. Selects your subscription and creates the resource group
+2. Creates Azure Container Registry (ACR) and builds the Docker image remotely via `az acr build`
+3. Registers `Microsoft.App` and `Microsoft.OperationalInsights` providers
+4. Ensures the Container Apps extension is installed
+5. Creates the Container Apps environment
+6. Deploys the container with external ingress on port `8888`
+
+### 3.3 Manual deployment commands (if you prefer explicit control)
+
+Run the following sequentially:
+
+```bash
+az account set --subscription "$AZ_SUBSCRIPTION"
+az group create --name "$AZ_RESOURCE_GROUP" --location "$AZ_REGION"
+az acr create --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --location "$AZ_REGION" --sku Basic --admin-enabled true
+az acr build --registry "$AZ_ACR_NAME" --image "$AZ_IMAGE_NAME" -f deployment/Dockerfile .
+```
+
+Retrieve registry credentials for the Container App:
+```bash
+LOGIN_SERVER=$(az acr show --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --query loginServer -o tsv)
+REGISTRY_USERNAME=$(az acr credential show --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --query username -o tsv)
+REGISTRY_PASSWORD=$(az acr credential show --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --query "passwords[0].value" -o tsv)
+```
+
+Provision the Container Apps environment and deploy:
+```bash
+az provider register --namespace Microsoft.App
+az provider register --namespace Microsoft.OperationalInsights
+az extension add --name containerapp --yes
+az containerapp env create --name "$AZ_CONTAINERAPP_ENV" --resource-group "$AZ_RESOURCE_GROUP" --location "$AZ_REGION"
+az containerapp create \
+  --name "$AZ_CONTAINERAPP_NAME" \
+  --resource-group "$AZ_RESOURCE_GROUP" \
+  --environment "$AZ_CONTAINERAPP_ENV" \
+  --image "$LOGIN_SERVER/$AZ_IMAGE_NAME" \
+  --target-port 8888 \
+  --ingress external \
+  --registry-server "$LOGIN_SERVER" \
+  --registry-username "$REGISTRY_USERNAME" \
+  --registry-password "$REGISTRY_PASSWORD"
+```
+
+### 3.4 Configure application secrets and environment variables
+
+Store sensitive values as Container App secrets and map them to environment variables:
+
+```bash
+az containerapp secret set \
+  --name "$AZ_CONTAINERAPP_NAME" \
+  --resource-group "$AZ_RESOURCE_GROUP" \
+  --secrets \
+    FACEBOOK_EMAIL="$SCRAPER_FACEBOOK_EMAIL" \
+    FACEBOOK_PASSWORD="$SCRAPER_FACEBOOK_PASSWORD"
+
+az containerapp update \
+  --name "$AZ_CONTAINERAPP_NAME" \
+  --resource-group "$AZ_RESOURCE_GROUP" \
+  --set-env-vars \
+    FACEBOOK_EMAIL=secretref:FACEBOOK_EMAIL \
+    FACEBOOK_PASSWORD=secretref:FACEBOOK_PASSWORD
+```
+
+Restart to apply the new configuration:
+```bash
+az containerapp restart --name "$AZ_CONTAINERAPP_NAME" --resource-group "$AZ_RESOURCE_GROUP"
+```
+
+### 3.5 Verify deployment and monitor
+
+* Get the public URL:
+  ```bash
+  az containerapp show \
+    --name "$AZ_CONTAINERAPP_NAME" \
+    --resource-group "$AZ_RESOURCE_GROUP" \
+    --query "properties.configuration.ingress.fqdn" -o tsv
+  ```
+* Tail live logs:
+  ```bash
+  az containerapp logs show \
+    --name "$AZ_CONTAINERAPP_NAME" \
+    --resource-group "$AZ_RESOURCE_GROUP" \
+    --follow true
+  ```
+* Scale settings (optional):
+  ```bash
+  az containerapp scale update \
+    --name "$AZ_CONTAINERAPP_NAME" \
+    --resource-group "$AZ_RESOURCE_GROUP" \
+    --min-replicas 1 \
+    --max-replicas 3
+  ```
+
+### 3.6 Update and redeploy image
+
+When the application changes:
+
+```bash
+az acr build --registry "$AZ_ACR_NAME" --image "$AZ_IMAGE_NAME" -f deployment/Dockerfile .
+az containerapp update \
+  --name "$AZ_CONTAINERAPP_NAME" \
+  --resource-group "$AZ_RESOURCE_GROUP" \
+  --image "$LOGIN_SERVER/$AZ_IMAGE_NAME"
+```
+
+---
+
+## 4. Clean up resources
+
+Remove Azure resources to avoid ongoing charges when testing is complete:
+```bash
+az group delete --name "$AZ_RESOURCE_GROUP" --yes --no-wait
+```
+
+Stop local Docker containers when they are no longer needed:
+```bash
+docker compose down
+```
+
+---
+
+## 5. Troubleshooting Checklist
+
+| Scenario | Resolution |
+|----------|------------|
+| Docker build fails on Chrome install | Ensure host has at least 4 GB free RAM and rerun `docker build` |
+| Cannot access Container App URL | Confirm ingress is set to `external` and the app reports healthy status via `az containerapp show` |
+| Container App fails to authenticate | Verify secrets exist with `az containerapp secret list` and that env vars use `secretref:` syntax |
+| Azure CLI command not found | Install or update the `containerapp` extension using `az extension add --name containerapp` |
+| Deployment stuck registering providers | Rerun `az provider register` and wait a few minutes; registration is asynchronous |
+
+With these steps you can move seamlessly from local Docker testing to a production-grade Azure Container Apps deployment.
