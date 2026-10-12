
output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.securecloud.id
}

output "instance_type" {
  description = "EC2 instance type"
  value       = aws_instance.securecloud.instance_type
}

output "private_ip" {
  description = "Private IP address"
  value       = aws_instance.securecloud.private_ip
}
