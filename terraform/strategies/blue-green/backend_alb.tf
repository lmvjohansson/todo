# ─── Backend ALB ───────────────────────────────────────────────
resource "aws_lb" "todo_backend_alb" {
  name               = "todo-backend-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.backend_alb.id]
  subnets            = data.aws_subnets.default.ids
  enable_deletion_protection = false
}

resource "aws_lb_target_group" "todo_backend_tg" {
  name        = "todo-backend-tg"
  target_type = "ip"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    path      = "/api/ready"
    protocol  = "HTTP"
    matcher   = "200"
  }
}

resource "aws_lb_target_group" "todo_backend_tg_green" {
  name        = "todo-backend-tg-green"
  target_type = "ip"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    path      = "/api/ready"
    protocol  = "HTTP"
    matcher   = "200"
  }
}

resource "aws_lb_listener" "todo_backend_listener" {
  load_balancer_arn = aws_lb.todo_backend_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "404: Not Found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener_rule" "todo_backend_production_rule" {
  listener_arn = aws_lb_listener.todo_backend_listener.arn
  priority     = 100

  action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.todo_backend_tg.arn
        weight = 100
      }
      target_group {
        arn    = aws_lb_target_group.todo_backend_tg_green.arn
        weight = 0
      }
    }
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  lifecycle {
    ignore_changes = [action]
  }
}

resource "aws_lb_listener_rule" "todo_backend_test_rule" {
  listener_arn = aws_lb_listener.todo_backend_listener.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.todo_backend_tg_green.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}