resource "aws_ecs_service" "todo_backend_service" {
  name                  = "todo-backend-service"
  cluster               = aws_ecs_cluster.todo_cluster.id
  task_definition       = aws_ecs_task_definition.todo_backend.arn
  desired_count         = 5
  launch_type           = "FARGATE"
  wait_for_steady_state = true

  deployment_configuration {
    strategy             = "BLUE_GREEN"
    bake_time_in_minutes = 5
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.todo_backend_tg.arn
    container_name   = "todo-backend"
    container_port   = 5000

    advanced_configuration {
      alternate_target_group_arn = aws_lb_target_group.todo_backend_tg_green.arn
      production_listener_rule   = aws_lb_listener_rule.todo_backend_production_rule.arn
      test_listener_rule         = aws_lb_listener_rule.todo_backend_test_rule.arn
      role_arn                   = aws_iam_role.ecs_alb_role.arn
    }
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