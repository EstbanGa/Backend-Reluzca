$ErrorActionPreference = "Continue"

# AWS credentials should be set via environment variables before running this script
# Set them using: source aws-creds.ps1 or manually:
# $env:AWS_ACCESS_KEY_ID = "your_key"
# $env:AWS_SECRET_ACCESS_KEY = "your_secret"
# $env:AWS_DEFAULT_REGION = "us-east-1"

$AWS_REGION = "us-east-1"
$AWS_ACCOUNT_ID = "139826822721"
$ECR_REPO = "reluzca-api"
$LAMBDA_FUNCTION = "reluzca-api"
$IMAGE_TAG = "latest"

$ECR_URI = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
$FULL_IMAGE = "$ECR_URI/${ECR_REPO}:${IMAGE_TAG}"

Write-Host "Creating IAM role if needed..." -ForegroundColor Cyan
aws iam get-role --role-name lambda-execution-role 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating IAM role..." -ForegroundColor Yellow
    aws iam create-role --role-name lambda-execution-role --assume-role-policy-document '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}'
    aws iam attach-role-policy --role-name lambda-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    aws iam attach-role-policy --role-name lambda-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
    Start-Sleep -Seconds 10
} else {
    Write-Host "Ensuring role has required policies..." -ForegroundColor Yellow
    aws iam attach-role-policy --role-name lambda-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>$null
    aws iam attach-role-policy --role-name lambda-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole 2>$null
}

$env:DOCKER_BUILDKIT = "0"

Write-Host "Building Docker image..." -ForegroundColor Cyan
docker build --platform linux/amd64 -f Dockerfile.lambda -t "${ECR_REPO}:${IMAGE_TAG}" .

Write-Host "Tagging image..." -ForegroundColor Cyan
docker tag "${ECR_REPO}:${IMAGE_TAG}" $FULL_IMAGE

Write-Host "Logging into ECR..." -ForegroundColor Cyan
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

Write-Host "Creating repository if needed..." -ForegroundColor Cyan
aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating ECR repository..." -ForegroundColor Yellow
    aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION
}

Write-Host "Pushing to ECR..." -ForegroundColor Cyan
docker push $FULL_IMAGE

Write-Host "Getting compatible image digest..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
$imageDigest = aws ecr describe-images --repository-name $ECR_REPO --image-ids imageTag=$IMAGE_TAG --region $AWS_REGION --query 'imageDetails[0].imageDigest' --output text
$IMAGE_URI_WITH_DIGEST = "${ECR_URI}/${ECR_REPO}@${imageDigest}"
Write-Host "Using image: $IMAGE_URI_WITH_DIGEST" -ForegroundColor Yellow

Write-Host "Creating/Updating Lambda function..." -ForegroundColor Cyan
aws lambda get-function --function-name $LAMBDA_FUNCTION --region $AWS_REGION 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Lambda function..." -ForegroundColor Yellow
    aws lambda create-function `
        --function-name $LAMBDA_FUNCTION `
        --package-type Image `
        --code ImageUri=$IMAGE_URI_WITH_DIGEST `
        --role "arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-execution-role" `
        --timeout 30 `
        --memory-size 512 `
        --region $AWS_REGION
} else {
    Write-Host "Updating Lambda function..." -ForegroundColor Yellow
    aws lambda update-function-code --function-name $LAMBDA_FUNCTION --image-uri $IMAGE_URI_WITH_DIGEST --region $AWS_REGION
}

Write-Host "Done!" -ForegroundColor Green
