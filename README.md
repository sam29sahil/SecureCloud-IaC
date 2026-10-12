# SecureCloud-IaC

**Secure Cloud Infrastructure Provisioning and Security Validation using Terraform and AWS**

SecureCloud-IaC is a cloud security learning project that provisions a private AWS EC2 environment using Terraform and validates important security configurations through an automated Python script.

The project demonstrates Infrastructure as Code (IaC), AWS networking, EC2 security hardening, and automated cloud-security checks.

## Project Objectives

- Provision AWS infrastructure using Terraform.
- Deploy an Ubuntu EC2 instance without a public IPv4 address.
- Create a dedicated private subnet and route table.
- Restrict inbound network access using an AWS security group.
- Require Instance Metadata Service Version 2 (IMDSv2).
- Encrypt the EC2 root EBS volume.
- Automate security configuration checks using Python and the AWS CLI.

## Architecture

The project uses the following architecture:

- **Cloud provider:** Amazon Web Services (AWS)
- **Region:** Asia Pacific (Mumbai) — `ap-south-1`
- **Infrastructure as Code:** Terraform
- **Compute:** Ubuntu 24.04 LTS on EC2 `t3.micro`
- **Networking:** Dedicated private subnet and route table
- **Network security:** Security group with no inbound rules
- **Storage security:** Encrypted 8 GiB gp3 root volume
- **Metadata security:** IMDSv2 required
- **Validation:** Python security validation script

The EC2 instance has no public IP and the dedicated route table has no default internet route. This design intentionally prevents ordinary direct internet connectivity.

## Security Controls

| Security control | Implementation |
|---|---|
| Public IP exposure | Disabled |
| Inbound access | No inbound security-group rules |
| Internet routing | No default internet route |
| Instance metadata | IMDSv2 required |
| Root disk | EBS encryption enabled |
| Network isolation | Dedicated private subnet |
| Security validation | Automated Python checks |

## Project Structure

```text
SecureCloud-IaC/
├── main.tf
├── variables.tf
├── outputs.tf
├── .terraform.lock.hcl
├── .gitignore
├── README.md
└── validate_security.py
```

Terraform may also generate local files and directories such as `terraform.tfstate`, `.terraform/`, and backup files. These should not be committed to GitHub.

## Prerequisites

Install and configure:

- Terraform
- AWS CLI
- Python 3
- Git
- An AWS account with appropriate permissions

Configure AWS authentication before running Terraform. Use a dedicated least-privilege identity for routine development rather than the AWS root user.

## Installation and Deployment

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd SecureCloud-IaC
```

Initialize Terraform:

```bash
terraform init
```

Format and validate the configuration:

```bash
terraform fmt
terraform validate
```

Review the proposed infrastructure changes:

```bash
terraform plan
```

Deploy only after reviewing the plan and confirming that the resources and expected costs are acceptable:

```bash
terraform apply
```

View the outputs:

```bash
terraform output
```

## Automated Security Validation

Run the Python validation script from the project directory:

```bash
python validate_security.py
```

The script uses Terraform outputs and AWS CLI queries to check:

- EC2 instance state
- Public IPv4 address assignment
- IMDSv2 configuration
- Subnet automatic public-IP assignment
- Inbound security-group rules
- Default IPv4 and IPv6 routes
- EBS volume encryption

The script reports individual checks as `PASS` or `FAIL` and returns a nonzero exit status if a check fails or validation cannot complete.

A passing result confirms the specific checks implemented in the script; it does not guarantee complete security of the AWS account or infrastructure.

## Cost Management

AWS resources can incur charges even when they have no public IP address.

- EC2 instances can incur compute charges while running.
- EBS volumes can incur storage charges.
- Review the AWS pricing applicable to your account and region.
- No NAT gateway is provisioned by this configuration.

When you no longer need the environment, review the destruction plan and remove the Terraform-managed resources:

```bash
terraform plan -destroy
terraform destroy
```

Do not destroy resources that contain data you need to keep.

## Limitations

- The instance has no ordinary direct internet connectivity.
- The project does not yet implement centralized monitoring, threat detection, or SIEM integration.
- The security validation script checks selected configurations rather than performing a comprehensive security audit.
- Access to the private instance requires an appropriately designed private-access mechanism if remote administration is needed later.

## Future Improvements

- Add Terraform security scanning with Checkov or Trivy.
- Integrate Terraform formatting and validation into GitHub Actions.
- Add policy-as-code checks.
- Introduce centralized logging and monitoring.
- Explore secure remote administration without exposing SSH publicly.
- Add automated reporting of security validation results.

## Learning Outcomes

This project demonstrates practical experience with:

- Terraform and Infrastructure as Code
- AWS EC2 and VPC networking
- Private cloud infrastructure
- Cloud security configuration
- Python automation and AWS CLI
- Infrastructure validation and cost awareness

## Disclaimer

This project is intended for educational and portfolio purposes. Always review infrastructure plans, access permissions, and applicable AWS charges before deploying resources.