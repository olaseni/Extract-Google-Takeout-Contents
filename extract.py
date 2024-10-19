import os
import pathlib
import tarfile
from typing import Optional
import zipfile

def extract_inner_zip_file(zipped_file_path, target_path):
    try:
        with zipfile.ZipFile(zipped_file_path, 'r') as zip_ref:
            zip_ref.extractall(target_path)

        # clean up
        os.remove(zipped_file_path)
    except Exception:
        print(f"Error while extracting {zipped_file_path}")
        raise

def get_email_address_from_path(path_in_archive: str) -> Optional[str]:
    """
    File contents in the archive are arranged based on the user's email address.
    Each email user should have a directory containing their own data. That directory should be
    named the same as the user's email address.
    We can extract the concerned email from the string.
    """
    path_parts = pathlib.Path(path_in_archive).parts

    if len(path_parts) > 1 and path_parts[1].endswith('@communityrevolution.co.uk'):
        return path_parts[1]
    return None


def extract_exported_takeout_data(compressed_source_path: str, target_destination_directory: str):
    """
    Processes the Google Takeout export files and extracts them to the specified directory.
    """
    try:
        with tarfile.open(compressed_source_path, 'r:xz') as tar_handle:
            for member in tar_handle.getmembers():
                member: tarfile.TarInfo
                email = get_email_address_from_path(member.path)

                if not member.isfile() or not email:
                    continue

                tar_handle.extract(member, target_destination_directory)

                if member.name.endswith('.zip'):
                    extract_inner_zip_file(
                        # The path where the file was just extracted to
                        os.path.join(target_destination_directory, member.name),
                        # The destination for inner files which are also archives within the email user folder
                        os.path.join(target_destination_directory, pathlib.Path(member.name).parent)
                    )

    except tarfile.TarError as e:
        print(f"Error reading compressed source file: {compressed_source_path}:{e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract the contents of Google Takeout archives preserving folder structure.")
    parser.add_argument("--source",
                        required=True,
                        help="Source folder that contains chunked Google Takeout archives")
    parser.add_argument("--destination",
                        required=True,
                        help="Destination folder to hold extracted data. It will be created if it doesn't exist.")
    arguments = parser.parse_args()

    # Assert that the source folder is accessible
    try:
        if not( os.path.isdir(arguments.source) and os.access(arguments.source, os.R_OK)):
            raise ValueError('Unable to access the source folder.')
    except OSError as error:
        print(f"Unable to proceed due to a source path error: {error}")
        raise

    # Attempt to access or otherwise create the destination folder if it doesn't exist
    try:
        os.makedirs(arguments.destination, exist_ok=True)
        if not (os.path.isdir(arguments.destination) and os.access(arguments.destination, os.W_OK)):
            raise ValueError(f"Destination path [{arguments.destination}] does not exist, or is invalid")
    except OSError as error:
        print(f"Unable to proceed due to a destination path error: {error}")
        raise

    # Extract and handle files
    extract_exported_takeout_data(
        # Points to folder containing chunks of compressed Google Takeout data organised into sub-folders
        arguments.source.name,
        # Folder where extracted files will be placed
        arguments.destination
    )
