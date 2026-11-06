import hashlib
import hmac
import json
import time

from urllib.parse import parse_qsl
from config import BOT_TOKEN


def verify_init_data(init_data, max_age=86400):
    try:
        values = dict(
            parse_qsl(
                init_data or "",
                keep_blank_values=True
            )
        )

        received = values.pop("hash", "")
        auth_date = int(values.get("auth_date", "0"))
        now = int(time.time())

        if (
            not received
            or auth_date > now + 60
            or now - auth_date > max_age
        ):
            return None

        check = "\n".join(
            f"{k}={v}"
            for k, v in sorted(values.items())
        )

        secret = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        expected = hmac.new(
            secret,
            check.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, received):
            return None

        return int(json.loads(values["user"])["id"])

    except Exception:
        return None
