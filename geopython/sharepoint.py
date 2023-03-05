"""Use Python to access Sharepoint.

Usage:
    $ python -m geopython.sharepoint
"""
import os

from shareplum import Office365, Site


def authenticate(site_url, site_name, username, password):
    authcookie = Office365(site_url, username=username, password=password).GetCookies()
    return Site(f"{site_url}/sites/{site_name}/", authcookie=authcookie)


def main(site_url, site_name, username, password):
    site = authenticate(site_url, site_name, username, password)

    # Get the library by name
    library = site.List("Documents")

    files = library.GetListItems()

    print(files[0]["Name"])


if __name__ == "__main__":
    main(
        site_url=os.environ["SHAREPOINT_SITE_URL"],
        site_name=os.environ["SHAREPOINT_SITE_NAME"],
        username=os.environ["SHAREPOINT_USERNAME"],
        password=os.environ["SHAREPOINT_PASSWORD"],
    )
