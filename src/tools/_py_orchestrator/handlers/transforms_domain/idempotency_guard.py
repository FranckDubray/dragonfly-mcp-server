from ..base import AbstractHandler

class IdempotencyGuardHandler(AbstractHandler):
    """
    Check if action already done (idempotency guard).
    Useful for preventing duplicate operations.
    """
    @property
    def kind(self) -> str:
        return "idempotency_guard"

    def run(self, action_id, completed_actions=None, **kwargs) -> dict:
        if completed_actions is None:
            completed_actions = []
        skip = action_id in completed_actions
        return {"skip": skip, "action_id": action_id}
