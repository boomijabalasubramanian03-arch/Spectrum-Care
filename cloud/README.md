# AWS Serverless Deployment

This folder is the cloud deployment layer for **Serverless Cloud Assistant for Contextual Color Analysis and Accessibility Support**.

## Architecture

React -> API Gateway HTTP API -> Lambda
                         |          |
                         |          +-> DynamoDB (analysis/history)
                         |          +-> Amazon Polly (voice)
                         v
                       S3 presigned upload
                         |
                    S3 ObjectCreated
                         v
                       Lambda -> YOLOv4-tiny + OpenCV + OCR -> S3/DynamoDB

The Lambda reuses `backend/app/ml` so the local and cloud analysis logic stay aligned.

## Current cloud MVP

Implemented as code:
- S3 image bucket
- S3 upload trigger
- DynamoDB analysis table
- API Gateway HTTP API
- Lambda API routes: `/health`, `/upload-url`, `/analysis/{id}`, `/speak`
- Amazon Polly voice endpoint
- Shared YOLOv4-tiny + OpenCV colour pipeline

## Important

The cloud stack is **not deployed automatically**. AWS account credentials and AWS SAM/Docker are required for deployment. Keep the local FastAPI/SQLite mode as the development fallback until the cloud stack is verified.

### Deployment prerequisites

1. AWS account
2. AWS CLI configured (`aws configure`)
3. AWS SAM CLI
4. Docker Desktop running

From the project root:

```powershell
sam build --template-file cloud/template.yaml
sam deploy --guided --template-file .aws-sam/build/template.yaml
```

Do not commit AWS access keys to the project.
