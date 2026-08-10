import argparse
import json
import os
import sys
from datetime import datetime, timezone

import boto3


DEFAULT_PREFIX = "preprocessor-shadow"


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(f"{name}_REQUIRED")

    return value


def build_s3_client():
    return boto3.client("s3")


def build_evidence(
    *,
    action: str,
    shadow_run_id: str,
    status: str,
) -> dict:
    return {
        "schema_version": "1.0",
        "service": "preprocessor",
        "component": "shadow-control",
        "action": action,
        "shadow_run_id": shadow_run_id,
        "status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def evidence_key(
    *,
    prefix: str,
    shadow_run_id: str,
    name: str,
) -> str:
    prefix = prefix.strip("/")

    return (
        f"{prefix}/"
        f"{shadow_run_id}/"
        f"{name}.json"
    )


def put_evidence(
    *,
    s3,
    bucket: str,
    key: str,
    payload: dict,
) -> str | None:
    body = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    response = s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )

    return response.get("VersionId")


def get_evidence(
    *,
    s3,
    bucket: str,
    key: str,
) -> dict:
    response = s3.get_object(
        Bucket=bucket,
        Key=key,
    )

    return json.loads(
        response["Body"].read().decode("utf-8")
    )


def run_evidence_smoke(args) -> int:
    bucket = require_env(
        "PREPROCESSOR_SHADOW_EVIDENCE_BUCKET"
    )

    prefix = os.getenv(
        "PREPROCESSOR_SHADOW_EVIDENCE_PREFIX",
        DEFAULT_PREFIX,
    ).strip()

    shadow_run_id = args.shadow_run_id.strip()

    if not shadow_run_id:
        raise RuntimeError("SHADOW_RUN_ID_REQUIRED")

    key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="control-runner-smoke",
    )

    payload = build_evidence(
        action="EVIDENCE_SMOKE",
        shadow_run_id=shadow_run_id,
        status="PASS",
    )

    s3 = build_s3_client()

    version_id = put_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
        payload=payload,
    )

    print("S3_PUT=PASS")
    print(f"EVIDENCE_BUCKET={bucket}")
    print(f"EVIDENCE_KEY={key}")
    print(
        f"EVIDENCE_VERSION_ID="
        f"{version_id or ''}"
    )

    loaded = get_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
    )

    print("S3_GET=PASS")

    if loaded != payload:
        raise RuntimeError(
            "EVIDENCE_CONTENT_MISMATCH"
        )

    print("S3_CONTENT_VERIFY=PASS")
    print(
        "PREPROCESSOR_SHADOW_CONTROL_"
        "EVIDENCE=SUCCESS"
    )

    return 0


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--action",
        required=True,
        choices=[
            "EVIDENCE_SMOKE",
        ],
    )

    parser.add_argument(
        "--shadow-run-id",
        required=True,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.action == "EVIDENCE_SMOKE":
            return run_evidence_smoke(args)

        raise RuntimeError(
            f"UNSUPPORTED_ACTION:{args.action}"
        )

    except Exception as exc:
        print(
            "SHADOW_CONTROL_FAILED="
            f"{type(exc).__name__}:{exc}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())