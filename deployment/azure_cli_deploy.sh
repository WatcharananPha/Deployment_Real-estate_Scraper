diff --git a/deployment/azure_cli_deploy.sh b/deployment/azure_cli_deploy.sh
new file mode 100755
index 0000000000000000000000000000000000000000..c13cf137bb06bca0aead482813ccade2ad5a3424
--- /dev/null
+++ b/deployment/azure_cli_deploy.sh
@@ -0,0 +1,26 @@
+#!/usr/bin/env bash
+set -euo pipefail
+: "${AZ_SUBSCRIPTION:?}"
+: "${AZ_RESOURCE_GROUP:?}"
+: "${AZ_REGION:?}"
+: "${AZ_ACR_NAME:?}"
+: "${AZ_IMAGE_NAME:?}"
+: "${AZ_CONTAINERAPP_NAME:?}"
+: "${AZ_CONTAINERAPP_ENV:?}"
+: "${SCRAPER_FACEBOOK_EMAIL:?}"
+: "${SCRAPER_FACEBOOK_PASSWORD:?}"
+az account set --subscription "$AZ_SUBSCRIPTION"
+az group create --name "$AZ_RESOURCE_GROUP" --location "$AZ_REGION"
+az acr create --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --location "$AZ_REGION" --sku Basic --admin-enabled true
+az acr build --registry "$AZ_ACR_NAME" --image "$AZ_IMAGE_NAME" -f deployment/Dockerfile .
+LOGIN_SERVER=$(az acr show --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --query loginServer -o tsv)
+REGISTRY_USERNAME=$(az acr credential show --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --query username -o tsv)
+REGISTRY_PASSWORD=$(az acr credential show --name "$AZ_ACR_NAME" --resource-group "$AZ_RESOURCE_GROUP" --query "passwords[0].value" -o tsv)
+az provider register --namespace Microsoft.App
+az provider register --namespace Microsoft.OperationalInsights
+az extension add --name containerapp --yes
+az containerapp env create --name "$AZ_CONTAINERAPP_ENV" --resource-group "$AZ_RESOURCE_GROUP" --location "$AZ_REGION"
+az containerapp up --name "$AZ_CONTAINERAPP_NAME" --resource-group "$AZ_RESOURCE_GROUP" --environment "$AZ_CONTAINERAPP_ENV" --image "$LOGIN_SERVER/$AZ_IMAGE_NAME" --target-port 8888 --ingress external --registry-server "$LOGIN_SERVER" --registry-username "$REGISTRY_USERNAME" --registry-password "$REGISTRY_PASSWORD"
+az containerapp secret set --name "$AZ_CONTAINERAPP_NAME" --resource-group "$AZ_RESOURCE_GROUP" --secrets FACEBOOK_EMAIL="$SCRAPER_FACEBOOK_EMAIL" FACEBOOK_PASSWORD="$SCRAPER_FACEBOOK_PASSWORD"
+az containerapp update --name "$AZ_CONTAINERAPP_NAME" --resource-group "$AZ_RESOURCE_GROUP" --set-env-vars FACEBOOK_EMAIL=secretref:FACEBOOK_EMAIL FACEBOOK_PASSWORD=secretref:FACEBOOK_PASSWORD
+az containerapp restart --name "$AZ_CONTAINERAPP_NAME" --resource-group "$AZ_RESOURCE_GROUP"
