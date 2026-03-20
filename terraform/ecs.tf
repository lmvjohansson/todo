resource "aws_ecs_cluster" "todo_cluster" {
  name = "todo-cluster"
}

resource "aws_ecs_task_definition" "todo_backend" {
  family                   = "todo-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = "arn:aws:iam::600889066998:role/ecsTaskExecutionRole"
  task_role_arn            = "arn:aws:iam::600889066998:role/ecsTaskRole"

  container_definitions = jsonencode([
    {
      name      = "todo-backend"
      image     = "${aws_ecr_repository.todo_backend.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 5000
          hostPort      = 5000
        }
      ]
      environment = [
        { name = "DB_HOST",      value = var.rds_endpoint },
        { name = "DB_NAME",      value = var.rds_database_name },
        { name = "DB_PORT",      value = "5432" },
        { name = "SECRET_NAME",  value = var.rds_secret },
        { name = "AWS_REGION",   value = var.aws_region }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/todo-backend"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "todo_frontend" {
  family                   = "todo-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = "arn:aws:iam::600889066998:role/ecsTaskExecutionRole"
  task_role_arn            = "arn:aws:iam::600889066998:role/ecsTaskRole"

  container_definitions = jsonencode([
    {
      name      = "todo-frontend"
      image     = "${aws_ecr_repository.todo_frontend.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/todo-frontend"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      environment = [
        { name = "BACKEND_URL", value = aws_lb.todo_backend_alb.dns_name }
      ]
    }
  ])
}

resource "aws_ecs_service" "todo_frontend_service" {
  name            = "todo-frontend-service"
  cluster         = aws_ecs_cluster.todo_cluster.id
  task_definition = aws_ecs_task_definition.todo_frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  load_balancer {
    target_group_arn = aws_lb_target_group.todo_frontend_tg.arn
    container_name   = "todo-frontend"
    container_port   = 80
  }
  
  network_configuration {
    assign_public_ip = true
    security_groups  = [aws_security_group.frontend_ecs.id]
    subnets          = data.aws_subnets.default.ids
  }
}

resource "aws_ecs_service" "todo_backend_service" {
  name            = "todo-backend-service"
  cluster         = aws_ecs_cluster.todo_cluster.id
  task_definition = aws_ecs_task_definition.todo_backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  load_balancer {
    target_group_arn = aws_lb_target_group.todo_backend_tg.arn
    container_name   = "todo-backend"
    container_port   = 5000
  }
  
  network_configuration {
    assign_public_ip = true
    security_groups  = [aws_security_group.backend_ecs.id]
    subnets          = data.aws_subnets.default.ids
  }
}