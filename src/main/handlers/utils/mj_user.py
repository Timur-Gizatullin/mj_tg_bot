from decouple import config


class MjUserTokenQueue:
    db_senders: list[str] = config("DISCORD_USER_TOKENS").split(" ")
    interaction_left_count: int = 20
    current_sender_index: int = 0

    async def get_sender_token(self) -> str:
        if self.interaction_left_count > 0:
            self.interaction_left_count -= 1
            return self.db_senders[self.current_sender_index]
        if self.current_sender_index == len(self.db_senders) - 1 and self.interaction_left_count <= 0:
            self.current_sender_index = 0
            self.interaction_left_count = 20
            return self.db_senders[self.current_sender_index]
        if self.interaction_left_count <= 0:
            self.current_sender_index += 1
            self.interaction_left_count = 20
            return self.db_senders[self.current_sender_index]
