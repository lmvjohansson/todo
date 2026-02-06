# Comparing Deployment Strategies on AWS – Bachelor's Thesis Project

<div align="center">

**KTH Royal Institute of Technology** | **Knightec Group**

*January – June 2026*

</div>

---

## Working Title

<div align="center">

### Comparing Blue-Green, Rolling, and Canary Deployment Strategies in Amazon Web Services: Impact on System Reliability, Resource Efficiency and Operational Complexity

</div>

---

## Primary Research Question

> *How do blue-green, rolling, and canary deployment strategies compare in terms of system reliability, resource efficiency and operational complexity when deploying containerized full-stack applications on AWS?*

### Sub-Questions

1. How does each deployment strategy perform during failure scenarios in terms of rollback speed and user impact? Specifically, when a deployed version contains critical errors, how quickly can each strategy revert to the stable version, and what percentage of users experience service degradation during the failure and recovery period?
2. What are the infrastructure cost and operational complexity trade-offs between the three deployment approaches? This includes measuring AWS resource consumption, deployment duration, pipeline structure, and the degree of infrastructure and CI/CD (Continuous Integration and Continuous Deployment) configuration required to support each strategy.

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
- **Load Testing:** Locust or k6
- **Version Control:** Git & GitHub

---

## Current Status

### ✅ Completed
- [x] Full-stack TODO application with comprehensive testing
- [x] Docker containerization with proper networking
- [x] CORS configuration and database integration
- [x] Health endpoints (liveness and readiness checks)
- [x] Literature review establishing research gap

### 🚧 In Progress
- [ ] Chapter 1 draft (Introduction)
- [ ] AWS infrastructure setup with ECS Fargate
- [ ] Terraform Infrastructure as Code implementation

### 📋 Upcoming
- [ ] CI/CD pipeline development with GitHub Actions
- [ ] Implementation of three deployment strategies
- [ ] Load testing framework
- [ ] Failure scenario experimentation
- [ ] Results analysis and thesis completion

---

<div align="center">

*This project serves as both a demonstration of technical capabilities in cloud infrastructure and DevOps practices, and as a contribution to the empirical understanding of deployment strategies in production environments.*

**[KTH Royal Institute of Technology](https://www.kth.se)** | **[Knightec Group](https://www.knightec.se)**

</div>
