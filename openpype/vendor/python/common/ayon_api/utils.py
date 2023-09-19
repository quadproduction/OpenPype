import re
import datetime
import uuid
import string
import platform
import collections
try:
    # Python 3
    from urllib.parse import urlparse, urlencode
except ImportError:
    # Python 2
    from urlparse import urlparse
    from urllib import urlencode

import requests
import unidecode

from .exceptions import UrlError

REMOVED_VALUE = object()
SLUGIFY_WHITELIST = string.ascii_letters + string.digits
SLUGIFY_SEP_WHITELIST = " ,./\\;:!|*^#@~+-_="

RepresentationParents = collections.namedtuple(
    "RepresentationParents",
    ("version", "product", "folder", "project")
)


def prepare_query_string(key_values):
    """Prepare data to query string.

    If there are any values a query starting with '?' is returned otherwise
    an empty string.

    Args:
         dict[str, Any]: Query values.

    Returns:
        str: Query string.
    """

    if not key_values:
        return ""
    return "?{}".format(urlencode(key_values))


def create_entity_id():
    return uuid.uuid1().hex


def convert_entity_id(entity_id):
    if not entity_id:
        return None

    if isinstance(entity_id, uuid.UUID):
        return entity_id.hex

    try:
        return uuid.UUID(entity_id).hex

    except (TypeError, ValueError, AttributeError):
        pass
    return None


def convert_or_create_entity_id(entity_id=None):
    output = convert_entity_id(entity_id)
    if output is None:
        output = create_entity_id()
    return output


def entity_data_json_default(value):
    if isinstance(value, datetime.datetime):
        return int(value.timestamp())

    raise TypeError(
        "Object of type {} is not JSON serializable".format(str(type(value)))
    )


def slugify_string(
    input_string,
    separator="_",
    slug_whitelist=SLUGIFY_WHITELIST,
    split_chars=SLUGIFY_SEP_WHITELIST,
    min_length=1,
    lower=False,
    make_set=False,
):
    """Slugify a text string.

    This function removes transliterates input string to ASCII, removes
    special characters and use join resulting elements using
    specified separator.

    Args:
        input_string (str): Input string to slugify
        separator (str): A string used to separate returned elements
            (default: "_")
        slug_whitelist (str): Characters allowed in the output
            (default: ascii letters, digits and the separator)
        split_chars (str): Set of characters used for word splitting
            (there is a sane default)
        lower (bool): Convert to lower-case (default: False)
        make_set (bool): Return "set" object instead of string.
        min_length (int): Minimal length of an element (word).

    Returns:
        Union[str, Set[str]]: Based on 'make_set' value returns slugified
            string.
    """

    tmp_string = unidecode.unidecode(input_string)
    if lower:
        tmp_string = tmp_string.lower()

    parts = [
        # Remove all characters that are not in whitelist
        re.sub("[^{}]".format(re.escape(slug_whitelist)), "", part)
        # Split text into part by split characters
        for part in re.split("[{}]".format(re.escape(split_chars)), tmp_string)
    ]
    # Filter text parts by length
    filtered_parts = [
        part
        for part in parts
        if len(part) >= min_length
    ]
    if make_set:
        return set(filtered_parts)
    return separator.join(filtered_parts)


def failed_json_default(value):
    return "< Failed value {} > {}".format(type(value), str(value))


def prepare_attribute_changes(old_entity, new_entity, replace=False):
    attrib_changes = {}
    new_attrib = new_entity.get("attrib")
    old_attrib = old_entity.get("attrib")
    if new_attrib is None:
        if not replace:
            return attrib_changes
        new_attrib = {}

    if old_attrib is None:
        return new_attrib

    for attr, new_attr_value in new_attrib.items():
        old_attr_value = old_attrib.get(attr)
        if old_attr_value != new_attr_value:
            attrib_changes[attr] = new_attr_value

    if replace:
        for attr in old_attrib:
            if attr not in new_attrib:
                attrib_changes[attr] = REMOVED_VALUE

    return attrib_changes


def prepare_entity_changes(old_entity, new_entity, replace=False):
    """Prepare changes of entities."""

    changes = {}
    for key, new_value in new_entity.items():
        if key == "attrib":
            continue

        old_value = old_entity.get(key)
        if old_value != new_value:
            changes[key] = new_value

    if replace:
        for key in old_entity:
            if key not in new_entity:
                changes[key] = REMOVED_VALUE

    attr_changes = prepare_attribute_changes(old_entity, new_entity, replace)
    if attr_changes:
        changes["attrib"] = attr_changes
    return changes


def _try_parse_url(url):
    try:
        return urlparse(url)
    except BaseException:
        return None


def _try_connect_to_server(url):
    try:
        # TODO add validation if the url lead to Ayon server
        #   - thiw won't validate if the url lead to 'google.com'
        requests.get(url)

    except BaseException:
        return False
    return True


def login_to_server(url, username, password):
    """Use login to the server to receive token.

    Args:
        url (str): Server url.
        username (str): User's username.
        password (str): User's password.

    Returns:
        Union[str, None]: User's token if login was successfull.
            Otherwise 'None'.
    """

    headers = {"Content-Type": "application/json"}
    response = requests.post(
        "{}/api/auth/login".format(url),
        headers=headers,
        json={
            "name": username,
            "password": password
        }
    )
    token = None
    # 200 - success
    # 401 - invalid credentials
    # *   - other issues
    if response.status_code == 200:
        token = response.json()["token"]
    return token


def logout_from_server(url, token):
    """Logout from server and throw token away.

    Args:
        url (str): Url from which should be logged out.
        token (str): Token which should be used to log out.
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token)
    }
    requests.post(
        url + "/api/auth/logout",
        headers=headers
    )


def is_token_valid(url, token):
    """Check if token is valid.

    Args:
        url (str): Server url.
        token (str): User's token.

    Returns:
        bool: True if token is valid.
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token)
    }
    response = requests.get(
        "{}/api/users/me".format(url),
        headers=headers
    )
    return response.status_code == 200


def validate_url(url):
    """Validate url if is valid and server is available.

    Validation checks if can be parsed as url and contains scheme.

    Function will try to autofix url thus will return modified url when
    connection to server works.

    ```python
    my_url = "my.server.url"
    try:
        # Store new url
        validated_url = validate_url(my_url)

    except UrlError:
        # Handle invalid url
        ...
    ```

    Args:
        url (str): Server url.

    Returns:
        Url which was used to connect to server.

    Raises:
        UrlError: Error with short description and hints for user.
    """

    stripperd_url = url.strip()
    if not stripperd_url:
        raise UrlError(
            "Invalid url format. Url is empty.",
            title="Invalid url format",
            hints=["url seems to be empty"]
        )

    # Not sure if this is good idea?
    modified_url = stripperd_url.rstrip("/")
    parsed_url = _try_parse_url(modified_url)
    universal_hints = [
        "does the url work in browser?"
    ]
    if parsed_url is None:
        raise UrlError(
            "Invalid url format. Url cannot be parsed as url \"{}\".".format(
                modified_url
            ),
            title="Invalid url format",
            hints=universal_hints
        )

    # Try add 'https://' scheme if is missing
    # - this will trigger UrlError if both will crash
    if not parsed_url.scheme:
        new_url = "https://" + modified_url
        if _try_connect_to_server(new_url):
            return new_url

    if _try_connect_to_server(modified_url):
        return modified_url

    hints = []
    if "/" in parsed_url.path or not parsed_url.scheme:
        new_path = parsed_url.path.split("/")[0]
        if not parsed_url.scheme:
            new_path = "https://" + new_path

        hints.append(
            "did you mean \"{}\"?".format(parsed_url.scheme + new_path)
        )

    raise UrlError(
        "Couldn't connect to server on \"{}\"".format(url),
        title="Couldn't connect to server",
        hints=hints + universal_hints
    )


class TransferProgress:
    """Object to store progress of download/upload from/to server."""

    def __init__(self):
        self._started = False
        self._transfer_done = False
        self._transfered = 0
        self._content_size = None

        self._failed = False
        self._fail_reason = None

        self._source_url = "N/A"
        self._destination_url = "N/A"

    def get_content_size(self):
        return self._content_size

    def set_content_size(self, content_size):
        if self._content_size is not None:
            raise ValueError("Content size was set more then once")
        self._content_size = content_size

    def get_started(self):
        return self._started

    def set_started(self):
        if self._started:
            raise ValueError("Progress already started")
        self._started = True

    def get_transfer_done(self):
        return self._transfer_done

    def set_transfer_done(self):
        if self._transfer_done:
            raise ValueError("Progress was already marked as done")
        if not self._started:
            raise ValueError("Progress didn't start yet")
        self._transfer_done = True

    def get_failed(self):
        return self._failed

    def get_fail_reason(self):
        return self._fail_reason

    def set_failed(self, reason):
        self._fail_reason = reason
        self._failed = True

    def get_transferred_size(self):
        return self._transfered

    def set_transferred_size(self, transfered):
        self._transfered = transfered

    def add_transferred_chunk(self, chunk_size):
        self._transfered += chunk_size

    def get_source_url(self):
        return self._source_url

    def set_source_url(self, url):
        self._source_url = url

    def get_destination_url(self):
        return self._destination_url

    def set_destination_url(self, url):
        self._destination_url = url

    @property
    def is_running(self):
        if (
            not self.started
            or self.done
            or self.failed
        ):
            return False
        return True

    @property
    def transfer_progress(self):
        if self._content_size is None:
            return None
        return (self._transfered * 100.0) / float(self._content_size)

    content_size = property(get_content_size, set_content_size)
    started = property(get_started)
    transfer_done = property(get_transfer_done)
    failed = property(get_failed)
    fail_reason = property(get_fail_reason)
    source_url = property(get_source_url, set_source_url)
    destination_url = property(get_destination_url, set_destination_url)
    content_size = property(get_content_size, set_content_size)
    transferred_size = property(get_transferred_size, set_transferred_size)


def create_dependency_package_basename(platform_name=None):
    """Create basename for dependency package file.

    Args:
        platform_name (Optional[str]): Name of platform for which the
            bundle is targeted. Default value is current platform.

    Returns:
        str: Dependency package name with timestamp and platform.
    """

    if platform_name is None:
        platform_name = platform.system().lower()

    now_date = datetime.datetime.now()
    time_stamp = now_date.strftime("%y%m%d%H%M")
    return "ayon_{}_{}".format(time_stamp, platform_name)
