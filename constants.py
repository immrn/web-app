class SessionStateKey:
    # The keys are used in streamlits session state and must be unique:

    # Global keys will be initialized at this EOF:
    class Common:
        _prefix = "common" + "-"
        user = _prefix + "user"
        logged_in = _prefix + "logged_in"

    class Banking:
        _prefix = "banking" + "-"
        recipient = _prefix + "recipient"
        reference = _prefix + "reference"
        value = _prefix + "value"
        confirm = _prefix + "confirm"
        cancel = _prefix + "cancel"

