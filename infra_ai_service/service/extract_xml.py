#!/usr/bin/python3

import xml.etree.ElementTree as ET


def _get_tag_name(tag: str):
    return tag.split('}')[-1]


def _process_func_common(data_cnt: dict, info: ET.Element):
    '''
    process for name, summary, description, url
    '''
    tag_name = _get_tag_name(info.tag)
    data_cnt[tag_name] = info.text.strip() if info.text else ''
    if tag_name == 'description' and data_cnt[tag_name] == '.':
        data_cnt[tag_name] = ''


def _process_func_version(data_cnt: dict, info: ET.Element):
    tag_name = _get_tag_name(info.tag)
    ver = info.get('ver', '').strip()
    pos = ver.rfind('.')
    if pos != -1:
        ver = ver[0:pos]
    data_cnt[tag_name] = ver


def _process_func_requires(data_cnt: dict, info: ET.Element):
    for ft in info:  # process element in format
        tag_name = _get_tag_name(ft.tag)
        if tag_name == 'requires':
            if not data_cnt.get(tag_name, None):
                data_cnt[tag_name] = []
            for entry in ft:  # process element in requires
                require = entry.get('name')
                if require.startswith('/'):
                    continue
                if require.find('>') != -1:
                    data_cnt[tag_name].append(require.split('>')[0].strip())
                elif require.find('>=') != -1:
                    data_cnt[tag_name].append(require.split('>=')[0].strip())
                else:
                    data_cnt[tag_name].append(require)

    # if there's no requires info in format, add [] to it
    if not data_cnt.get('requires', None):
        data_cnt['requires'] = []


def _get_func_with_name(name: str):
    process_func = {
        'name': _process_func_common,
        'version': _process_func_version,
        'summary': _process_func_common,
        'description': _process_func_common,
        'url': _process_func_common,
        'format': _process_func_requires,
    }
    return process_func.get(name, None)


def extract_xml_features(content: str):
    try:
        metadata = ET.fromstring(content)
        res = {}
        count = 1
        for package in metadata:
            if _get_tag_name(package.tag) != 'package':
                continue

            if not res.get(count, None):
                res[count] = {}

            for info in package:
                tag_name = _get_tag_name(info.tag)
                tag_func = _get_func_with_name(tag_name)
                if tag_func:
                    tag_func(res[count], info)

            count += 1

        return res
    except Exception as e:
        raise Exception(f'process xml error: {e}')
