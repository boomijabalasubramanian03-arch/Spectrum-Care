$ErrorActionPreference = 'Stop'
Write-Host 'Building Chroma Context serverless stack...'
sam build --template-file cloud/template.yaml
Write-Host 'Deploying with AWS SAM...'
sam deploy --guided --template-file .aws-sam/build/template.yaml
