def test_seat_key_derivation():
    from agentura_sdk.runner.seat_resolver import seat_key
    assert seat_key("dev/pr-code-reviewer") == ("dev/pr-code-reviewer", "pr-code-reviewer", "dev")
    assert seat_key("summarizer") == ("summarizer", "summarizer", "")
    assert seat_key("/dev/x/") == ("dev/x", "x", "dev")
    assert seat_key("") == ("unknown", "", "")
