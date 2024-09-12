#!/usr/bin/python3

import json


def get_and_check_name(info: dict):
    try:
        return info['name']
    except Exception as e:
        # TODO: log the exception
        pass


def _update_json(xml, spec):
    res = {}
    all_keys = set(xml.keys()).union(set(spec.keys()))
    for key in all_keys:
        if key in xml and key in spec:
            if isinstance(spec[key], list):  # dont process other type
                spec[key] = list(set(spec[key] + xml[key]))

        elif key in xml:
            res[key] = xml[key]
        else:
            res[key] = spec[key]

    return res


def update_json(j_xml: dict, j_spec: dict):
    '''
    The API /feature-insert/ only process one spec, so the j_spec
    must be one length.
    '''
    spec_info = j_spec[1]
    spec_name = get_and_check_name(spec_info)

    for i, info in j_xml:
        xml_name = get_and_check_name(info)
        if xml_name == spec_name:
            j_spec[1] = _update_json(info, spec_info)

    return j_spec


def write_json(file, data):
    '''
    maybe self-test only
    '''
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
