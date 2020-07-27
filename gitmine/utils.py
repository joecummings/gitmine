def catch_bad_responses(res) -> None:
    """ Raise error code if response is not 200 OK
    """

    res.raise_for_status()
