# Azure Container Deployment Guide

## Prerequisites
- Azure subscription ID
- Azure CLI 2.53.0 or later with `containerapp` extension available
- Logged in with `az login`
- Local clone of this repository

## Required Environment Variables
Set the following variables before running the deployment script:

```bash
export AZ_SUBSCRIPTION="<subscription-id>"
export AZ_RESOURCE_GROUP="<resource-group-name>"
export AZ_REGION="<azure-region>"
export AZ_ACR_NAME="<unique-acr-name>"
export AZ_IMAGE_NAME="realestate-scraper:latest"
export AZ_CONTAINERAPP_NAME="<container-app-name>"
export AZ_CONTAINERAPP_ENV="<container-app-environment>"
```

## Build and Deploy
Execute the automated deployment script from the project root:

```bash
./deployment/azure_cli_deploy.sh
```

The script performs the following actions:
1. Selects the target subscription and creates the resource group
2. Creates an Azure Container Registry and builds the Docker image via `az acr build`
3. Registers required providers and ensures the Container Apps extension is present
4. Creates a Container Apps environment and deploys the image with external ingress on port 8888

## Post-Deployment
Retrieve the application endpoint:

```bash
az containerapp show \
  --name "$AZ_CONTAINERAPP_NAME" \
  --resource-group "$AZ_RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv
```

Update environment variables or secrets with:

```bash
az containerapp secret set \
  --name "$AZ_CONTAINERAPP_NAME" \
  --resource-group "$AZ_RESOURCE_GROUP" \
  --secrets FACEBOOK_EMAIL="<email>" FACEBOOK_PASSWORD="<password>"
```

Restart the container to apply updated secrets:

```bash
az containerapp restart \
  --name "$AZ_CONTAINERAPP_NAME" \
  --resource-group "$AZ_RESOURCE_GROUP"
```
