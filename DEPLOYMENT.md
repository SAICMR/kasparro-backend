# Cloud Deployment Guide

This guide shows how to deploy the ETL system to AWS, GCP, or Azure.

## Table of Contents
1. [AWS Deployment](#aws-deployment)
2. [GCP Deployment](#gcp-deployment)
3. [Azure Deployment](#azure-deployment)

---

## AWS Deployment

### Step 1: Create RDS PostgreSQL Database

```bash
# Using AWS CLI
aws rds create-db-instance \
  --db-instance-identifier etl-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password YourStrongPassword \
  --allocated-storage 20 \
  --storage-type gp2 \
  --publicly-accessible
```

Save the endpoint: `etl-postgres.c9akciq32.us-east-1.rds.amazonaws.com`

### Step 2: Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name etl-app

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Build and push image
docker build -t 123456789.dkr.ecr.us-east-1.amazonaws.com/etl-app:latest .
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/etl-app:latest
```

### Step 3: Deploy with ECS Fargate

```bash
# Create task definition (save as task-definition.json)
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create ECS cluster
aws ecs create-cluster --cluster-name etl-cluster

# Create service
aws ecs create-service \
  --cluster etl-cluster \
  --service-name etl-api \
  --task-definition etl-app:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=etl-app,containerPort=8000
```

### Step 4: Setup CloudWatch Scheduled ETL

```bash
# Create IAM role for Lambda
aws iam create-role --role-name etl-lambda-role \
  --assume-role-policy-document file://trust-policy.json

# Create Lambda function for ETL trigger
aws lambda create-function \
  --function-name etl-trigger \
  --runtime python3.11 \
  --role arn:aws:iam::123456789:role/etl-lambda-role \
  --handler index.handler \
  --zip-file fileb://function.zip

# Create EventBridge schedule (cron: daily at 2 AM UTC)
aws events put-rule \
  --name etl-daily \
  --schedule-expression "cron(0 2 * * ? *)" \
  --state ENABLED

# Add Lambda as target
aws events put-targets \
  --rule etl-daily \
  --targets "Id"="1","Arn"="arn:aws:lambda:..."
```

### Step 5: Setup Application Load Balancer

```bash
# Create load balancer
aws elbv2 create-load-balancer \
  --name etl-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --scheme internet-facing \
  --type application

# Create target group
aws elbv2 create-target-group \
  --name etl-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --health-check-path /health

# Register targets
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=<container-id>
```

---

## GCP Deployment

### Step 1: Create Cloud SQL Instance

```bash
gcloud sql instances create etl-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --database-flags=cloudsql_iam_authentication=on
```

### Step 2: Create Cloud Run Service

```bash
# Build image with Cloud Build
gcloud builds submit --tag gcr.io/PROJECT_ID/etl-app

# Deploy to Cloud Run
gcloud run deploy etl-api \
  --image gcr.io/PROJECT_ID/etl-app \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=postgresql://... \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --timeout 3600s
```

### Step 3: Setup Cloud Scheduler

```bash
# Create daily ETL job (2 AM UTC)
gcloud scheduler jobs create http etl-daily \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri=https://etl-api-xxxxx.run.app/trigger-etl \
  --http-method=POST \
  --oidc-service-account-email=etl-runner@PROJECT_ID.iam.gserviceaccount.com
```

### Step 4: Monitor with Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --format json

# Create metric alert
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="ETL Failure Alert" \
  --condition-display-name="ETL Status Failed"
```

---

## Azure Deployment

### Step 1: Create Azure Database for PostgreSQL

```bash
az postgres server create \
  --resource-group etl-rg \
  --name etl-postgres \
  --location eastus \
  --admin-user postgres \
  --admin-password YourStrongPassword \
  --sku-name B_Gen5_1 \
  --storage-size 51200 \
  --public-network-access Enabled
```

### Step 2: Create Container Registry & Push Image

```bash
# Create registry
az acr create --resource-group etl-rg --name etlregistry --sku Basic

# Build image
az acr build --registry etlregistry --image etl-app:latest .

# Get login credentials
az acr credential show --name etlregistry
```

### Step 3: Deploy with App Service

```bash
# Create App Service Plan
az appservice plan create \
  --name etl-plan \
  --resource-group etl-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group etl-rg \
  --plan etl-plan \
  --name etl-api \
  --deployment-container-image-name etlregistry.azurecr.io/etl-app:latest

# Configure environment variables
az webapp config appsettings set \
  --resource-group etl-rg \
  --name etl-api \
  --settings DATABASE_URL=postgresql://... WEBSITES_PORT=8000
```

### Step 4: Setup Function Timer Trigger (ETL Scheduler)

```bash
# Create function app
az functionapp create \
  --resource-group etl-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name etl-trigger

# Deploy function code (creates timer trigger at 2 AM UTC)
# See function_app.py template below
```

**function_app.py:**
```python
import azure.functions as func
import requests

app = func.FunctionApp()

@app.function_name("ETLTrigger")
@app.schedule_trigger(schedule="0 0 2 * * *", arg_name="myTimer", run_on_startup=False)
def etl_trigger(myTimer: func.TimerRequest):
    """Trigger ETL daily at 2 AM UTC"""
    try:
        response = requests.post('https://etl-api.azurewebsites.net/trigger-etl')
        return f"ETL triggered: {response.status_code}"
    except Exception as e:
        return f"ETL trigger failed: {str(e)}"
```

### Step 5: Monitor with Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app etl-insights \
  --resource-group etl-rg \
  --application-type web

# Link to App Service
az webapp config set \
  --resource-group etl-rg \
  --name etl-api \
  --app-settings APPINSIGHTS_INSTRUMENTATIONKEY=<key>
```

---

## Common Environment Variables

Use these across all platforms:

```env
DATABASE_URL=postgresql://user:pass@host:5432/etl_db
API_KEY=your-api-key
ETL_INTERVAL=3600
LOG_LEVEL=INFO
API_HOST=http://jsonplaceholder.typicode.com
CSV_URL=https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv
```

---

## Monitoring & Alerts

### Key Metrics to Track
- ETL run duration
- ETL success/failure rate
- Records processed per run
- API response time
- Database connection pool usage
- API error rate

### AWS CloudWatch Example
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name etl-failure-alert \
  --metric-name ETLFailures \
  --namespace CustomETL \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --alarm-actions arn:aws:sns:us-east-1:...:alert-topic
```

---

## Logging & Observability

### View logs for each platform:

**AWS (CloudWatch):**
```bash
aws logs tail /ecs/etl-app --follow
```

**GCP (Cloud Logging):**
```bash
gcloud logging read --limit 50 --format=json
```

**Azure (Application Insights):**
```bash
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "traces | limit 50"
```

---

## Cost Estimation (Monthly)

| Service | AWS | GCP | Azure |
|---------|-----|-----|-------|
| Database (5GB) | $15 | $15 | $15 |
| Compute | $20 | $10 | $10 |
| Scheduler | <$1 | <$1 | $5 |
| Logging | <$1 | <$1 | <$1 |
| **Total** | **~$35** | **~$26** | **~$31** |

---

## Scaling Considerations

### Horizontal Scaling
- Cloud Run: Auto-scales with traffic
- ECS: Configure task auto-scaling
- App Service: Scale out plan

### Vertical Scaling
- Increase CPU/Memory
- Upgrade database tier
- Increase connection pool

### Database
- Read replicas for queries
- Connection pooling (PgBouncer)
- Query optimization

---

## Security Checklist

- [ ] Use managed database
- [ ] Enable encryption at rest
- [ ] Use VPC/Private networks
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Use secrets manager for API keys
- [ ] Enable HTTPS/TLS
- [ ] Rate limiting on API
- [ ] Authentication on sensitive endpoints

---

## Quick Deploy Commands

**One-liner for AWS:**
```bash
aws ecs create-service --cluster etl --service-name api --task-definition etl:1 --desired-count 1
```

**One-liner for GCP:**
```bash
gcloud run deploy etl-api --image gcr.io/PROJECT_ID/etl-app --region us-central1
```

**One-liner for Azure:**
```bash
az webapp create --resource-group etl --plan etl-plan --name etl-api
```

---

## Rollback Strategy

1. Keep previous image tags
2. Update load balancer to previous version
3. Monitor error rates
4. Scale down new version if needed
5. Investigate and fix issues
6. Retry deployment

---

## Support & Troubleshooting

- Check logs: `make logs` (or cloud provider logs)
- Test connectivity: `curl /health`
- Verify environment: `env | grep DATABASE`
- Database issues: Check connectivity limits
- Performance: Review CloudWatch/Cloud Monitoring metrics

