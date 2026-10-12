import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REGION = "ap-south-1"


def run_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "Command failed"
        )

    return result.stdout


def aws_json(*args):
    output = run_command([
        "aws", *args,
        "--region", REGION,
        "--output", "json",
    ])
    return json.loads(output)


def main():
    print("\nSecureCloud-IaC Security Validation")
    print("=" * 42)

    results = []

    def record(name, passed, detail):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: {detail}")
        results.append({
            "check": name,
            "status": status,
            "passed": bool(passed),
            "detail": str(detail),
        })

    try:
        # GitHub Actions runners do not have the local Terraform state.
        # Use EC2_INSTANCE_ID in CI; use Terraform output for local runs.
        instance_id = os.environ.get("EC2_INSTANCE_ID")
        if not instance_id:
            outputs = json.loads(
                run_command(["terraform", "output", "-json"])
            )
            instance_id = outputs["instance_id"]["value"]

        response = aws_json(
            "ec2", "describe-instances",
            "--instance-ids", instance_id,
        )

        instance = response["Reservations"][0]["Instances"][0]
        subnet_id = instance["SubnetId"]

        # 1. Instance state
        record(
            "Instance running",
            instance["State"]["Name"] == "running",
            instance["State"]["Name"],
        )

        # 2. No public IPv4 address
        public_ip = instance.get("PublicIpAddress")
        record(
            "No public IP",
            not public_ip,
            public_ip or "No public IPv4 address",
        )

        # 3. IMDSv2 required
        tokens = instance.get("MetadataOptions", {}).get("HttpTokens")
        record(
            "IMDSv2 required",
            tokens == "required",
            f"HttpTokens={tokens}",
        )

        # 4. Subnet does not auto-assign public IPs
        subnet_data = aws_json(
            "ec2", "describe-subnets",
            "--subnet-ids", subnet_id,
        )
        subnet = subnet_data["Subnets"][0]
        auto_public_ip = subnet["MapPublicIpOnLaunch"]

        record(
            "Subnet public IP assignment disabled",
            auto_public_ip is False,
            f"MapPublicIpOnLaunch={auto_public_ip}",
        )

        # 5. No inbound rules on attached security groups
        group_ids = [
            group["GroupId"]
            for group in instance.get("SecurityGroups", [])
        ]

        if not group_ids:
            record("Security group inbound rules", False,
                   "No security groups attached")
        else:
            groups_data = aws_json(
                "ec2", "describe-security-groups",
                "--group-ids", *group_ids,
            )

            for group in groups_data["SecurityGroups"]:
                ingress = group.get("IpPermissions", [])
                record(
                    f"Inbound rules ({group['GroupId']})",
                    len(ingress) == 0,
                    "No inbound rules" if not ingress
                    else f"{len(ingress)} inbound rule(s) found",
                )

        # 6. No default internet route in the subnet route table
        route_data = aws_json(
            "ec2", "describe-route-tables",
            "--filters",
            f"Name=association.subnet-id,Values={subnet_id}",
        )

        route_tables = route_data.get("RouteTables", [])

        if not route_tables:
            record("Private route table", False,
                   "No explicitly associated route table found")
        else:
            routes = route_tables[0].get("Routes", [])

            default_routes = [
                route for route in routes
                if route.get("DestinationCidrBlock") == "0.0.0.0/0"
                or route.get("DestinationIpv6CidrBlock") == "::/0"
            ]

            record(
                "No default internet route",
                len(default_routes) == 0,
                "No IPv4/IPv6 default route" if not default_routes
                else f"{len(default_routes)} default route(s) found",
            )

        # 7. EBS volumes encrypted
        mappings = instance.get("BlockDeviceMappings", [])
        volume_ids = [
            mapping["Ebs"]["VolumeId"]
            for mapping in mappings
            if mapping.get("Ebs", {}).get("VolumeId")
        ]

        if not volume_ids:
            record("EBS volume encryption", False,
                   "No EBS volumes found")
        else:
            volumes_data = aws_json(
                "ec2", "describe-volumes",
                "--volume-ids", *volume_ids,
            )

            volumes = volumes_data["Volumes"]
            encrypted = all(volume.get("Encrypted") is True
                            for volume in volumes)

            record(
                "EBS volume encryption",
                encrypted,
                "All attached EBS volumes encrypted"
                if encrypted else "An EBS volume is not encrypted",
            )

        failed_count = sum(1 for item in results if not item["passed"])
        report = {
            "project": "SecureCloud-IaC",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "region": REGION,
            "instance_id": instance_id,
            "summary": {
                "total": len(results),
                "passed": len(results) - failed_count,
                "failed": failed_count,
                "result": "PASS" if failed_count == 0 else "FAIL",
            },
            "checks": results,
        }

        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = reports_dir / f"security-report-{timestamp}.json"
        report_path.write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Security report saved: {report_path}")

        print("=" * 42)
        print("RESULT:", "ALL CHECKS PASSED"
              if failed_count == 0 else "REVIEW FAILED CHECKS")

        if failed_count:
            sys.exit(1)

    except (RuntimeError, KeyError, IndexError,
            json.JSONDecodeError) as error:
        print(f"\n[ERROR] Validation could not complete: {error}")
        sys.exit(2)


if __name__ == "__main__":
    main()
