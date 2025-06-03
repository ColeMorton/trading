def validate_requester(event):
    # Check the source IP address
    source_ip = event["requestContext"]["http"]["sourceIp"]
    if source_ip != "3.12.143.24" and source_ip != "178.162.225.106":
        raise ValueError(f"Unauthorized IP address: {source_ip}")

    # Parse headers body
    headers = event.get("headers", {})
    requester = headers.get("x-requester")
    if requester != "trendspider":
        raise ValueError(f"Unauthorized requester: {requester}")
    reason = headers.get("x-reason")
    if reason != "alert-webhook":
        raise ValueError(f"Unauthorized reason: {reason}")

    return True


def validate_request(body):
    if not body.get("symbol") or not body.get("action") or not body.get("quantity"):
        raise ValueError("Missing required parameters")


def validate_exchange(body):
    if body.get("category") == "linear":
        return "bybit"
    if body.get("class") == "cfd":
        return "ibkr"
    raise ValueError("Unknown exchange")
