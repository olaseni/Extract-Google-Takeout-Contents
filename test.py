import extract
import os
import pathlib
import random
import string
import tarfile
import tempfile
import unittest
import zipfile
from typing import List
from unittest.mock import patch


def random_content(length=10):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))


def create_zipped_archive_with_files(filename: str, number_of_files: int = 3, start = 0):
    files = {f'file{index + start}.txt': random_content(index * 10)
             for index in range(number_of_files)}

    with zipfile.ZipFile(filename, 'w') as zip_file:
        for name, content in files.items():
            zip_file.writestr(name, content)


def get_sample_users() -> List[str]:
    return [
        'user1@communityrevolution.co.uk',
        'user2@communityrevolution.co.uk',
        'user3@communityrevolution.co.uk',
        'user4@communityrevolution.co.uk',
        'user1@another-domain.com',
        'sans-domain'
    ]


def create_sample_combined_archive(target_path: str) -> str:
    source_path = os.path.join(target_path, '20241010')

    for email_user in get_sample_users():
        user_source_path = os.path.join(source_path, email_user)
        # make each user's containing directory
        os.makedirs(user_source_path)
        create_zipped_archive_with_files(os.path.join(user_source_path, 'takeout-01.zip'))
        create_zipped_archive_with_files(os.path.join(user_source_path, 'takeout-02.zip'), 4, 4)

    compressed_path = os.path.join(target_path, '20241010.xz')

    with tarfile.open(compressed_path, 'w:xz') as tar_file:
        tar_file.add(source_path, arcname=os.path.basename(source_path))

    return compressed_path


class TestExtractionScript(unittest.TestCase):
    def setUp(self):
        self.source = tempfile.TemporaryDirectory()
        self.compressed_path = create_sample_combined_archive(self.source.name)
        self.destination = tempfile.TemporaryDirectory()

    def tearDown(self):
        try:
            self.source.cleanup()
        except OSError:
            pass
        try:
            self.destination.cleanup()
        except OSError:
            pass

    def test_combined_archive(self):
        self.assertTrue(os.path.exists(self.compressed_path))

    def test_get_email_address_from_path(self):
        # User email should be returned if contained in path in the second level only
        self.assertEqual(
            extract.get_email_address_from_path('20240927T191328Z/user-08@communityrevolution.co.uk'),
            'user-08@communityrevolution.co.uk'
        )
        self.assertEqual(
            extract.get_email_address_from_path(
                '20240927T191328Z/user-01@communityrevolution.co.uk/takeout-20240927T191331Z-001.zip'),
            'user-01@communityrevolution.co.uk'
        )
        self.assertIsNone(
            extract.get_email_address_from_path('20240927T191328Z/Second-level/user-08@communityrevolution.co.uk')
        )
        # Method should return None if TCR domain isn't found
        self.assertIsNone(extract.get_email_address_from_path('20240927T191328Z/user-01@communityrevolution.com'))
        self.assertIsNone(extract.get_email_address_from_path('20240927T191328Z/sans-domain'))

    def test_email_user_folders_are_created(self):
        destination_path = self.destination.name
        extract.extract_exported_takeout_data(self.compressed_path, destination_path)

        # Check that the extracted source exists
        expected_extracted_source = os.path.join(destination_path, '20241010')
        self.assertTrue(os.path.isdir(expected_extracted_source))

        illegal_users = ['user1@another-domain.com', 'sans-domain']

        for email_user in get_sample_users():
            email_user_path = os.path.join(expected_extracted_source, email_user)
            email_user_path_exists = os.path.exists(email_user_path)
            if email_user in illegal_users:
                self.assertFalse(email_user_path_exists)
            else:
                self.assertTrue(email_user_path_exists)

        sub_folders = [subdir.name for subdir in pathlib.Path(expected_extracted_source).rglob('*') if subdir.is_dir()]
        self.assertCountEqual(sub_folders, [
            'user1@communityrevolution.co.uk',
            'user2@communityrevolution.co.uk',
            'user3@communityrevolution.co.uk',
            'user4@communityrevolution.co.uk'
        ])

    @patch('extract.extract_inner_zip_file')
    def test_email_users_have_takeout_archives(self, mocked_function):
        destination_path = self.destination.name
        extract.extract_exported_takeout_data(self.compressed_path, destination_path)
        # The function is called once for each zipped file
        self.assertEqual(mocked_function.call_count, 8)

        expected_extracted_source = os.path.join(destination_path, '20241010')

        for email_user in get_sample_users():
            email_user_path = os.path.join(expected_extracted_source, email_user)
            if not os.path.exists(email_user_path):
                continue

            for sub_path in pathlib.Path(email_user_path).rglob('*'):
                self.assertTrue(sub_path.name.endswith('.zip'))

    def test_extract_exported_takeout_data(self):
        destination_path = self.destination.name
        extract.extract_exported_takeout_data(self.compressed_path, destination_path)

        expected_extracted_source = os.path.join(destination_path, '20241010')

        for email_user in get_sample_users():
            email_user_path = os.path.join(expected_extracted_source, email_user)
            if not os.path.exists(email_user_path):
                continue

            # The takeout archives should have been removed
            # The folder should contain regular files
            for sub_path in pathlib.Path(email_user_path).rglob('*'):
                self.assertFalse(sub_path.name.endswith('.zip'))
                self.assertTrue(sub_path.is_file())



if __name__ == "__main__":
    unittest.main()
