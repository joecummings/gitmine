import click

def catch_bad_responses(res, **kwargs) -> None:
    """ Raise error code if response is not 200 OK
    """
    if res.status_code == 401:
        message = f"Error Fetching {kwargs['get']}. Unauthorized 401 \n Bad Credentials"
        click.ClickException(message)
        return

    message = f"Error encountered with status code: {res.status_code}"
    click.ClickException(message)
