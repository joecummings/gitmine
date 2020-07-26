def catch_bad_responses(res) -> None:
    res.raise_for_status()
