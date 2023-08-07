class SessionStateKey:
    # The keys are used in streamlits session state and must be unique:

    # Global keys will be initialized at this EOF:
    class Common:
        _prefix = "common" + "-"
        user = _prefix + "user"
        logged_in = _prefix + "logged_in"
        page = _prefix + "page"
        window_size = _prefix + "window_size"
