class SessionStateKey:
    # The keys are used in streamlits session state and must be unique:

    # Global keys will be initialized at this EOF:
    class Common:
        _prefix = "common" + "-"
        user_id = _prefix + "user_id"
        state = _prefix + "state"

        # Used by login:
        ret_check_login = _prefix + "ret_check_login"
        changed_pw = _prefix + "changed_pw"
        changed_username_or_email = _prefix + "changed_username_or_email"

    class Banking:
        _prefix = "banking" + "-"
        recipient = _prefix + "recipient"
        reference = _prefix + "reference"
        value = _prefix + "value"
        confirm = _prefix + "confirm"
        cancel = _prefix + "cancel"

