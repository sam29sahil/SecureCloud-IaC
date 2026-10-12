# SecureCloud-IaC

**Private AWS Infrastructure Provisioning and Security Validation with Terraform, Python, and GitHub Actions**

SecureCloud-IaC is an educational cloud-security portfolio project that provisions a private AWS EC2 environment with Terraform and validates selected security controls through Python and the AWS CLI. GitHub Actions automates Terraform checks, scans the configuration with Checkov, authenticates to AWS through GitHub OIDC, runs live validation, and uploads a JSON security report.

> **Scope:** This project checks specific configuration controls. It is not a full penetration test, compliance certification, or guarantee that an AWS environment is completely secure.

## Highlights

- Infrastructure as Code with Terraform.
- Ubuntu 24.04 LTS EC2 instance in a private subnet.
- No public IPv4 address and no default IPv4/IPv6 route in the checked subnet route table.
- Security group configured with no inbound rules.
- EC2 Instance Metadata Service Version 2 (IMDSv2) required.
- Encrypted EBS storage.
- Python-based live AWS security checks.
- GitHub Actions workflow for formatting, initialization, validation, Checkov scanning, AWS OIDC authentication, and live validation.
- Timestamped JSON report uploaded as a GitHub Actions artifact for 14 days.

## Architecture

```text
Developer
   |
   | Push / pull request
   v
GitHub Repository
   |
   v
GitHub Actions
   |-- Terraform fmt / init / validate
   |-- Checkov Terraform scan
   |
   | OIDC (no long-lived AWS access key in workflow)
   v
AWS IAM Role
   |
   | Read-only EC2/VPC describe permissions
   v
Existing AWS Environment
   |-- Private subnet
   |-- EC2 instance (Ubuntu 24.04, t3.micro)
   |-- Security group with no inbound rules
   |-- Encrypted EBS root volume
   |-- Route table with no default internet route
   |
   v
Python Security Validation
   |
   v
Timestamped JSON report
   |
   v
GitHub Actions artifact (14-day retention)
```

This diagram represents the project's intended validation flow. The GitHub Actions workflow does not create or modify the deployed infrastructure; it validates the configured Terraform code and inspects the existing EC2 instance.

## Technology Stack

| Area | Technology |
|---|---|
| Cloud provider | Amazon Web Services (AWS) |
| Region | Asia Pacific (Mumbai), `ap-south-1` |
| Infrastructure as Code | Terraform |
| Compute | Ubuntu 24.04 LTS on EC2 `t3.micro` |
| Networking | VPC, private subnet, route table, security group |
| Storage | Encrypted EBS gp3 volume |
| Automation | Python 3 and AWS CLI |
| CI | GitHub Actions |
| IaC security scanning | Checkov |
| CI-to-AWS authentication | GitHub OIDC and AWS IAM role |
| Report format | JSON |

## Security Controls Validated

The current Python script checks:

1. EC2 instance is running.
2. Instance has no public IPv4 address.
3. IMDSv2 is required.
4. The subnet does not automatically assign public IPv4 addresses.
5. Attached security groups have no inbound rules.
6. The checked route table has no IPv4 or IPv6 default route.
7. EBS volumes attached to the instance are encrypted.

The script prints a `PASS` or `FAIL` result for each check and exits with a nonzero status if a check fails or validation cannot complete. It writes a timestamped report to `reports/security-report-YYYYMMDDTHHMMSSZ.json`.

A successful run confirms only the checks implemented above. It does not assess every AWS resource, IAM policy, application vulnerability, or account-level security setting.

## GitHub Actions Workflow

Workflow file: [`.github/workflows/terraform.yml`](.github/workflows/terraform.yml)

On pushes to `main`, pull requests targeting `main`, and manual workflow dispatches, the workflow:

1. Checks out the repository and configures Python and Terraform.
2. Runs `terraform fmt -check -recursive`.
3. Initializes Terraform with `terraform init -backend=false`.
4. Runs `terraform validate`.
5. Scans Terraform configuration with Checkov.
6. For non-pull-request runs, obtains AWS credentials through GitHub OIDC.
7. Runs live validation against the configured EC2 instance.
8. Uploads the JSON report as the `securecloud-security-report` artifact for 14 days.

**Checkov note:** the workflow currently uses `--soft-fail`, so Checkov findings do not by themselves fail the workflow. A green workflow should not be interpreted as proof that Checkov found no issues.

### OIDC security

The workflow uses GitHub's OIDC identity to assume an AWS IAM role rather than storing long-lived AWS access keys in repository secrets. The `AWS_ROLE_ARN` repository secret stores the role ARN. The IAM role trust policy should restrict which repository and branch can assume it, and its permissions should remain limited to the read operations needed by the validator.

Do not commit AWS credentials, Terraform state, or secret values to the repository.

## Repository Structure

```text
SecureCloud-IaC/
├── .github/
│   └── workflows/
│       └── terraform.yml
├── main.tf
├── variables.tf
├── outputs.tf
├── validate_security.py
├── reports/                 # Generated locally; reports may be ignored by Git
├── .terraform.lock.hcl
├── .gitignore
└── README.md
```

Terraform's local state and working directory (including `terraform.tfstate` and `.terraform/`) should not be committed to GitHub.

## Prerequisites

Install and configure:

- Git
- Terraform
- AWS CLI
- Python 3
- An AWS account with permissions appropriate to the resources being managed

Configure AWS authentication before using Terraform locally. Prefer a dedicated least-privilege IAM identity or an appropriate federated identity instead of the AWS root user.

## Run Locally

Clone the repository:

```bash
git clone https://github.com/sam29sahil/SecureCloud-IaC.git
cd SecureCloud-IaC
```

Initialize and validate the Terraform configuration:

```bash
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
```

Review the plan and estimated charges before applying:

```bash
terraform apply
```

View outputs:

```bash
terraform output
```

Run live security validation after AWS credentials are configured and the Terraform state is available:

```bash
python validate_security.py
```

The script uses `EC2_INSTANCE_ID` when that environment variable is set (as it is in the GitHub Actions workflow). Otherwise, it reads `instance_id` from `terraform output -json`.

## Download a CI Security Report

1. Open the [GitHub Actions runs](https://github.com/sam29sahil/SecureCloud-IaC/actions).
2. Select a completed run triggered by a push to `main` or a manual dispatch.
3. Find the **Artifacts** section.
4. Download `securecloud-security-report`.

Artifacts are configured to be retained for 14 days. A report is only produced if the live validation script reaches its report-writing stage; inspect the workflow logs if no artifact is available.

## Cost Management

AWS resources can incur charges even without a public IP address.

- A running EC2 instance can incur compute charges.
- EBS volumes can incur storage charges.
- Review the current pricing for your account and region.
- This design does not provision a NAT gateway.

When the environment is no longer needed, review the destruction plan and remove Terraform-managed resources:

```bash
terraform plan -destroy
terraform destroy
```

Only destroy resources after confirming that you no longer need them or their data. A green GitHub Actions run does not stop AWS resources or stop charges.

## Current Limitations

- The instance has no ordinary direct internet connectivity.
- The validator checks selected controls rather than performing a comprehensive security audit.
- Checkov is currently configured with soft-fail behavior.
- Centralized logging, threat detection, and SIEM integration are not implemented.
- Private remote administration is not configured by this project.
- The workflow validates existing infrastructure; it does not run `terraform apply`.

## Roadmap

- [x] Provision private EC2 infrastructure with Terraform.
- [x] Add Python checks for selected AWS security controls.
- [x] Add GitHub Actions Terraform validation and Checkov scanning.
- [x] Configure GitHub OIDC authentication for live AWS validation.
- [x] Generate and upload timestamped JSON security reports.
- [ ] Add policy-as-code enforcement with explicit failure thresholds.
- [ ] Add a secured remote Terraform state backend and locking.
- [ ] Expand IAM, logging, and network security checks.
- [ ] Add screenshots of successful workflow runs and example reports.

## Learning Outcomes

This project demonstrates practical work with Infrastructure as Code, AWS EC2 and VPC networking, private cloud design, EC2 metadata hardening, EBS encryption, Python automation, AWS CLI, GitHub Actions, OIDC federation, and security reporting.

## Disclaimer

This project is intended for educational and portfolio use. Review infrastructure plans, IAM permissions, and AWS costs before deployment. Use security testing only on systems and accounts for which you have authorization.
