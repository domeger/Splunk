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
A module with common functions for writing Splunk lookup tables.
"""

# pylint: disable=import-error, relative-import
import os
import shutil
import csv as pycsv

from c42api.common import script_common
from c42api.common import script_output
from c42csv import c42_csv as csv


def write_lookup_table(old_path, tmp_path, json_list, uid_key, keys_to_ignore, time_key=None):
    # pylint: disable=too-many-arguments
    """
    Write a Splunk lookup table. Will overwrite an already-existing lookup
    table, by reading the already-existing lookup table and writing to a temp
    lookup table, and then overwriting the already-existing with the temp.

    New rows will only be added to the lookup table if they have a different
    hash value than already-existing rows in the lookup table.
    :param old_path:       Path to old lookup table. If no lookup table already
                            exists, this is the path to where the final lookup
                            table should go.
    :param tmp_path:       Path to the temporary lookup table.
    :param json_list:      List of json objects from an API call to write to
                            the lookup table.
    :param uid_key:        The key in the json dictionary pointing to the
                            object's unique identifier.
    :param keys_to_ignore: List of keys to ignore when hashing the row
                            dictionaries.
    :param time_key:       The key in the json dictionary pointing to the
                            object's time value, used by the lookup table.
    """

    def hash_in_map(hash_to_check, hash_map, uid):
        """
        Check whether the given hash is in the given hash map.

        :param hash_to_check: The hash to look for in the hash map.
        :param hash_map:      The hash map to look for the hash in.
        :param uid:           The uid key of the hash map.
        :return:              True if hash in map, otherwise False
        """
        try:
            return hash_to_check in hash_map[uid]
        except KeyError:
            return False

    def add_hash_to_map(hash_to_add, hash_map, uid):
        """
        Add the given hash to the given hash map.

        :param hash_to_add: The hash to add to the map.
        :param hash_map:    The hash map to add the key to.
        :param uid:         The uid key of the hash map to add the hash to.
        """
        if uid in hash_map:
            hash_set = hash_map[uid]
            hash_set.add(hash_to_add)
        else:
            hash_map[uid] = {hash_to_add}

    def hash_dictionary(dict_to_hash):
        """
        Return the hash value of a dictionary, ignoring given keys when hashing.

        :param dict_to_hash: The dictionary to hash
        :return:             A hash value of the dictionary
        """
        prime = 31
        result = 1
        for key, value in dict_to_hash.items():
            if key in keys_to_ignore:
                continue
            try:
                result = prime * result + hash(value)
            except TypeError:
                continue
        return result

    def write_lookup_row(out, json_dict, key_set, hash_map):
        """
        Write a row to the given lookup table if it should (based on hashes).

        :param out:       File handle to the lookup table to write to.
        :param json_dict: The json dictionary to write as a lookup talbe row.
        :param key_set:   KeySet object used to write the dictionary.
        :param hash_map:  Hash map to check to see if the row should be
                           written.
        """
        json_hash = hash_dictionary(json_dict)
        uid = json_dict[uid_key]
        if not hash_in_map(json_hash, hash_map, uid):
            script_output.write_csv(out, [json_dict], header=False, shallow=True, keyset=key_set)
            add_hash_to_map(json_hash, hash_map, uid)

    def _run():
        """
        Run the function.
        """
        with script_common.smart_open(tmp_path) as tmp:
            key_set = csv.KeySet()
            hash_map = {}
            wrote_header = False
            modify_time = False
            for json_dict in json_list:
                if not key_set:
                    for key, value in json_dict.items():
                        json_key = csv.create_key(key, value, shallow=True)
                        key_set.add_key(json_key)
                    try:
                        with open(old_path, 'r') as old:
                            first = True
                            reader = pycsv.DictReader(old)
                            for row in reader:
                                if first:
                                    for key, value in row.items():
                                        json_key = csv.create_key(key, value, shallow=True)
                                        key_set.add_key(json_key)
                                    script_output.write_header_from_keyset(key_set, tmp)
                                    wrote_header = True
                                    first = False
                                write_lookup_row(tmp, row, key_set, hash_map)
                    except IOError:
                        modify_time = time_key or modify_time
                if not wrote_header:
                    script_output.write_header_from_keyset(key_set, tmp)
                    wrote_header = True
                if modify_time:
                    json_dict[time_key] = "2000-01-01T00:01:01.000-00:00"
                write_lookup_row(tmp, json_dict, key_set, hash_map)
        if os.path.exists(old_path) and key_set:
            os.remove(old_path)
        if key_set:
            shutil.move(tmp_path, old_path)
        else:
            os.remove(tmp_path)

    _run()
