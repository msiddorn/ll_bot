'''
    some useful spark bot suff
'''
import requests
from functools import partial

MENTION_REGEX = r'<spark-mention.*?data-object-id="(\w+)".*?spark-mention>'
PERSON_ID = 'Y2lzY29zcGFyazovL3VzL1BFT1BMRS9jZjE5OTU0OC05MzE1LTQ2NjktOGJmYy03MmNjMGNiYjc0NWQ'


def person_info(headers, person_id):
    return requests.get(
        'https://api.ciscospark.com/v1/people/{}'.format(person_id),
        headers=headers
    )

API_CALLS = {
    'create_message': partial(requests.post, 'https://api.ciscospark.com/v1/messages'),
    'get_person_details': person_info,
}
