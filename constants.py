class SessionStateKey:
    # The keys are used in streamlits session state and must be unique:

    # Global keys will be initialized at this EOF:
    class Common:
        _prefix = "common" + "-"
        user_id = _prefix + "user_id"
        state = _prefix + "state"
        show_pw_warning = _prefix + "show_pw_warning"
        pw_before = _prefix + "pw_before"

    class Banking:
        _prefix = "banking" + "-"
        recipient = _prefix + "recipient"
        reference = _prefix + "reference"
        value = _prefix + "value"
        confirm = _prefix + "confirm"
        cancel = _prefix + "cancel"

