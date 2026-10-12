
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SecureCloud-IaC"
      Environment = "Learning"
      ManagedBy   = "Terraform"
    }
  }
}

# Find the official Ubuntu 24.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

# Use the existing default VPC
data "aws_vpc" "default" {
  default = true
}

# Dedicated private subnet with automatic public IP assignment disabled
resource "aws_subnet" "securecloud_private" {
  vpc_id                  = data.aws_vpc.default.id
  cidr_block              = "172.31.48.0/20"
  availability_zone       = "ap-south-1b"
  map_public_ip_on_launch = false

  tags = {
    Name = "SecureCloud-Private-Subnet"
  }
}

# Private route table with no internet gateway or NAT route
resource "aws_route_table" "securecloud_private" {
  vpc_id = data.aws_vpc.default.id

  tags = {
    Name = "SecureCloud-Private-Route-Table"
  }
}

# Associate the private subnet with its dedicated route table
resource "aws_route_table_association" "securecloud_private" {
  subnet_id      = aws_subnet.securecloud_private.id
  route_table_id = aws_route_table.securecloud_private.id
}

# Security group with no inbound access
resource "aws_security_group" "securecloud" {
  name_prefix = "securecloud-"
  description = "SecureCloud EC2 security group with no inbound access"
  vpc_id      = data.aws_vpc.default.id

  # Outbound rules are allowed, but the private route table
  # provides no internet route.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "SecureCloud-Private-SG"
  }
}

# Private Ubuntu EC2 instance
resource "aws_instance" "securecloud" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.securecloud_private.id
  associate_public_ip_address = false

  vpc_security_group_ids = [
    aws_security_group.securecloud.id
  ]

  # Require Instance Metadata Service Version 2
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  # Encrypted root disk
  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "SecureCloud-Learning-Instance"
  }

  depends_on = [
    aws_route_table_association.securecloud_private
  ]
}
