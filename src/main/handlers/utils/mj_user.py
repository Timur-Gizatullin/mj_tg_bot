from main.models import MjUser

db_senders: list[MjUser] = MjUser.objects.get_mj_users()

senders = {}
interaction_left_count = 20

for db_sender in db_senders:
    senders[db_sender.token] = interaction_left_count


def _refresh_senders():
    for key, value in senders:
        senders[key] = interaction_left_count


def get_sender_token() -> str:
    for key, value in senders:
        if value != 0:
            return key
    _refresh_senders()
