"""
Splunk script to allow analytics to be collected from the Splunk app.
"""
import os
import shutil
import getpass
import sys
import subprocess

# pylint: disable=relative-import, import-error
from common import CONFIG, EVENTS_DIR, ANALYTICS_DIR
from c42api.common import analytics

QUERY_FILE = os.path.join(os.path.dirname(__file__), 'analytics.queries')
SPLUNK_COMMAND = os.path.join(CONFIG.splunk_home, 'bin', 'splunk')


def _extract_queries(query_file):
    """
    Takes an opened filed and reads the queries from it.

    The query file has a format of the following:

    #query_name
    line one of the query that breaks at a sensible point
    | line two of the query AND
        line three of the query that also break at sensible points
    | just write the query and break up it how you see fit without
    blank lines within any one query

    Between each query should be exactly one blank line.

    :param query_file: An opened file in read mode containing queries
    :return:           A map of query names to queries
    """

    def extract_next_query():
        """
        Reads the file to determine the next query.

        This function reads the file line by line using the next() function on
        the file object. When it hits a blank line it assumes that the query
        is complete and will join each line with a space.

        :return: The name of the query and the query itself
        """
        query_name = None
        query_list = []
        try:
            line = query_file.next()
            query_name = line.strip('#').strip() if line.startswith('#') else None
            while line:
                line = query_file.next().strip()
                query_list.append(line)
        except StopIteration:
            pass
        return query_name, ' '.join(query_list)

    results = {}
    name = True
    while name:
        name, query = extract_next_query()
        results[name] = query
    del results[None]
    return results


def _output_query_to_file(query, output_file, username, password):
    """
    Runs a splunk query and dumps the output to a file.

    :param query:       The search query for splunk to run
    :param output_file: The file to dump the resulting data
    :param username:    A splunk username
    :param password:    The password for that username
    """
    query = [SPLUNK_COMMAND, "search", "{}".format(query),
             '-output', 'json', '-auth', '{}:{}'.format(username, password)]
    subprocess.call(query, stdout=output_file)


@analytics.with_lock
def _run():
    """
    The scripts body. Captures json data from Splunk concerning the Code42 App
    """

    # collect user info
    username = raw_input("Splunk username:")
    password = getpass.getpass("Password:")

    # get all of the queries we need to run
    with open(QUERY_FILE, 'r') as query_file:
        queries = _extract_queries(query_file)

    # write out the results of each query to its own file
    for name, query in queries.items():
        out_file = os.path.join(ANALYTICS_DIR, name + '.json')
        with open(out_file, 'w+') as out:
            _output_query_to_file(query, out, username, password)

    # zip it up and delete the json files.
    archive_path = shutil.make_archive(ANALYTICS_DIR, 'zip', ANALYTICS_DIR)
    shutil.rmtree(ANALYTICS_DIR)
    os.mkdir(ANALYTICS_DIR)

    sys.stdout.write("The analytics are located at:\n")
    sys.stdout.write(os.path.join(EVENTS_DIR, archive_path))
    sys.stdout.write("\n\n")
    sys.stdout.write("Thanks for your help in improving our product!\n")


if __name__ == '__main__':
    _run()
