from importlib.metadata import files

import extract
import os
import pathlib
import random
import string
import tempfile
import unittest
import zipfile
from typing import List
from unittest.mock import patch

FOLDER_NAME = '20241010'

def random_content(length=10):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))


def create_zipped_archive_with_files(filename: str, number_of_files: int = 4, start = 0):
    files = {f'file{index + start}.txt': random_content(index * 10)
             for index in range(number_of_files)}

    with zipfile.ZipFile(filename, 'w') as zip_file:
        for name, content in files.items():
            zip_file.writestr(name, content)


def get_sample_user_paths() -> List[str]:
    return [
        'user1@communityrevolution.co.uk',
        'user2@communityrevolution.co.uk',
        'user3@communityrevolution.co.uk',
        'user4@communityrevolution.co.uk',
        'user1@another-domain.com',
        'sans-domain',
        'Resource: -32232332',
        'Resource: 12232332',
        'Resources-32232332'
    ]


def create_sample_source_folder(source_path: str):
    for email_user in get_sample_user_paths():
        user_source_path = os.path.join(source_path, email_user)
        # make each user's containing directory
        os.makedirs(user_source_path)
        create_zipped_archive_with_files(os.path.join(user_source_path, 'takeout-01.zip'))
        create_zipped_archive_with_files(os.path.join(user_source_path, 'takeout-02.zip'), 6, 4)


class TestExtractionScript(unittest.TestCase):
    @property
    def source_path(self):
        if self._paths:
            return '%s' % self._paths[0].absolute()
        return None

    @property
    def destination_path(self):
        if self._paths:
            return '%s' % self._paths[1].absolute()
        return None

    def setUp(self):
        self.test_folder = tempfile.TemporaryDirectory()
        parent_path = pathlib.Path(self.test_folder.name, 'paths')

        self._paths = (
            parent_path / 'source/{}'.format(FOLDER_NAME),
            parent_path / 'destination/{}'.format(FOLDER_NAME)
        )

        list(map(lambda path: path.mkdir(parents=True), self._paths ))

        create_sample_source_folder(self.source_path)

    def tearDown(self):
        try:
            self.test_folder.cleanup()
        except OSError:
            pass

    def test_source_folder(self):
        self.assertTrue(os.path.isdir(self.source_path))
        self.assertTrue(os.access(self.source_path, os.R_OK))

    def test_get_is_user_path_allowed(self):
        # Method should return True if path name ends with TCR domain or starts with 'Resource:'
        self.assertTrue(extract.get_is_user_path_allowed('user-01@communityrevolution.co.uk'))
        self.assertTrue(extract.get_is_user_path_allowed('user-08@communityrevolution.co.uk'))
        self.assertTrue(extract.get_is_user_path_allowed('Resource: -132233242'))
        self.assertTrue(extract.get_is_user_path_allowed('Resource: 132233242'))
        # otherwise
        self.assertFalse( extract.get_is_user_path_allowed('takeout-20240927T191331Z-001.zip'))
        self.assertFalse(extract.get_is_user_path_allowed('user-01@communityrevolution.com'))
        self.assertFalse(extract.get_is_user_path_allowed('sans-domain'))
        self.assertFalse(extract.get_is_user_path_allowed('Resource'))

    @patch('extract.extract_user_takeout_archive')
    def test_email_users_have_takeout_archives(self, mocked_function):
        extract.extract_exported_takeout_data(self.source_path, self.destination_path)
        # The function is called once for each zipped file
        self.assertEqual(mocked_function.call_count, 12)

        for path in get_sample_user_paths():
            user_path = pathlib.Path(self.destination_path, path)
            if not user_path.exists():
                continue

            for sub_path in pathlib.Path(user_path).rglob('*'):
                self.assertTrue(sub_path.name.endswith('.zip'))

    def test_extract_exported_takeout_data(self):
        extract.extract_exported_takeout_data(self.source_path, self.destination_path)

        for path in get_sample_user_paths():
            user_path = pathlib.Path(self.destination_path, path)
            if not user_path.exists():
                continue

            # The folder should contain regular files
            for sub_path in pathlib.Path(user_path).rglob('*'):
                self.assertFalse(sub_path.name.endswith('.zip'))
                self.assertTrue(sub_path.is_file())



if __name__ == "__main__":
    unittest.main()
