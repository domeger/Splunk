"""
Tests for the script output functions
"""

import json
import string
from hypothesis import given, assume, Settings
import hypothesis.strategies as strat

from c42api_test import test_lib
from c42api_test.test_lib import WriteTester
from c42api.common import script_output
from c42csv import c42_csv as csv


@given(strat.text(), strat.text(), settings=Settings(max_examples=50))
def test_output_json(random1, random2):
    """Test to make sure the JSON is written out correctly"""
    data = [{'link': 'courage', 'zelda': 'wisdom', 'ganon': 'power', 'num': 3},
            {'random_one': random1, 'random_two': random2}]
    output_file = WriteTester()
    script_output.write_json(output_file, data)
    lines = output_file.lines()
    assert len(lines) == 5
    assert json.loads(''.join(lines))
    assert lines[0] == '[\n'
    assert lines[2] == ',\n'
    assert lines[4] == '\n]\n'
    dict1 = json.loads(lines[1])
    dict2 = json.loads(lines[3])
    assert dict1['link'] == 'courage'
    assert dict1['zelda'] == 'wisdom'
    assert dict1['ganon'] == 'power'
    assert dict1['num'] == 3
    assert dict2['random_one'] == random1
    assert dict2['random_two'] == random2


def test_output_no_json():
    """Test writing empty JSON"""
    data = {}
    output_file = WriteTester()
    script_output.write_json(output_file, data)
    lines = output_file.lines()
    assert len(lines) == 2
    assert lines[0] == '[\n'
    assert lines[1] == '\n]\n'


@given(strat.text(), strat.text(), settings=Settings(max_examples=50))
def test_output_json_splunk(random1, random2):
    """Test to make sure the 'splunk' JSON is written out correctly"""
    data = [{'link': 'courage', 'zelda': 'wisdom', 'ganon': 'power', 'num': 3},
            {'random_one': random1, 'random_two': random2}]
    output_file = WriteTester()
    script_output.write_json_splunk(output_file, data)
    lines = output_file.lines()
    assert len(lines) == 2
    dict1 = json.loads(lines[0])
    dict2 = json.loads(lines[1])
    assert dict1['link'] == 'courage'
    assert dict1['zelda'] == 'wisdom'
    assert dict1['ganon'] == 'power'
    assert dict1['num'] == 3
    assert dict2['random_one'] == random1
    assert dict2['random_two'] == random2


def test_output_no_json_splunk():
    """Test writing empty 'splunk' JSON"""
    data = []
    output_file = WriteTester()
    script_output.write_json_splunk(output_file, data)
    lines = output_file.lines()
    assert len(lines) == 0


@given(strat.text(), strat.text(), settings=Settings(max_examples=50))
def test_output_csv(random1, random2):
    """Test to make sure CSV is written out correctly"""
    assume(all(substring not in random_str
               for substring in [',', '"', '\n', '\r']
               for random_str in [random1, random2]))
    data = [{'link': 'courage', 'zelda': 'wisdom', 'ganon': 'power', 'num': 3},
            {'ganon': random1, 'link': random2}]
    output_file = WriteTester()
    script_output.write_csv(output_file, data, header=True)
    lines = output_file.lines()
    assert len(lines) == 3
    assert lines[0].split(',') == ['ganon', 'link', 'num', 'zelda\n']
    assert lines[1].split(',') == ['power', 'courage', str(3), 'wisdom\n']
    assert lines[2].split(',') == [random1.encode('UTF-8'), random2.encode('UTF-8'), '', '\n']


@given(strat.text(), strat.text(), settings=Settings(max_examples=50))
def test_output_csv_no_header(random1, random2):
    """
    Test to make sure the computers CSV is written out correctly, with no header.
    """
    assume(all(substring not in random_str
               for substring in [',', '"', '\n', '\r']
               for random_str in [random1, random2]))
    data = [{'link': 'courage', 'zelda': 'wisdom', 'ganon': 'power', 'num': 3},
            {'ganon': random1, 'link': random2}]
    output_file = WriteTester()
    script_output.write_csv(output_file, data, header=False)
    lines = output_file.lines()
    assert len(lines) == 2
    assert lines[0].split(',') == ['power', 'courage', str(3), 'wisdom\n']
    assert lines[1].split(',') == [random1.encode('UTF-8'), random2.encode('UTF-8'), '', '\n']


@given(strat.text(), strat.text(), settings=Settings(max_examples=50))
def test_output_csv_special_char(random1, random2):
    """
    Test to check the behavior of printing out special characters to CSV.
    Special characters are '\n', '\r', '"', and ','.
    """
    assume(random1)
    assume(random2)
    data = [{'special': random1 + ',' + random2},
            {'special': random1 + '\n' + random2},
            {'special': random1 + '\r' + random2},
            {'special': random1 + '"' + random2}]
    output_file = WriteTester()
    script_output.write_csv(output_file, data)
    lines = output_file.lines()
    assert len(lines) == 4
    for line in lines:
        assert line.endswith('\n')
        test_str = line[:-1]
        assert test_str.startswith('"')
        assert test_str.endswith('"')
    quote_line = lines[3][:-1]
    before_replacement = random1 + '"' + random2
    assert quote_line.count('"') == before_replacement.count('"') * 2 + 2


@given(strat.text(alphabet=list(string.ascii_lowercase)), settings=Settings(max_examples=50))
def test_output_csv_shallow(random_str):
    """
    Test to verify a shallow parse works.
    """
    assume(random_str)
    assume(all(substring not in random_str
               for substring in [',', '"', '\n', '\r']))
    sub_dict = {'meow': random_str}
    data = [{'test': sub_dict}]

    output_file = WriteTester()
    script_output.write_csv(output_file, data, header=True, shallow=True)
    lines = output_file.lines()
    assert len(lines) == 2
    assert lines[0] == 'test\n'
    assert lines[1].startswith('"{""meow"": ')
    test_str = lines[1].split(':')[1]
    assert random_str in test_str
    assert lines[1].endswith('"\n')


def test_output_csv_given_keyset():
    """
    Test that a csv write works when a KeySet is provided ahead of time.
    """
    key_set = csv.KeySet()
    sub_dict = {'meow': 'cat'}
    data_dict = {'test': sub_dict}
    for key, value in data_dict.items():
        json_key = csv.create_key(key, value, shallow=True)
        key_set.add_key(json_key)
    data = [data_dict]
    output_file = WriteTester()
    script_output.write_csv(output_file, data, header=False, shallow=True, keyset=key_set)
    lines = output_file.lines()
    assert len(lines) == 1
    assert lines[0] == '"{""meow"": ""cat""}"\n'


def test_output_csv_no_data():
    """Test CSV written from no data"""
    data = []
    output_file = WriteTester()
    script_output.write_csv(output_file, data, header=False)
    lines = output_file.lines()
    assert len(lines) == 0


if __name__ == '__main__':
    test_lib.run_all_tests()
