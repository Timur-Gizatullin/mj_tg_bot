from main.models import DsMjUser


async def get_proxy(header: dict[str, str]):
    sender: DsMjUser = await DsMjUser.objects.get_sender_by_token(header["authorization"])

    if sender.proxy:
        proxies = {
            "ss": sender.proxy,
            "ssh": sender.proxy
        }
    else:
        proxies = {}

    return proxies
