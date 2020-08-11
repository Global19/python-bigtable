# Copyright 2015 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest

import mock

from ._testing import _make_credentials


class Test__create_gapic_client(unittest.TestCase):
    def _invoke_client_factory(self, client_class, **kw):
        from google.cloud.bigtable.base_client import _create_gapic_client

        return _create_gapic_client(client_class, **kw)

    def test_wo_emulator(self):
        client_class = mock.Mock()
        credentials = _make_credentials()
        client = _Client(credentials)
        client_info = client._client_info = mock.Mock()

        result = self._invoke_client_factory(client_class)(client)

        self.assertIs(result, client_class.return_value)
        client_class.assert_called_once_with(
            credentials=client._credentials,
            client_info=client_info,
            client_options=None,
        )

    def test_wo_emulator_w_client_options(self):
        client_class = mock.Mock()
        credentials = _make_credentials()
        client = _Client(credentials)
        client_info = client._client_info = mock.Mock()
        client_options = mock.Mock()

        result = self._invoke_client_factory(
            client_class, client_options=client_options
        )(client)

        self.assertIs(result, client_class.return_value)
        client_class.assert_called_once_with(
            credentials=client._credentials,
            client_info=client_info,
            client_options=client_options,
        )

    def test_w_emulator(self):
        client_class = mock.Mock()
        emulator_host = emulator_channel = object()
        credentials = _make_credentials()
        client = _Client(
            credentials, emulator_host=emulator_host, emulator_channel=emulator_channel
        )
        client_info = client._client_info = mock.Mock()

        result = self._invoke_client_factory(client_class)(client)

        self.assertIs(result, client_class.return_value)
        client_class.assert_called_once_with(
            channel=client._emulator_channel, client_info=client_info
        )


class _Client(object):
    def __init__(self, credentials, emulator_host=None, emulator_channel=None):
        self._credentials = credentials
        self._emulator_host = emulator_host
        self._emulator_channel = emulator_channel


class TestClientConstants:
    PROJECT = "PROJECT"
    INSTANCE_ID = "instance-id"
    DISPLAY_NAME = "display-name"
    USER_AGENT = "you-sir-age-int"


class TestBaseClient(unittest.TestCase, TestClientConstants):
    @staticmethod
    def _get_target_class():
        from google.cloud.bigtable.base_client import BaseClient

        return BaseClient

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def test_constructor_defaults(self):
        from google.cloud.bigtable.base_client import _CLIENT_INFO
        from google.cloud.bigtable.base_client import DATA_SCOPE

        credentials = _make_credentials()

        with mock.patch("google.auth.default") as mocked:
            mocked.return_value = credentials, self.PROJECT
            client = self._make_one()

        self.assertEqual(client.project, self.PROJECT)
        self.assertIs(client._credentials, credentials.with_scopes.return_value)
        self.assertFalse(client._read_only)
        self.assertFalse(client._admin)
        self.assertIs(client._client_info, _CLIENT_INFO)
        self.assertIsNone(client._channel)
        self.assertIsNone(client._emulator_host)
        self.assertIsNone(client._emulator_channel)
        self.assertEqual(client.SCOPE, (DATA_SCOPE,))

    def test_constructor_explicit(self):
        import warnings
        from google.cloud.bigtable.base_client import ADMIN_SCOPE
        from google.cloud.bigtable.base_client import DATA_SCOPE

        credentials = _make_credentials()
        client_info = mock.Mock()

        with warnings.catch_warnings(record=True) as warned:
            client = self._make_one(
                project=self.PROJECT,
                credentials=credentials,
                read_only=False,
                admin=True,
                client_info=client_info,
                channel=mock.sentinel.channel,
            )

        self.assertEqual(len(warned), 1)

        self.assertEqual(client.project, self.PROJECT)
        self.assertIs(client._credentials, credentials.with_scopes.return_value)
        self.assertFalse(client._read_only)
        self.assertTrue(client._admin)
        self.assertIs(client._client_info, client_info)
        self.assertIs(client._channel, mock.sentinel.channel)
        self.assertEqual(client.SCOPE, (DATA_SCOPE, ADMIN_SCOPE))

    def test_constructor_both_admin_and_read_only(self):
        credentials = _make_credentials()
        with self.assertRaises(ValueError):
            self._make_one(
                project=self.PROJECT,
                credentials=credentials,
                admin=True,
                read_only=True,
            )

    def test_constructor_with_emulator_host(self):
        from google.cloud.environment_vars import BIGTABLE_EMULATOR

        credentials = _make_credentials()
        emulator_host = "localhost:8081"
        with mock.patch("os.getenv") as getenv:
            getenv.return_value = emulator_host
            with mock.patch("grpc.insecure_channel") as factory:
                getenv.return_value = emulator_host
                client = self._make_one(project=self.PROJECT, credentials=credentials)

        self.assertEqual(client._emulator_host, emulator_host)
        self.assertIs(client._emulator_channel, factory.return_value)
        factory.assert_called_once_with(emulator_host)
        getenv.assert_called_once_with(BIGTABLE_EMULATOR)

    def test__get_scopes_default(self):
        from google.cloud.bigtable.base_client import DATA_SCOPE

        client = self._make_one(project=self.PROJECT, credentials=_make_credentials())
        self.assertEqual(client._get_scopes(), (DATA_SCOPE,))

    def test__get_scopes_admin(self):
        from google.cloud.bigtable.base_client import ADMIN_SCOPE
        from google.cloud.bigtable.base_client import DATA_SCOPE

        client = self._make_one(
            project=self.PROJECT, credentials=_make_credentials(), admin=True
        )
        expected_scopes = (DATA_SCOPE, ADMIN_SCOPE)
        self.assertEqual(client._get_scopes(), expected_scopes)

    def test__get_scopes_read_only(self):
        from google.cloud.bigtable.base_client import READ_ONLY_SCOPE

        client = self._make_one(
            project=self.PROJECT, credentials=_make_credentials(), read_only=True
        )
        self.assertEqual(client._get_scopes(), (READ_ONLY_SCOPE,))

    def test_project_path_property(self):
        credentials = _make_credentials()
        project = "PROJECT"
        client = self._make_one(project=project, credentials=credentials, admin=True)
        project_name = "projects/" + project
        self.assertEqual(client.project_path, project_name)

    def test_table_data_client_not_initialized(self):
        from google.cloud.bigtable.base_client import _CLIENT_INFO
        from google.cloud.bigtable_v2 import BigtableClient

        credentials = _make_credentials()
        client = self._make_one(project=self.PROJECT, credentials=credentials)

        table_data_client = client.table_data_client
        self.assertIsInstance(table_data_client, BigtableClient)
        self.assertIs(table_data_client._client_info, _CLIENT_INFO)
        self.assertIs(client._table_data_client, table_data_client)

    def test_table_data_client_not_initialized_w_client_info(self):
        from google.cloud.bigtable_v2 import BigtableClient

        credentials = _make_credentials()
        client_info = mock.Mock()
        client = self._make_one(
            project=self.PROJECT, credentials=credentials, client_info=client_info
        )

        table_data_client = client.table_data_client
        self.assertIsInstance(table_data_client, BigtableClient)
        self.assertIs(table_data_client._client_info, client_info)
        self.assertIs(client._table_data_client, table_data_client)

    def test_table_data_client_not_initialized_w_client_options(self):
        credentials = _make_credentials()
        client_options = mock.Mock()
        client = self._make_one(
            project=self.PROJECT, credentials=credentials, client_options=client_options
        )

        patch = mock.patch("google.cloud.bigtable_v2.BigtableClient")
        with patch as mocked:
            table_data_client = client.table_data_client

        self.assertIs(table_data_client, mocked.return_value)
        self.assertIs(client._table_data_client, table_data_client)
        mocked.assert_called_once_with(
            client_info=client._client_info,
            credentials=mock.ANY,  # added scopes
            client_options=client_options,
        )

    def test_table_data_client_initialized(self):
        credentials = _make_credentials()
        client = self._make_one(
            project=self.PROJECT, credentials=credentials, admin=True
        )

        already = client._table_data_client = object()
        self.assertIs(client.table_data_client, already)

    def test_table_admin_client_not_initialized_no_admin_flag(self):
        credentials = _make_credentials()
        client = self._make_one(project=self.PROJECT, credentials=credentials)

        with self.assertRaises(ValueError):
            client.table_admin_client()

    def test_table_admin_client_not_initialized_w_admin_flag(self):
        from google.cloud.bigtable.base_client import _CLIENT_INFO
        from google.cloud.bigtable_admin_v2 import BigtableTableAdminClient

        credentials = _make_credentials()
        client = self._make_one(
            project=self.PROJECT, credentials=credentials, admin=True
        )

        table_admin_client = client.table_admin_client
        self.assertIsInstance(table_admin_client, BigtableTableAdminClient)
        self.assertIs(table_admin_client._client_info, _CLIENT_INFO)
        self.assertIs(client._table_admin_client, table_admin_client)

    def test_table_admin_client_not_initialized_w_client_info(self):
        from google.cloud.bigtable_admin_v2 import BigtableTableAdminClient

        credentials = _make_credentials()
        client_info = mock.Mock()
        client = self._make_one(
            project=self.PROJECT,
            credentials=credentials,
            admin=True,
            client_info=client_info,
        )

        table_admin_client = client.table_admin_client
        self.assertIsInstance(table_admin_client, BigtableTableAdminClient)
        self.assertIs(table_admin_client._client_info, client_info)
        self.assertIs(client._table_admin_client, table_admin_client)

    def test_table_admin_client_not_initialized_w_client_options(self):
        credentials = _make_credentials()
        admin_client_options = mock.Mock()
        client = self._make_one(
            project=self.PROJECT,
            credentials=credentials,
            admin=True,
            admin_client_options=admin_client_options,
        )

        patch = mock.patch("google.cloud.bigtable_admin_v2.BigtableTableAdminClient")
        with patch as mocked:
            table_admin_client = client.table_admin_client

        self.assertIs(table_admin_client, mocked.return_value)
        self.assertIs(client._table_admin_client, table_admin_client)
        mocked.assert_called_once_with(
            client_info=client._client_info,
            credentials=mock.ANY,  # added scopes
            client_options=admin_client_options,
        )

    def test_table_admin_client_initialized(self):
        credentials = _make_credentials()
        client = self._make_one(
            project=self.PROJECT, credentials=credentials, admin=True
        )

        already = client._table_admin_client = object()
        self.assertIs(client.table_admin_client, already)