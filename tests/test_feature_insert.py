import pytest
import json
import unittest
import os
import tempfile
import urllib.request
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from infra_ai_service.core.app import get_app
from infra_ai_service.config.config import settings
from infra_ai_service.service.extract_spec import (
    extract_spec_features,
    _decompress_src_rpm,
    _get_tar_cmd,
    _decompress_tar_file,
    _process_binarylist,
    check_xml_info,
)
import infra_ai_service.service.extract_spec as es

app = get_app()


class TestFeatureInsert(unittest.TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    @pytest.mark.asyncio
    async def test_feature_insert_with_bad_url(self):

        base_url = f'http://localhost:{settings.PORT}/'
        async with AsyncClient(app=app, base_url=base_url) as ac:
            headers = {
                'Content-Type': 'application/json'
            }
            data = {
                'src_rpm_url': 'https://example.com/test-package.src.rpm2',
                'os_version': 'openEuler-24.03',
            }
            resp = await ac.post(
                '/api/v1/feature-insert/',
                headers=headers,
                data=json.dumps(data))
            content = json.loads(resp._content.decode())

            self.assertEqual(resp.status_code, 200)
            self.assertIn('error', content)
            self.assertIn('url of src.rpm may be wrong', content)

            data = {
                'src_rpm_url': 'https://example.com/test-package.src.rpm',
                'os_version': 'openEuler-24.03',
            }
            resp = await ac.post(
                '/api/v1/feature-insert/',
                headers=headers,
                data=json.dumps(data))
            content = json.loads(resp._content.decode())

            self.assertEqual(resp.status_code, 200)
            self.assertIn('error', content)
            self.assertIn('download src.rpm fail', content)

    def test_decompress_src_rpm_fail(self):
        with tempfile.TemporaryDirectory() as src_rpm_dir:
            src_rpm_path = os.path.join(src_rpm_dir, 'tmp.src.rpm')
            with open(src_rpm_path, 'w') as f:
                f.write('This is a simulated .src.rpm package.\n')

            try:
                _decompress_src_rpm(src_rpm_path)
            except Exception as e:
                prefix = str(e)[:23]
                self.assertEqual('decompress src.rpm fail', prefix)

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_get_tar_cmd(self, mock_makedirs, mock_exists):
        mock_exists.return_value = True
        tar_path = '/path/tmp.tar.gz'
        dst_path = '/path/'
        res = {
            '.tar.gz': f'tar -xzf {tar_path} -C {dst_path}',
            '.tgz': f'tar -xzf {tar_path} -C {dst_path}',
            '.tar.bz2': f'tar -xjf {tar_path} -C {dst_path}',
            '.tar.xz': f'tar -xJf {tar_path} -C {dst_path}',
            '.zip': f'unzip {tar_path} -d {dst_path}'
        }
        for k, v in res.items():
            cmd = _get_tar_cmd(k, tar_path, dst_path)
            self.assertEqual(cmd, v)

    @patch('os.makedirs')
    def test_decompress_tar_file_fail(self, mock_makedirs):
        with tempfile.TemporaryDirectory() as tar_dir:
            src_dir = os.path.join(tar_dir, 'src')
            os.makedirs(src_dir)
            src_rpm_path = os.path.join(tar_dir, 'tmp.tar.gz')
            with open(src_rpm_path, 'w') as f:
                f.write('This is a simulated .tar.gz package.\n')

            try:
                _decompress_tar_file(tar_dir)
            except Exception as e:
                prefix = str(e)[:25]
                self.assertEqual('decompress tar file error', prefix)

    def _create_spec_content(slef):
        return (
            'Name:           python-bunch\nVersion:        1.0.1\n'
            'Release:        3\nSummary:        A dot-accessible dictionary '
            '(a la JavaScript objects)\n'
            'License:        MIT\nURL:        http://github.com/dsc/bunch\n'
            'Source0:        https://pythonhosted.org/bunch-1.0.1.zip\n'
            'BuildArch:      noarch\n%description\nBunch is a dictionary that '
            'supports attribute-style access, a la JavaScript.\n\n'
            '%package -n python3-bunch\n'
            'Summary:  A dot-accessible dictionary (a la JavaScript objects)\n'
            'Provides:       python-bunch\n# Base build requires\n'
            'BuildRequires:  python3-devel\n'
            'BuildRequires:  python3-setuptools\n'
            'BuildRequires:  python3-pbr\nBuildRequires:  python3-pip\n'
            'BuildRequires:  python3-wheel\n%description -n python3-bunch\n'
            'Bunch is a dictionary that supports attribute-style access, '
            'a la JavaScript.\n\n%package help\n'
            'Summary:        A dot-accessible dictionary '
            '(a la JavaScript objects)\nProvides:       python3-bunch-doc\n'
            '%description help\nBunch is a dictionary that supports '
            'attribute-style access, a la JavaScript.\n'
            '%prep\n%autosetup -n bunch-1.0.1 -p1\n%build\n%py3_build\n'
            '%install\n%py3_install\n%files -n python3-bunch -f filelist.lst\n'
            '%dir %{python3_sitelib}/*\n%files help -f doclist.lst\n'
            '%{_docdir}/*\n\n%changelog\n'
            '* Thu Sep 30 2024 bot <bot@gmail.com> - 1.0.1-3\n'
            '- DESC: fix conflict with bunch\n'
        )

    def test_extract_spec_features(self):
        es.XML_INFO = {
            1: {
                'description': 'Best practices checker for Ansible',
                'name': 'ansible-lint',
                'requires': []
            },
            3: {
                'description': 'A dot-accessible dictionary',
                'name': 'bunch',
                'version': '1.0.1',
                'url': 'http://github.com/dsc/bunch'
            }
        }
        with tempfile.TemporaryDirectory() as dir_path:
            spec_path = os.path.join(dir_path, 'bunch.spec')
            with open(spec_path, 'w', encoding='utf-8') as f:
                f.write(self._create_spec_content())

            data = extract_spec_features(dir_path)
            expected_data = {
                1: {
                    'binaryList': [
                        'python-bunch',
                        'python3-bunch',
                        'python-bunch-help'],
                    'buildRequires': [
                        'python3-dev',
                        'python3-pbr',
                        'python3-pip',
                        'python3-setuptools',
                        'python3-wheel'],
                    'description': 'A dot-accessible dictionary',
                    'name': 'bunch',
                    'provides': [
                        'python-bunch',
                        'python3-bunch',
                        'python-bunch-help',
                        'python3-bunch-doc'],
                    'source0': 'https://pythonhosted.org/bunch-1.0.1.zip',
                    'url': 'http://github.com/dsc/bunch',
                    'version': '1.0.1'
                }
            }
            self.assertEqual(data, expected_data)

    def test_process_binarylist(self):
        binary_list = ['test1-123', 'test2-2.2.2-3', 'test3-2.4.3.src']
        res = {}
        _process_binarylist(binary_list, res)
        self.assertIn('test1', res['binaryList'])
        self.assertIn('test2', res['binaryList'])
        self.assertIn('test3', res['binaryList'])

    def _create_xml_content(slef):
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<metadata xmlns="http://linux.duke.edu/metadata/common" '
            'xmlns:rpm="http://linux.duke.edu/metadata/rpm" '
            'packages="1024">\n'
            '<package type="rpm">\n<name>ansible-lint</name>\n'
            '<arch>noarch</arch>\n'
            '<version epoch="0" ver="4.2.0" rel="3.oe2403"/>\n'
            '<checksum type="sha256" pkgid="YES">f08be97d</checksum>\n'
            '<summary>Best practices checker for Ansible</summary>\n'
            '<description>Best practices checker for Ansible</description>\n'
            '<packager>http://openeuler.org</packager>\n'
            '<url>https://github.com/ansible/ansible-lint</url>\n'
            '<time file="1716988656" build="1716362886"/>\n'
            '<size package="106369" installed="331780" archive="0"/>\n'
            '<location href="Packages/ansible-lint-4.2.0-3.oe2403.'
            'noarch.rpm"/>\n'
            '<format>\n'
            '<rpm:license>Apache-2.0</rpm:license>\n'
            '<rpm:vendor></rpm:vendor>\n'
            '<rpm:group>Unspecified</rpm:group>\n'
            '<rpm:buildhost>dc-64g.compass-ci</rpm:buildhost>\n'
            '<rpm:sourcerpm>ansible-lint-4.2.0-3.oe2403.src.rpm'
            '</rpm:sourcerpm>\n'
            '<rpm:header-range start="768" end="24901"/>\n'
            '<rpm:provides>\n'
            '<rpm:entry name="ansible-lint" flags="EQ" epoch="0" '
            'ver="4.2.0" rel="3.oe2403"/>\n'
            '<rpm:entry name="python3.11dist(ansible-lint)" flags='
            '"EQ" epoch="0" ver="4.2"/>\n'
            '<rpm:entry name="python3dist(ansible-lint)" flags="EQ" '
            'epoch="0" ver="4.2"/>\n'
            '</rpm:provides>\n'
            '<rpm:requires>\n'
            '<rpm:entry name="/usr/bin/python3"/>\n'
            '<rpm:entry name="ansible" flags="GE" epoch="0" ver="2.8"/>\n'
            '<rpm:entry name="python(abi)" flags="EQ" epoch="0" '
            'ver="3.11"/>\n'
            '<rpm:entry name="python3-pyyaml"/>\n'
            '<rpm:entry name="python3-ruamel-yaml" flags="GE" epoch="0" '
            'ver="0.15.34"/>\n'
            '<rpm:entry name="python3-setuptools_scm"/>\n'
            '<rpm:entry name="python3-six"/>\n'
            '<rpm:entry name="python3-typing-extensions"/>\n'
            '<rpm:entry name="python3.11dist(ansible)" flags="GE" '
            'epoch="0" ver="2.7"/>\n'
            '<rpm:entry name="python3.11dist(pyyaml)"/>\n'
            '<rpm:entry name="python3.11dist(ruamel.yaml)" flags="GE" '
            'epoch="0" ver="0.15.37"/>\n'
            '<rpm:entry name="python3.11dist(ruamel.yaml)" flags="LT" '
            'epoch="0" ver="1"/>\n'
            '<rpm:entry name="python3.11dist(setuptools)"/>\n'
            '<rpm:entry name="python3.11dist(six)"/>\n'
            '</rpm:requires>\n'
            '<file>/etc/ima/digest_lists.tlv/0-metadata_list-compact'
            '_tlv-ansible-lint-4.2.0-3.oe2403.noarch</file>\n'
            '<file>/etc/ima/digest_lists/0-metadata_list-compact-'
            'ansible-lint-4.2.0-3.oe2403.noarch</file>\n'
            '<file>/usr/bin/ansible-lint</file>\n'
            '</format>\n'
            '</package>\n'
            '</metadata>\n'
        )

    @patch('urllib.request.urlretrieve')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=MagicMock)
    @patch('subprocess.run')
    def test_extract_xml_features(self,
                                  mock_run,
                                  mock_open,
                                  mock_exists,
                                  mock_urlretrieve):
        TEST_XML_URL = 'http://example.com/primary.xml.zst'
        TEST_OS_VERSION = 'test_os_version'
        mock_open.return_value.__enter__.return_value.read.return_value = \
            self._create_xml_content()
        mock_urlretrieve.return_value = ('download success', {})
        mock_run.return_value = MagicMock(returncode=0, stdout=None, stderr=None)

        result = check_xml_info(TEST_XML_URL, TEST_OS_VERSION)

        xml_expected = {
            1: {
                'description': 'Best practices checker for Ansible',
                'name': 'ansible-lint',
                'requires': [
                    'ansible',
                    'python(abi)',
                    'python3-pyyaml',
                    'python3-ruamel-yaml',
                    'python3-setuptools_scm',
                    'python3-six',
                    'python3-typing-extensions',
                    'python3.11dist(ansible)',
                    'python3.11dist(pyyaml)',
                    'python3.11dist(ruamel.yaml)',
                    'python3.11dist(ruamel.yaml)',
                    'python3.11dist(setuptools)',
                    'python3.11dist(six)'],
                'summary': 'Best practices checker for Ansible',
                'url': 'https://github.com/ansible/ansible-lint',
                'version': '4.2'
            },
            'os_version': 'test_os_version'
        }

        self.assertEqual(result, xml_expected)
