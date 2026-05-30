from __future__ import annotations

import argparse
import hashlib


def main() -> None:
    parser = argparse.ArgumentParser(description="Hash a tenant token.")
    parser.add_argument("token", help="Tenant token to hash.")
    args = parser.parse_args()
    digest = hashlib.sha256(args.token.encode("utf-8")).hexdigest()
    print(f"sha256:{digest}")


if __name__ == "__main__":
    main()
