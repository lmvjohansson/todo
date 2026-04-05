resource "aws_cloudwatch_metric_alarm" "backend_5xx" {
  alarm_name          = "todo-backend-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 100
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.todo_backend_alb.arn_suffix
  }
}