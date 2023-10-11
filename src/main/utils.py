async def is_has_censor(message: str, censor_list: list[str]) -> bool:
    message = message.lower()
    message = message.replace(" ", "")

    for censor_word in censor_list:
        if message.find(censor_word.lower()) != -1:
            return True

    return False
