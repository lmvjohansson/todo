resource "aws_ecs_service" "todo_backend_service" {
  name            = "todo-backend-service"
  cluster         = aws_ecs_cluster.todo_cluster.id
  task_definition = aws_ecs_task_definition.todo_backend.arn
  desired_count   = 5
  launch_type     = "FARGATE"
  
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

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
  
  alarms {
    enable      = true
    rollback    = true
    alarm_names = [aws_cloudwatch_metric_alarm.backend_5xx.alarm_name]
  }
}