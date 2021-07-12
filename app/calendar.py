# Create a new Google Calendar session through the Service Account.
# This interacts with the calendar to:
#   - Create new events
#   - Send invitations to users when they register
#   - Remove users when they cancel a registration

# init an oauth client
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

basedir = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(basedir, 'token.json')

# Set scope constants for the ECS PD account
scopes = ['https://www.googleapis.com/auth/calendar.readonly']


credentials = service_account.Credentials.from_service_account_file(path, scopes=scopes)
# delegated_credentials = credentials.with_subject(subject)


class CalendarService:
    def __init__(self):
        return None

    def build(self):
        return build('calendar', 'v3', credentials=credentials)
