from config import OWNER_ID


def is_owner(user_id: int) -> bool:
    """
    Checks if the message sender is the bot owner.
    Returns True if owner, else False.
    """

    return user_id == OWNER_ID