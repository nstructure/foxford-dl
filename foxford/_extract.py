import m3u8, re, time, json, requests
from concurrent.futures import ThreadPoolExecutor
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from ._const import *

def extract_json(obj, key):
    arr = []

    def extract(obj, arr, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)

    return values

class FoxfordBuilder(object):
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        retries = Retry(
            total=3,
            backoff_factor=4,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self._session.mount(
            "https://",
            adapter=HTTPAdapter(
                max_retries=retries
            )
        )

        self._refresh_token = None
        self._access_token = None
        self._access_token_expiration = 0

        self._executor = ThreadPoolExecutor()
    
    def revoke_access_token(self):
        if time.time() > self._access_token_expiration:
            res = self._session.post(
                REFRESH_API,
                headers={'Authorization': self._refresh_token}
            )
            self._access_token = res.json().get('access_token', '')
            self._access_token_expiration = time.time() + 270

    def fetch_csrf_token(self):
        return self._session.get(
            CSRF_TOKEN,
            headers={
                'Referer': BASE
            }
        ).json().get('token', '')
    
    def activate_course(self, course_id, promocode):
        return self._session.get(
            ACTIVATE.format(course_id=course_id, promocode=promocode)
        )
    
    def fetch_task(self, lesson_id, task_id):
        return self._session.get(
            TASK.format(lesson_id=lesson_id, task_id=task_id)
        ).json()
    
    def fail_task(self, lesson_id, task_id):
        return self._session.post(
            FAILS.format(lesson_id=lesson_id, task_id=task_id),
            headers={'X-CSRF-TOKEN': self.fetch_csrf_token()}
        ).status_code
    
    def login(self, username, password):
        res = self._session.post(
            USER_LOGIN,
            headers={
                'Referer': BASE,
                'X-CSRF-Token': self.fetch_csrf_token(),
            },
            json={
                'user': {
                    'email': username,
                    'password': password
                }
            }
        )

        if res.status_code == 200:
            return {'login': 'successful'}
        else:
            return {'login': 'failed'}

    def fetch_me(self):
        return self._session.get(
            ME
        ).json()
    
    def fetch_bookmarks(self):
        def recursive(page_num):
            course_list_response = self._session.get(
                BOOKMARKS.format(query=f'page={page_num}&archived=0'),
            )

            if course_list_response.status_code != 200:
                return []

            if all(False for _ in course_list_response.json().get("bookmarks", [])):
                return ()

            return (
                *course_list_response.json().get("bookmarks", []),
                *recursive(page_num + 1)
            )
        
        return recursive(1)
    
    def fetch_lessons(self, course_id):
        r = self._session.get(
            LESSONS.format(course_id=course_id, query='')
        ).json()
        
        cursorb = r.get('cursors', {}).get('before')
        while cursorb != None:
            r = self._session.get(
                LESSONS.format(
                    course_id=course_id,
                    query=f'before={cursorb}'
                )
            ).json()

            cursorb = r.get('cursors', {}).get('before')

        cursora = r.get('cursors', {}).get('after')
        lessons = r.get('lessons', [])
        while cursora != None:
            r = self._session.get(
                LESSONS.format(
                    course_id=course_id,
                    query=f'after={cursora}'
                )
            ).json()

            for i in r.get('lessons', []):
                lessons.append(i)
            
            cursora = r.get('cursors', {}).get('after')

        return lessons
    
    def fetch_course(self, course_id):
        return self._session.get(
            COURSE.format(course_id=course_id)
        ).json()
    
    def fetch_lesson(self, course_id, lesson_id):
        return self._session.get(
            LESSON.format(course_id=course_id, lesson_id=lesson_id)
        ).json()
    
    def fetch_tasks(self, lesson_id):
        return self._session.get(
            TASKS.format(lesson_id=lesson_id)
        ).json()
    
    def fetch_webinar_scope(self, webinar_id):
        scope = ''
        res = self._session.get(
            GROUPS.format(
                webinar_id=webinar_id
            )
        )

        if not self._refresh_token and 'refresh_token' in res.text:
            s1 = res.text.find("refresh_token=") + len("refresh_token=")
            self._refresh_token = res.text[s1:s1+204]

        if 'scope=' in res.text:
            s = res.text.find("scope=") + len("scope=")
            scope = res.text[s:s+54]

            fix_scope = ''
            for c in scope:
                if c.isalnum():
                    fix_scope += c
                    
            scope = fix_scope
    
        return scope
    
    def fetch_stream_id(self, webinar_scope):
        stream_id = ''

        if not self._refresh_token: return stream_id
        self.revoke_access_token()

        res = self._session.get(
            WEBINAR_SCOPE.format(scope=webinar_scope),
            headers={'Authorization': f'Bearer {self._access_token}'}
        )
        try:
            res = res.json()
            stream_id = next(iter(extract_json(res, 'stream_id')), '')
        except:
            pass

        return stream_id
    
    def fetch_event_room_id(self, webinar_scope):
        event_room_id = ''
        if not self._refresh_token: return event_room_id
        self.revoke_access_token()

        res = self._session.get(
            WEBINAR_SCOPE.format(scope=webinar_scope),
            headers={'Authorization': f'Bearer {self._access_token}'}
        )
        try:
            res = res.json()
            possible_rooms = extract_json(res, 'event_room_id')
            if possible_rooms:
                event_room_id = possible_rooms[-1]
        except:
            pass

        return event_room_id

    def fetch_streams(self, webinar_id):
        streams = []
        stream_id = ''
        r = self._session.get(
            GROUPS.format(webinar_id=webinar_id)
        )
        
        if 'kinescope' in r.url:
            r = self._session.get(r.url)
            url = re.search("https://.*m3u8", r.text).group(0)
            r = self._session.get(url)

            if r.status_code != 200:
                return streams
        else:
            scope = self.fetch_webinar_scope(webinar_id)
            stream_id = self.fetch_stream_id(scope)

            if not stream_id:
                return streams
    
            r = self._session.get(
                MASTER.format(stream_id=stream_id),
                headers={'Authorization': f'Bearer {self._access_token}'}
            )
        
        master = m3u8.loads(r.text, r.url)
        for playlist in master.playlists:
            stream = {}
            audio = None

            if not playlist.base_path:
                playlist.base_path = r.url[:r.url.rfind('/')]

            stream['video'] = playlist.uri

            for media in playlist.media:
                if media.type == 'AUDIO':
                    audio = media.uri
    
            stream['audio'] = audio

            w, h = 0, 0
            if playlist.stream_info.resolution:
                w, h = playlist.stream_info.resolution

            stream['width'] = w
            stream['height'] = h

            streams.append(stream)
        
        return streams
    
    def fetch_events(self, event_room_id):
        if not self._refresh_token: return []
        self.revoke_access_token()
        try:
            return self._session.get(
                EVENTS.format(event_room_id=event_room_id),
                headers={
                    'Authorization': f'Bearer {self._access_token}'
                }
            ).json().get('events', [])
        except:
            return []
    
    def fetch_full_lesson(self, course_id, lesson_id):
        lesson = self.fetch_lesson(course_id, lesson_id)
        webinar_id = lesson.get('webinar_id')
        webinar_status = lesson.get('webinar_status')

        is_locked = lesson.get('is_locked')
        streams = []
        if not is_locked and webinar_status == 'video_available':
            streams = self.fetch_streams(webinar_id)
        
        lesson["streams"] = streams
        lesson["webinar_scope"] = self.fetch_webinar_scope(webinar_id)
        lesson["event_room_id"] = (
            self.fetch_event_room_id(lesson["webinar_scope"])
            if lesson["webinar_scope"]
            else ""
        )
        lesson["events"] = (
            self.fetch_events(lesson["event_room_id"])
            if lesson["event_room_id"]
            else []
        )
        lesson["tasks"] = self.fetch_tasks(lesson_id)

        return lesson