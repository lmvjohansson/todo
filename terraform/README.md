# Terraform — Infrastructure as Code
 
This directory contains the complete Terraform configuration for the thesis project infrastructure on AWS ECS Fargate (eu-north-1).
 
## Prerequisites
 
- [Terraform](https://developer.hashicorp.com/terraform/install) installed
- AWS CLI configured with SSO profile: `aws login --profile knightec`
 
---
 
## File Structure
 
| File | Description |
|------|-------------|
| `main.tf` | AWS provider configuration |
| `variables.tf` | Input variables (region, RDS endpoint, database name, secret name) |
| `networking.tf` | VPC/subnet data sources, security groups and rules |
| `ecr.tf` | ECR repositories for backend and frontend images |
| `alb.tf` | Application Load Balancers, target groups, listeners |
| `ecs.tf` | ECS cluster, task definitions, services |
| `outputs.tf` | ALB DNS names printed after apply |
 
---
 
## Important Notes
 
The following resources have `prevent_destroy = true` and will **never** be deleted by Terraform:
 
- `aws_ecr_repository.todo_backend` — preserves Docker images between experiments
- `aws_ecr_repository.todo_frontend` — preserves Docker images between experiments
- `aws_security_group.rds_sg` — attached to RDS instance, cannot be detached
 
The RDS instance itself is **not managed by Terraform**. It is referenced as input variables only.
 
---
 
## Common Commands
 
### Authenticate to AWS
```bash
aws login --profile knightec
```
 
### Initialize Terraform (first time only)
```bash
terraform init
```
 
### Preview changes
```bash
terraform plan
```
 
### Apply infrastructure
```bash
terraform apply
```
 
### Destroy infrastructure (excludes ECR and RDS resources)
```bash
terraform destroy -target=aws_ecs_service.todo_backend_service -target=aws_ecs_service.todo_frontend_service -target=aws_ecs_cluster.todo_cluster -target=aws_lb.todo_backend_alb -target=aws_lb.todo_frontend_alb -target=aws_security_group.backend_alb -target=aws_security_group.backend_ecs -target=aws_security_group.frontend_alb -target=aws_security_group.frontend_ecs
```
 
---
 
## Docker Image Management
 
### Authenticate Docker to ECR
```bash
aws ecr get-login-password --region eu-north-1 --profile knightec | docker login --username AWS --password-stdin 600889066998.dkr.ecr.eu-north-1.amazonaws.com
```
 
### Build and push backend
```bash
docker build -t todo-backend ./backend
docker tag todo-backend:latest 600889066998.dkr.ecr.eu-north-1.amazonaws.com/todo-backend:latest
docker push 600889066998.dkr.ecr.eu-north-1.amazonaws.com/todo-backend:latest
```
 
### Build and push frontend
```bash
docker build -t todo-frontend ./frontend
docker tag todo-frontend:latest 600889066998.dkr.ecr.eu-north-1.amazonaws.com/todo-frontend:latest
docker push 600889066998.dkr.ecr.eu-north-1.amazonaws.com/todo-frontend:latest
```
 
> **Note:** Images only need to be pushed after the first `terraform apply`, or if application code changes. The ECR repositories persist across destroy/apply cycles.
 
---
 
## ECS Service Management
 
### Force new deployment (after pushing new images)
```bash
aws ecs update-service --cluster todo-cluster --service todo-backend-service --force-new-deployment --profile knightec
aws ecs update-service --cluster todo-cluster --service todo-frontend-service --force-new-deployment --profile knightec
```
 
### Scale down to zero (stop incurring costs when not working)
```bash
aws ecs update-service --cluster todo-cluster --service todo-backend-service --desired-count 0 --profile knightec
aws ecs update-service --cluster todo-cluster --service todo-frontend-service --desired-count 0 --profile knightec
```
 
### Scale back up
```bash
aws ecs update-service --cluster todo-cluster --service todo-backend-service --desired-count 2 --profile knightec
aws ecs update-service --cluster todo-cluster --service todo-frontend-service --desired-count 1 --profile knightec
```
 
---
 
## Experiment Workflow
 
The typical workflow for each deployment strategy experiment:
 
```
1. terraform apply          # recreate clean infrastructure
2. push images (if needed)  # only if ECR repos were somehow lost
3. force new deployment     # ensure ECS pulls latest images
4. run experiments          # collect metrics
5. terraform destroy        # tear down for next strategy
```
 
 