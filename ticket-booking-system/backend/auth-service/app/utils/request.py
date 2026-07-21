#         If you're using Nginx or a Load Balancer
#         Instead of: client_ip = request.client.host
#         forwarded_ip = request.headers.get("X-Forwarded-For")


# if forwarded_ip:
#     client_ip = forwarded_ip.split(",")[0].strip()
# else:
#     client_ip = request.client.host


from fastapi import Request


def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    x_real_ip = request.headers.get("X-Real-IP")

    if x_real_ip:
        return x_real_ip

    return request.client.host
