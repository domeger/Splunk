"""
This module is meant to provide scripts and utilities for writing scripts that
hit Code42 installations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# pylint: disable=relative-import
from backup_metadata_delta import calculate_delta
from computers import fetch_computers
from query import organization, devices
from security_event_restore import fetch_detection_events, create_filter_by_utc_datetime, create_filter_by_cursor
from storage_server import storage_servers
from users import fetch_users

from common.logging_config import set_log_file, set_log_level, get_logger
from common import resources
from common.script_output import write_csv, write_header_from_keyset, write_json, write_json_splunk
from common.server import Server

from requests.exceptions import ConnectionError, HTTPError
