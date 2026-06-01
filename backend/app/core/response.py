from uuid import uuid4


def success(data):
    return {
        "code": 0,
        "message": "ok",
        "data": data,
        "request_id": f"req_{uuid4().hex[:10]}",
    }
