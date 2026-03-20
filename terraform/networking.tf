data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ─── Backend Security Groups ───────────────────────────────────────────────
resource "aws_security_group" "backend_alb" {
  name        = "backend-alb-sg"
  description = "Allow HTTP traffic to backend ALB"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_security_group" "backend_ecs" {
  name        = "backend-ecs-sg"
  description = "Allow traffic from ALB to backend ECS tasks"
  vpc_id      = data.aws_vpc.default.id
}

# ─── Backend Ingress Rules ──────────────────────────────────────────────────
resource "aws_vpc_security_group_ingress_rule" "allow_port_80_backend" {
  security_group_id = aws_security_group.backend_alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "allow_alb_traffic_backend" {
  security_group_id = aws_security_group.backend_ecs.id
  referenced_security_group_id = aws_security_group.backend_alb.id
  from_port         = 5000
  ip_protocol       = "tcp"
  to_port           = 5000
}

# ─── Backend Egress Rules ──────────────────────────────────────────────────
resource "aws_vpc_security_group_egress_rule" "backend_alb_egress_ipv4" {
  security_group_id = aws_security_group.backend_alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_vpc_security_group_egress_rule" "backend_alb_egress_ipv6" {
  security_group_id = aws_security_group.backend_alb.id
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_vpc_security_group_egress_rule" "backend_ecs_egress_ipv4" {
  security_group_id = aws_security_group.backend_ecs.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_vpc_security_group_egress_rule" "backend_ecs_egress_ipv6" {
  security_group_id = aws_security_group.backend_ecs.id
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

# ─── Frontend Security Groups ───────────────────────────────────────────────
resource "aws_security_group" "frontend_alb" {
  name        = "frontend-alb-sg"
  description = "Allow HTTP traffic to frontend ALB"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_security_group" "frontend_ecs" {
  name        = "frontend-ecs-sg"
  description = "Allow traffic from ALB to frontend ECS tasks"
  vpc_id      = data.aws_vpc.default.id
}

# ─── Frontend Ingress Rules ──────────────────────────────────────────────────
resource "aws_vpc_security_group_ingress_rule" "allow_port_80_frontend" {
  security_group_id = aws_security_group.frontend_alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "allow_alb_traffic_frontend" {
  security_group_id = aws_security_group.frontend_ecs.id
  referenced_security_group_id = aws_security_group.frontend_alb.id
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

# ─── Frontend Egress Rules ──────────────────────────────────────────────────
resource "aws_vpc_security_group_egress_rule" "frontend_alb_egress_ipv4" {
  security_group_id = aws_security_group.frontend_alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_vpc_security_group_egress_rule" "frontend_alb_egress_ipv6" {
  security_group_id = aws_security_group.frontend_alb.id
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_vpc_security_group_egress_rule" "frontend_ecs_egress_ipv4" {
  security_group_id = aws_security_group.frontend_ecs.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_vpc_security_group_egress_rule" "frontend_ecs_egress_ipv6" {
  security_group_id = aws_security_group.frontend_ecs.id
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

# ─── RDS Security Group ───────────────────────────────────────────────
resource "aws_security_group" "rds_sg" {
  name        = "rds-sg"
  description = "Created by RDS management console"
  vpc_id      = data.aws_vpc.default.id
  
  lifecycle {
    prevent_destroy = true
  }
}

# ─── RDS Ingress Rule ──────────────────────────────────────────────────
resource "aws_vpc_security_group_ingress_rule" "allow_port_5432_rds" {
  security_group_id = aws_security_group.rds_sg.id
  referenced_security_group_id = aws_security_group.backend_ecs.id
  from_port         = 5432
  ip_protocol       = "tcp"
  to_port           = 5432
}

# ─── RDS Egress Rules ──────────────────────────────────────────────────
resource "aws_vpc_security_group_egress_rule" "rds_egress_ipv4" {
  security_group_id = aws_security_group.rds_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_vpc_security_group_egress_rule" "rds_egress_ipv6" {
  security_group_id = aws_security_group.rds_sg.id
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}