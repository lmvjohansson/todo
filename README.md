# Comparing Deployment Strategies on AWS – Bachelor's Thesis Project
<div align="center">
**KTH Royal Institute of Technology** | **Knightec Group**
*January – June 2026*
</div>

---

## Working Title
<div align="center">

### A Comparative Study of Deployment Strategies in Cloud Environments: Impact on Deployment Process Performance, Failure Response and Resource Efficiency

</div>

---

## Primary Research Question

> *How do blue-green, rolling, and canary deployment strategies compare in terms of deployment process performance, failure response and resource efficiency when deploying applications in a cloud environment?*

---

## Technical Stack

### Application
- **Frontend:** React with Vite
- **Backend:** Python Flask with SQLAlchemy
- **Database:** PostgreSQL
- **Containerization:** Docker & docker-compose

### AWS Infrastructure

| Service | Purpose |
|---------|---------|
| **ECS Fargate** | Container orchestration |
| **Application Load Balancer** | Traffic management |
| **RDS PostgreSQL** | Managed database |
| **CloudWatch** | Monitoring, logging, and metrics |
| **CodeDeploy** | Deployment automation |
| **ECR** | Container image registry |

### DevOps Tooling
- **CI/CD:** GitHub Actions
- **Infrastructure as Code:** Terraform
- **Load Testing:** k6
- **Version Control:** Git & GitHub

---

## Current Status

### ✅ Completed
- [x] Full-stack TODO application with comprehensive testing
- [x] Docker containerization with proper networking
- [x] CORS configuration and database integration
- [x] Health endpoints (liveness and readiness checks)
- [x] Literature review establishing research gap
- [x] AWS infrastructure setup with ECS Fargate (VPC, security groups, ALBs, ECR, ECS cluster, task definitions, services)
- [x] Infrastructure as Code with Terraform (33 resources, fully reproducible with `terraform apply`)
- [x] CI/CD pipeline with GitHub Actions (automated build, push to ECR, and rolling deployment on push to main)
- [x] Thesis writing (Chapters 1–3)

### 🚧 In Progress
- [ ] Thesis writing (Chapters 4-5)
- [ ] Monitoring infrastructure (CloudWatch dashboards and alarms)

### 📋 Upcoming
- [ ] Implementation of three deployment strategies (rolling, blue-green, canary)
- [ ] Load testing framework with k6
- [ ] Failure scenario experimentation
- [ ] Results analysis and thesis completion

---

## Infrastructure Overview

The full AWS infrastructure is defined as Terraform code in the `terraform/` directory and can be reproduced with a single `terraform apply`. Key design decisions:

- **RDS is excluded from Terraform** to prevent data loss on `terraform destroy`. The database endpoint and credentials are passed as input variables.
- **Least-privilege security groups**: ECS tasks only accept traffic from their respective ALB, not directly from the internet.
- **Two separate ALBs**: one for the backend service (load testing target) and one for the frontend.
- Load testing with k6 targets the **backend service directly**, as the frontend is a static asset server not relevant to the deployment strategy metrics.

## CI/CD Pipeline

On every push to `main`, GitHub Actions automatically:

1. Builds Docker images for both backend and frontend
2. Tags images with both `:latest` and the git commit SHA
3. Pushes images to ECR
4. Downloads the current ECS task definition
5. Deploys to ECS Fargate (rolling deployment)

The backend and frontend are deployed in parallel as independent jobs.

---

<div align="center">

*This project serves as both a demonstration of technical capabilities in cloud infrastructure and DevOps practices, and as a contribution to the empirical understanding of deployment strategies in production environments.*

**[KTH Royal Institute of Technology](https://www.kth.se)** | **[Knightec Group](https://www.knightec.se)**

</div>