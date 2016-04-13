# Copyright (c) 2015 - 2016 Code42 Software, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for the Splunk lookup table functions
"""
# pylint: disable=invalid-name, import-error

import os
import tempfile

from c42api_test import test_lib
from splunk_utils import splunk_lookup_table


def test_temp_file_removed():
    """
    Test that the temp file does not exist after the lookup table is written.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    os.remove(old_lookup_table)


def test_old_file_not_overwritten():
    """
    Test that if no data is returned from the API call, the old lookup table
    remains the same.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    with open(old_lookup_table, 'w') as out:
        out.write("this is only a test")
    data = []
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    with open(old_lookup_table, 'r') as old:
        for line in old:
            assert line == "this is only a test"
    os.remove(old_lookup_table)


def test_new_lookup_table():
    """
    Test with no old lookup table. Simple verify of json written to the
    new lookup table.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    with open(old_lookup_table, 'r') as new:
        lines = new.readlines()
        assert len(lines) == 2
        assert lines[0].split(',') == ['first', 'id', 'last\n']
        assert lines[1].split(',') == ['nick', '12345', 'wallin\n']
    os.remove(old_lookup_table)


def test_add_to_old_lookup_table():
    """
    Test with an already-existing lookup table. Verify new rows are written
    to the lookup table.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    new_tmp_table = os.path.join(tmpdir, 'tmp.csv')
    new_data = [{'first': 'carl', 'last': 'benson', 'id': '11223'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, new_tmp_table, new_data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(new_tmp_table)
    with open(old_lookup_table, 'r') as new:
        lines = new.readlines()
        assert len(lines) == 3
        assert lines[0].split(',') == ['first', 'id', 'last\n']
        assert lines[1].split(',') == ['nick', '12345', 'wallin\n']
        assert lines[2].split(',') == ['carl', '11223', 'benson\n']
    os.remove(old_lookup_table)


def test_add_to_old_lookup_hash():
    """
    Test with an already-existing lookup table. Verify new rows with same hash
    are not written to the lookup table.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    new_tmp_table = os.path.join(tmpdir, 'tmp.csv')
    new_data = [{'first': 'nick', 'last': 'wallin', 'id': '12345'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, new_tmp_table, new_data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(new_tmp_table)
    with open(old_lookup_table, 'r') as new:
        lines = new.readlines()
        assert len(lines) == 2
        assert lines[0].split(',') == ['first', 'id', 'last\n']
        assert lines[1].split(',') == ['nick', '12345', 'wallin\n']
    os.remove(old_lookup_table)


def test_add_to_old_lookup_hash_ignore():
    """
    Test with an already-existing lookup table. Verify new rows with same hash
    are not written to the lookup table. Also ignore some keys when calculating
    the hash, to test that.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345', 'time': 'now'}]
    ignore_keys = ['time']
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', ignore_keys)
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    new_tmp_table = os.path.join(tmpdir, 'tmp.csv')
    new_data = [{'first': 'nick', 'last': 'wallin', 'id': '12345', 'time': 'later'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, new_tmp_table, new_data, 'id', ignore_keys)
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(new_tmp_table)
    with open(old_lookup_table, 'r') as new:
        lines = new.readlines()
        assert len(lines) == 2
        assert lines[0].split(',') == ['first', 'id', 'last', 'time\n']
        assert lines[1].split(',') == ['nick', '12345', 'wallin', 'now\n']
    os.remove(old_lookup_table)


def test_add_old_lookup_extra_column_json():
    """
    Test adding a row to the lookup table, when there's a new column in the
    json data that isn't already in the lookup table.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    new_tmp_table = os.path.join(tmpdir, 'tmp.csv')
    new_data = [{'first': 'nick', 'last': 'wallin', 'id': '12345', 'time': 'now'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, new_tmp_table, new_data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(new_tmp_table)
    with open(old_lookup_table, 'r') as new:
        lines = new.readlines()
        assert len(lines) == 3
        assert lines[0].split(',') == ['first', 'id', 'last', 'time\n']
        assert lines[1].split(',') == ['nick', '12345', 'wallin', '\n']
        assert lines[2].split(',') == ['nick', '12345', 'wallin', 'now\n']
    os.remove(old_lookup_table)


def test_add_old_lookup_extra_column_lookup():
    """
    Test adding a row to the lookup table, when there's a column in the old
    lookup table that isn't in the json data
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345', 'time': 'now'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    new_tmp_table = os.path.join(tmpdir, 'tmp.csv')
    new_data = [{'first': 'nick', 'last': 'wallin', 'id': '12345'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, new_tmp_table, new_data, 'id', [])
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(new_tmp_table)
    with open(old_lookup_table, 'r') as new:
        lines = new.readlines()
        assert len(lines) == 3
        assert lines[0].split(',') == ['first', 'id', 'last', 'time\n']
        assert lines[1].split(',') == ['nick', '12345', 'wallin', 'now\n']
        assert lines[2].split(',') == ['nick', '12345', 'wallin', '\n']
    os.remove(old_lookup_table)


def test_initial_lookup_time():
    """
    Test that when a lookup table is made for the first time, and a time key
    is provided, that the times are modified as we expect.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345', 'time': '2015-08-27'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [], 'time')
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    with open(old_lookup_table, 'r') as new:
        lines = new.readlines()
        assert len(lines) == 2
        assert lines[0].split(',') == ['first', 'id', 'last', 'time\n']
        assert lines[1].split(',') == ['nick', '12345', 'wallin', '2000-01-01T00:01:01.000-00:00\n']
    os.remove(old_lookup_table)


def test_initial_lookup_time_extra_rows():
    """
    Test that when a lookup table is made for the first time, and a time key
    is provided, that the times are modified as we expect, and later-added
    rows are NOT modified.
    """
    tmpdir = tempfile.gettempdir()
    old_lookup_table = os.path.join(tmpdir, 'old.csv')
    tmp_lookup_table = os.path.join(tmpdir, 'tmp.csv')
    data = [{'first': 'nick', 'last': 'wallin', 'id': '12345', 'time': '2015-08-27'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, tmp_lookup_table, data, 'id', [], 'time')
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(tmp_lookup_table)
    new_tmp_table = os.path.join(tmpdir, 'tmp.csv')
    new_data = [{'first': 'nick', 'last': 'james', 'id': '12345', 'time': '2015-08-27'}]
    splunk_lookup_table.write_lookup_table(old_lookup_table, new_tmp_table, new_data, 'id', [], 'time')
    assert os.path.exists(old_lookup_table)
    assert not os.path.exists(new_tmp_table)
    with open(old_lookup_table, 'r') as new:
        lines = new.readlines()
        assert len(lines) == 3
        assert lines[0].split(',') == ['first', 'id', 'last', 'time\n']
        assert lines[1].split(',') == ['nick', '12345', 'wallin', '2000-01-01T00:01:01.000-00:00\n']
        assert lines[2].split(',') == ['nick', '12345', 'james', '2015-08-27\n']
    os.remove(old_lookup_table)

if __name__ == '__main__':
    test_lib.run_all_tests()
