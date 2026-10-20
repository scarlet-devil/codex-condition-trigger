"""Optional, absolute authorization deadline for a bounded local trial."""
from datetime import datetime


def trial_deadline(config):
    value = config.get('trial_expires_at_utc')
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError('trial deadline must be an aware ISO 8601 timestamp')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError('naive timestamp')
        return parsed.timestamp()
    except (ValueError, OverflowError) as error:
        raise ValueError('trial deadline must be an aware ISO 8601 timestamp') from error
