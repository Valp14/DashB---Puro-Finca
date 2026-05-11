"""Genera hashes seguros para PORTAL_USERS.

Uso:
    python scripts/hash_password.py "contrasena-larga-y-unica"
"""

from __future__ import annotations

import getpass
import sys

from werkzeug.security import generate_password_hash


def main() -> int:
    password = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("Password: ")
    if len(password) < 12:
        print("La contrasena debe tener al menos 12 caracteres.", file=sys.stderr)
        return 1

    print(generate_password_hash(password))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
