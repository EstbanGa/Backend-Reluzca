.PHONY: build push deploy login create-repo all

AWS_REGION = us-east-1
AWS_ACCOUNT_ID = 139826822721
ECR_REPO = reluzca-api
LAMBDA_FUNCTION = reluzca-api
IMAGE_TAG = latest

# AWS credentials should be set via environment variables:
# export AWS_ACCESS_KEY_ID=your_key
# export AWS_SECRET_ACCESS_KEY=your_secret

ECR_URI = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
FULL_IMAGE = $(ECR_URI)/$(ECR_REPO):$(IMAGE_TAG)

login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_URI)

create-repo:
	aws ecr describe-repositories --repository-names $(ECR_REPO) --region $(AWS_REGION) || \
	aws ecr create-repository --repository-name $(ECR_REPO) --region $(AWS_REGION)

build:
	docker build -f Dockerfile.lambda -t $(ECR_REPO):$(IMAGE_TAG) .

tag: build
	docker tag $(ECR_REPO):$(IMAGE_TAG) $(FULL_IMAGE)

push: tag login
	docker push $(FULL_IMAGE)

deploy: push
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION) \
		--image-uri $(FULL_IMAGE) \
		--region $(AWS_REGION)

all: create-repo push deploy
