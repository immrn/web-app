import streamlit as st
from typing import List


__SHADOW__ = "shadow_"


# This is content for a later README file:
# This library creates and manages persistent session states (streamlit).
# It's made for apps using a multipage logic, but not the multipage feature of streamlit.
# Tested for st.selectbox and st.multiselect.
#
# Usage:
# import state
# # main.py, this is the file you run with streamlit (streamlit run main.py):
# s.init()
#
# # in any .py file or in your main.py:
# options = ["red", "blue", "yellow"]
# color = st.selectbox(
#   options=options,
#   key="my_color_key",
#   index=state.index(key="my_color_key", options=options)
# }
#
# You can avoid the persistent state behaviour of an streamlit widget by omitting the key param.
# End of README


def init():
    """!
    Call this function at the beginning of the python file you are running via streamlit.
    It updates/create all shadow states.
    """
    # Create and update shadows to st.session_state. Each shadow stores a value of an element from st.session_state.
    for key in st.session_state:
        if not key.startswith(__SHADOW__):
            st.session_state[__SHADOW__ + key] = st.session_state[key]


def index(key: str, options: List) -> int:
    """!
    Use this to set the index param of st.selectbox (or related).
    Searches for the index of st.session_state[prefix() + key] in options.
    If it doesn't exist, returns 0.

    @param key: same as key in st.selectbox(key=...) but without prefix
    @param options: same as options in st.selectbox(options=...)
    @return: index as int
    """
    try:
        return options.index(st.session_state[__SHADOW__ + key])
    except (ValueError, KeyError):
        return 0


def value(key: str, default=None):
    """!
    Get the value of a key from its shadow state.
    @param key: same as key in st.selectbox(key=...) but without prefix
    @param default: returns this if the key doesn't exist (key value could still be None or [])
    @return: the value of the key stored in its shadow state
    """
    if __SHADOW__ + key in st.session_state:
        return st.session_state[__SHADOW__ + key]
    else:
        return default
