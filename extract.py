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
        description="Extract the contents of Google Takeout data preserving folder structure.")
    parser.add_argument("--source",
                        required=True,
                        help="Google Takeout compressed archive",
                        type=argparse.FileType('rb'))
    parser.add_argument("--destination",
                        required=True,
                        help="The destination directory where data will be extracted to. This path will be created if it doesn't exist.")
    arguments = parser.parse_args()

    # Flag to control whether an extraction is allowed
    process_extraction = True

    # Do some basic checks on the source archive
    try:
        if not tarfile.is_tarfile(arguments.source):
            raise ValueError('Invalid compression type.')
    except OSError as error:
        print(f"Unable to proceed due to a source path error: {error}")
        process_extraction = False
    finally:
        try:
            arguments.source.close()
        except OSError:
            raise

    # Attempt to create the destination directory if it doesn't exist
    try:
        if not os.path.exists(arguments.destination):
            os.makedirs(arguments.destination)
        if not os.path.exists(arguments.destination):
            raise ValueError(f"Destination path [{arguments.destination}] does not exist")
    except OSError as error:
        print(f"Unable to proceed due to a destination path error: {error}")
        process_extraction = False

    if not process_extraction:
        exit(1)

    # Extract and handle files
    extract_exported_takeout_data(
        # Points to archive containing compressed Google Takeout data
        arguments.source.name,
        # Directory where extracted files will be placed
        arguments.destination
    )
