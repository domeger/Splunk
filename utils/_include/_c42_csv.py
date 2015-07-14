# File: _c42_csv.py
# Author: Nick Wallin
# Author: Carl Benson
# Last Modified: 06/17/2015
#
# Base class for parsing complex Python objects into a CSV output
# format.
#

# KeySet and Key classes courtesy of Carl Benson

class KeySet:
    """KeySet behaves like a set of Keys that merges appropriately
    and as expected. It's represented internally by a dictionary of
    keys to Keys so when a potentially new key is added it merges the
    old key with it if need be. It also supports a union operator
    which generates a new KeySet with all keys appropriately merged.
    """
    def __init__(self):
        self.keys = dict()

    def add_key(self, newKey):
        """Add a Key object to this KetSet. Will attempt to merge
        subkeys with the same Key.key

        Keyword arguments:
        newKey -- the Key object to add
        """
        try:
            val = self.keys[newKey.key]
            newKey.merge_keys(val)
            val = newKey
        except KeyError:
            val = newKey
        self.keys[newKey.key] = val

    def union(self, other):
        """Combine this KeySet with another KeySet and return it.

        Keyword arguments:
        other -- KeySet object to merge with this one
        """
        new_set = KeySet()
        for key, value in self.keys.items():
            new_set.add_key(value)
        for key, value in other.keys.items():
            new_set.add_key(value)
        return new_set

    def all_keys(self):
        """Return a sorted list of subkey Key objects"""
        sorted_keys = sorted(self.keys.keys())
        for key in sorted_keys:
            yield self.keys[key]

    def count(self):
        """Return count of subkey Key objects"""
        return len(list(self.keys.keys()))


class Key:
    def __init__(self):
        self.key = ""
        self.subkeys = KeySet()

    def __init__(self, keystring):
        self.key = keystring
        self.subkeys = KeySet()

    def add_subkey(self, json_key):
        """Add Key object to subkey KeySet

        Keyword arguments:
        json_key -- Key object to add to subkey KeySet
        """
        self.subkeys.add_key(json_key)

    def merge_keys(self, other):
        """If the given Key object has the same key, add that Key's
        subkeys to this Key object.

        Keyword arguments:
        other -- Key object from which to add subkeys
        """
        if self.key != other.key:
            return
        self.subkeys = self.subkeys.union(other.subkeys)


def _print_key_hierarchy(key, depth=0):
    """DEBUG: print the given Key object's key and each of its
    subkeys (one key per line). Hierarchy shown with indentation.

    Keyword arguments:
    key -- Key object to print the key hierarchy for.
    """
    print(" "*depth + key.key)
    for subkey in key.subkeys.all_keys():
        print_key_hierarchy(subkey, depth + 1)


def _print_flattened_keys(key, prefix=""):
    """DEBUG: print out each of the 'flattened' keys. For example, if
    there is a key FILE with subkeys SIZE and PATH, there would be two
    flattened keys: FILE_SIZE and FILE_PATH. Each would be printed on a
    separate line.

    Keyword arguments:
    key -- Key object to print the 'flattened' keys for.
    """
    if key.subkeys.count() == 0:
        if len(prefix) == 0:
            print(key.key)
        else:
            print(prefix + "_" + key.key)
    else:
        for subkey in key.subkeys.all_keys():
            if len(prefix) == 0:
                print_flattened_keys(subkey, key.key)
            else:
                print_flattened_keys(subkey, prefix + "_" + key.key)


def flattened_keys(key, working_list, prefix=""):
    """Return a list of the 'flattened' keys. For example, if
    there is a key FILE with subkeys SIZE and PATH, there would be two
    flattened keys: FILE_SIZE and FILE_PATH.

    Keyword arguments:
    key -- Key object to print the 'flattened' keys for.
    """
    if key.subkeys.count() == 0:
        if len(prefix) == 0:
            working_list.append(key.key)
        else:
            working_list.append(prefix + "_" + key.key)
    else:
        for subkey in key.subkeys.all_keys():
            if len(prefix) == 0:
                working_list = flattened_keys(subkey, working_list, key.key)
            else:
                working_list = flattened_keys(subkey, working_list, prefix + "_" + key.key)
    return working_list


def create_key(parent_key, child_value):
    """Create a Key object from a given key string and its associated
    value (can be a scalar, dict, or list).

    Keyword arguments:
    parent_key -- string of key
    child_value -- value associated with parent_key. If the value is a
    dictionary or list, they will be iterated over and subkeys Key
    objects will automatically be created.
    """
    parent = Key(parent_key)
    if isinstance(child_value, dict):
        for key, value in child_value.items():
            parent.add_subkey(create_key(key, value))
    elif isinstance(child_value, list):
        for item in child_value:
            if isinstance(item, dict):
                temp_key = create_key(parent_key, item)
                parent.merge_keys(temp_key)
    return parent


def dict_contains_array(dict):
    """Return the length of the list in the given dictionary, or -1 if
    there is no list in the dictionary.

    Keyword arguments:
    dict -- dictionary to check for the presence of a single list
    """
    list_length = -1
    for key in dict:
        if isinstance(dict[key], list):
            return len(dict[key])
    return list_length


def dict_into_values(json_dict, key_try, array_index=0):
    """Return a list of the values contained in the given dictionary.

    Keyword arguments:
    json_dict -- dictionary to make a list of values for
    key_try -- the Key object to try accessing in the dictionary
    """
    try:
        value = json_dict[key_try.key]
    except KeyError:
        return empty_values_for_keys(key_try)
    return values_for_keys(value, key_try, array_index)


def values_for_keys(value, key_try, array_index):
    """Return a list of values contained by the provided value object.
    The method will recursively go through dictionaries.

    Keyword arguments:
    value -- value object (scalar, list, dict) to make value list for
    key_try -- Key object to try accessing in the dictionary
    array_index -- if the given value is a list, the index of the list
    to get the value for
    """
    values = []
    if isinstance(value, dict):
        for subkey in key_try.subkeys.all_keys():
            values = values + dict_into_values(value, subkey)
    elif isinstance(value, list):
        values = values + values_for_keys(value[array_index], key_try, array_index)
    else:
        values.append(value)
    return values


def empty_values_for_keys(key_try):
    """Return a list of empty strings for each of the given Key and
    subkeys

    Keyword arguments:
    key_try -- Key object to make a list of empty strings for
    """
    values = []
    if key_try.subkeys.count() == 0:
        values.append("")
    else:
        for subkey in key_try.subkeys.all_keys():
            values = values + empty_values_for_keys(subkey)
    return values


def create_csv_string(value_list):
    """Return a string that corresponds to a row of a .csv file

    Keyword arguments:
    value_list -- List of values to turn into strings and make into .csv file row
    """
    csvpieces = []
    for value in value_list:
        string_value = str(value)
        if any((c in string_value) for c in ['\r', '\n', ',', '"']):
            string_value = string_value.replace('"', '""')
            string_value = '"' + string_value + '"'
        csvpieces.append(string_value)
    return ",".join(csvpieces)
