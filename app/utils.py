import bleach_extras
from html import unescape

from app.models import Course

def clean_escaped_html(value: str) -> str:
    """ Remove non-whitelist HTML tags from user input.

    On the frontend, Jodit escapes HTML characters on the fly, sending unicode strings. Those need
    to be removed before processing with bleach to remove non-whitelisted tags.

    This is a little goofy because the escaped HTML needs to be parsed back into unicode characters
    to be removed correctly by bleach.

    The bleach_extras package removes non-whitelisted tag children elements as well as the tags.

    This solution is a combination of approaches from 
      - https://stackoverflow.com/questions/701704/convert-html-entities-to-unicode-and-vice-versa
      - https://github.com/jvanasco/bleach_extras

    Args:
        value (str): string containing HTML

    Returns:
        str: Sanitized HTML
    """
    clean = bleach_extras.clean_strip_content(unescape(value), tags=['p', 'strong', 'em', 'u', 'br', 'ul', 'ol', 'li'])
    return clean

def object_to_select(items):
    """ Unpack a database class for the select partial

    Args:
        items (any): List of database objects
    
    Returns:
        list (object): [{text, value}, ...] formatted list
    """
    results = [{"text": item.name, "value": item.id} for item in items]

    return results
