from ._downloader import StreamDownloader, PresentationDownloader
from ._const import TASK_URL

class FoxfordMain(object):
    def __init__(self, username, password):
        self._username = username
        self._password = password

        self._session = None

        self._full_name = None
        self._bookmarks = []

        self._courses = []

        self._fetch_main()

    def __repr__(self):
        return f'{self._full_name}'

    def _fetch_main(self):
        raise NotImplementedError

    def _process_courses(self):
        raise NotImplementedError

    @property
    def courses(self):
        if not self._courses:
            self._process_courses()
        return self._courses
    
    @property
    def session(self):
        return self._session

class FoxfordCourse(object):
    def __init__(self, parent):
        self._parent = parent
        
        self._info = None

        self._refresh_token = None

        self._id = None
        self._title = None
        self._active = None

        self._lessons = []

        self._have_basic = False

    def __repr__(self):
        return f'{self._title} [ID: {self._id}]'

    def _fetch_course(self):
        raise NotImplementedError
    
    def _process_lessons():
        raise NotImplementedError

    @property
    def id(self):
        return self._id

    @property
    def title(self):
        return self._title

    @property
    def active(self):
        if not self._access_reason:
            self._fetch_course()
        return self._active

    @property
    def lessons(self):
        if not self._info:
            self._fetch_course()
        if not self._lessons:
            self._process_lessons()
        return self._lessons

class FoxfordLessons(object):
    def __init__(self, parent):
        self._parent = parent
        self._main = parent._parent
        self._info = None

        self._id = None
        self._position = None

        self._title = None

        self._is_locked = None

        self._preparation_materials = None

        self._webinar_id = None
        self._webinar_status = None
        self._webinar_duration = None
        self._webinar_scope = None
        self._streams = []

        self._events = []

        self._tasks = []

        self._have_basic = False

    def __repr__(self):
        lesson = f'{self.position}. {self.title}'
        return lesson

    def _fetch_lesson(self):
        raise NotImplementedError

    def _process_streams(self):
        raise NotImplementedError
    
    def _process_tasks(self):
        raise NotImplementedError

    def get_stream(self):
        raise NotImplementedError
    
    def get_presentation(self):
        raise NotImplementedError

    @property
    def id(self):
        return self._id

    @property
    def position(self):
        return int(self._position or 0)

    @property
    def title(self):
        return self._title

    @property
    def events(self):
        if not self._events:
            self._fetch_lesson()
        return self._events
    
    @property
    def is_locked(self):
        if not self._is_locked:
            self._fetch_lesson()
        return self._is_locked
    
    @property
    def preparation_materials(self):
        if not self._preparation_materials:
            self._fetch_lesson()
        return self._preparation_materials

    @property
    def streams(self):
        if not self._info:
            self._fetch_lesson()
        if not self._streams:
            self._process_streams()
        return self._streams

    @property
    def tasks(self):
        if not self._info:
            self._fetch_lesson()
        if not self._tasks:
            self._process_tasks()
        return self._tasks

    @property
    def webinar_id(self):
        if not self._webinar_id:
            self._fetch_lesson()
        return self._webinar_id
    
    @property
    def webinar_status(self):
        if not self._webinar_status:
            self._fetch_lesson()
        return self._webinar_status
    

class FoxfordLessonPresentation(PresentationDownloader):
    def __init__(self, parent):
        self._parent = parent
        self._refresh_token = None
        self._webinar_scope = None
        self._file_id = None
        self._title = None

        PresentationDownloader.__init__(self)

    def __repr__(self):
        return f'{self._title} ({self._file_id})'
    
class FoxfordLessonStream(StreamDownloader):
    def __init__(self, parent):
        self._parent = parent
        self._stream_id = None
        self._refresh_token = None

        self._video = None
        self._audio = None

        self._is_kinescope = None

        self._width = None
        self._height = None
        self._resolution = None
        self._quality = None
        
        StreamDownloader.__init__(self)

    def __repr__(self):
        return f'{self.resolution} stream'

    @property
    def video(self):
        return self._video
    
    @property
    def audio(self):
        return self._audio
    
    @property
    def resolution(self):
        return self._resolution
    
    @property
    def quality(self):
        return self._quality

class FoxfordLessonSingleTask(object):
    def __init__(self, parent):
        self._parent = parent

        self._parent_id = parent._id

        self._id = None
        self._name = None
        self._number = None

        self._answer_status = None

    def __repr__(self):
        return f'{self._name} [{self._id}]'

    @property
    def id(self):
        return self._id
    
    @property
    def url(self):
        return TASK_URL.format(lesson_id=self._parent_id, task_id=self._id)

    @property
    def name(self):
        return self._name

    @property
    def number(self):
        return self._number
    
    @property
    def status(self):
        return self._answer_status
