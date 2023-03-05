"""Use Python to access Sharepoint.

Usage: python -m geopython.sharepoint [OPTIONS] SHAREPOINT_FILENAME

Examples:
    python -m geopython.sharepoint
    python -m geopython.sharepoint "Input.xlsx"
    python -m geopython.sharepoint --help
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from loguru import logger as log
from shareplum import Office365, Site
from shareplum.site import Version

from . import utils

ROOT = Path(".")
DATA_DIR = ROOT / "data"


def authenticate(site_url, site_name, username, password):
    authcookie = Office365(site_url, username=username, password=password).GetCookies()
    return Site(f"{site_url}/sites/{site_name}/", version=Version.v365, authcookie=authcookie)


def download_input_file(folder, filename: Optional[str] = "Input.xlsx"):
    # We could iterate through the files for any files that look like "Input*.xlsx" and process them
    # all one-by-one. For now, we will not do this.
    # files = demo_folder.files  # noqa: E800
    # filename = files[0]["Name"]  # noqa: E800

    # Assume the file is called "Input.xlsx" and download this
    file_contents = folder.get_file(filename)
    filepath = DATA_DIR / "interim" / filename
    with open(filepath, "wb") as f:
        f.write(file_contents)

    return filepath


def process_xlsx(filepath):
    # Read in the xlsx & add columns for "Full name" and "ISO date"
    df = pd.read_excel(filepath, sheet_name="Sheet1")
    df["Full name"] = df["First name"] + df["Last name"]
    df["ISO date"] = pd.to_datetime(df["Date"])

    # Add lat, lng & formatted address via geocode lookup
    df.loc[:, ["lat", "lng", "formatted_address"]] = df.apply(
        lambda row: utils.geocode(row.Location),
        result_type="expand",
        axis=1,
    )

    # Export to local file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = filepath.name.replace(".xlsx", "")
    output_filepath = DATA_DIR / "processed" / f"{filename}__{timestamp}.xlsx"
    df.to_excel(output_filepath, index=False)

    return output_filepath


def upload_file(filepath, sharepoint_folder):
    with open(filepath, "rb") as f:
        file_contents = f.read()
        sharepoint_folder.upload_file(file_contents, filepath.name)


def main(sharepoint_filename: Optional[str]):
    site_url = os.environ["SHAREPOINT_SITE_URL"]
    site_name = os.environ["SHAREPOINT_SITE_NAME"]
    username = os.environ["SHAREPOINT_USERNAME"]
    password = os.environ["SHAREPOINT_PASSWORD"]

    # Authenticate with Sharepoint site
    site = authenticate(site_url, site_name, username, password)
    log.info(f"Authenticated with Sharepoint site: {site_url}")

    # Download the specified file from the Input folder of Sharepoint
    input_folder = site.Folder("Shared Documents/Input")
    downloaded_file = download_input_file(folder=input_folder, filename=sharepoint_filename)
    log.info(f"Downloaded file: {downloaded_file}")

    # Process the file (concatenate names, format date, geocode the location)
    processed_file = process_xlsx(downloaded_file)
    log.info(f"Saved processed file into: {processed_file}")

    # Upload local file to Sharepoint "Demo" folder
    output_folder = site.Folder("Shared Documents/Output")
    upload_file(processed_file, output_folder)
    log.opt(ansi=True).info("✅ <green>Successfully uploaded file back to Sharepoint</green> 🎉")


if __name__ == "__main__":
    typer.run(main)
