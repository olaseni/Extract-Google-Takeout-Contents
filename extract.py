import os
import pathlib
import zipfile

def extract_user_takeout_archive(takeout_archive, target_extraction_path):
    try:
        with zipfile.ZipFile(takeout_archive, 'r') as zip_ref:
            zip_ref.extractall(target_extraction_path)
    except Exception:
        print(f"Error while extracting {takeout_archive}")
        raise

def get_is_user_path_allowed(path: str) -> bool:
    """
    File contents in the source folder are arranged thus:
     - path ends with user's email address
     - path starts with 'Resource:'
    """
    return path.endswith('@communityrevolution.co.uk') or path.startswith('Resource:')

def extract_exported_takeout_data(source_folder: str, destination_folder: str):
    """
    Processes the Google Takeout export files and extracts them to the specified directory.
    """
    try:
        for source_sub_path in pathlib.Path(source_folder).iterdir(): # type: pathlib.Path
            if source_sub_path.is_dir() and get_is_user_path_allowed(source_sub_path.name):

                for user_file in pathlib.Path(source_sub_path).iterdir(): # type: pathlib.Path
                    if user_file.name.endswith('.zip'):
                        extract_user_takeout_archive(
                            user_file.absolute(),
                            # Supply the destination folder for target extraction
                            (pathlib.Path(destination_folder) / source_sub_path.name).absolute()
                        )

    except Exception as e:
        print(f"Error processing source path: {source_folder}:{e}")

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

        # Ensure source and destination are not the same
        if pathlib.Path(arguments.source).resolve() == pathlib.Path(arguments.destination).resolve():
            raise ValueError("Source and destination seem to point to the same path")
    except OSError as error:
        print(f"Unable to proceed due to a destination path error: {error}")
        raise

    # Extract and handle files
    extract_exported_takeout_data(
        # Points to folder containing chunks of compressed Google Takeout data organised into sub-folders
        arguments.source,
        # Folder where extracted files will be placed
        arguments.destination
    )
