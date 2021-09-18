import sys

from ._extract import FoxfordBuilder
from ._shared import (
        FoxfordMain,
        FoxfordCourse,
        FoxfordLessons,
        FoxfordLessonStream,
        FoxfordLessonPresentation,
        FoxfordLessonSingleTask
    )

# todo: change this v
session = FoxfordBuilder()

class InternFoxford(FoxfordMain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = session._session
    
    def _fetch_main(self):        
        auth = session.login(self._username, self._password)

        if auth.get('login') == 'successful':
            self._full_name = session.fetch_me().get('full_name')

            print(f'[Foxford] Успешная авторизация, {self._full_name}')
                        
        if auth.get('login') == 'failed':
            print('[Foxford] Не удалось авторизоваться')
            sys.exit(0)
    
    def _process_courses(self):
        courses = []
        self._bookmarks = session.fetch_bookmarks()
        for course in self._bookmarks:
            resource_type = course.get('resource_type')
            if resource_type == 'course':
                course_id = course.get('resource_id')
                title = f"{course.get('name')}. {course.get('subtitle')}"
                courses.append(InternFoxfordCourse(course_id, title, self))

        self._courses = courses

    def get_course(self, course_id):
        result = None
        courses = self.courses
        for course in courses:
            if course.id == course_id:
                result = course

        return result
    
    def unsafe_get_course(self, course_id):
        return InternFoxfordCourse(course_id, '', self)
    
    def activate_course(self, course_id, promocode):
        session.activate_course(course_id, promocode)
        self._process_courses()
        

class InternFoxfordCourse(FoxfordCourse):
    def __init__(self, course_id, title, parent):
        super().__init__(parent)
        self._id = course_id
        self._title = title

    def _fetch_course(self):
        if self._have_basic:
            return

        self._info = session.fetch_course(self._id)
        
        self._title = self._info.get('full_title')
        self._active = self._info.get('users_course').get('active')

        self._have_basic = True
    
    def _process_lessons(self):
        lessons = session.fetch_lessons(self._id)
        self._lessons = (
            [InternFoxfordLesson(lesson, self) for lesson in lessons]
            if len(lessons) > 0
            else []
        )

    def get_lesson(self, position):
        result = None
        for lesson in self.lessons:
            if int(lesson.position or 0) == int(position or 0):
                result = lesson
                break

        return result

class InternFoxfordLesson(FoxfordLessons):
    def __init__(self, lesson, parent):
        super().__init__(parent)
        self._id = lesson.get('id')
        self._position = lesson.get('position')
        self._title = lesson.get('title')

    def _fetch_lesson(self):
        if self._have_basic:
            return

        self._info = session.fetch_full_lesson(self._parent._id, self._id)

        self._is_locked = self._info.get('is_locked')

        self._preparation_materials = self._info.get('preparation_materials')

        self._webinar_id = self._info.get('webinar_id')
        self._webinar_status = self._info.get('webinar_status')
        self._webinar_duration = self._info.get('webinar_duration')
        self._webinar_scope = self._info.get('webinar_scope')

        self._events = self._info.get('events', [])

        self._have_basic = True

    def _process_streams(self):
        streams = (
            [InternFoxfordLessonStream(s, self) for s in self._info['streams']]
            if len(self._info['streams']) > 0
            else []
        )
        self._streams = sorted(streams, key=lambda e: e.quality, reverse=True)        
    
    def _process_tasks(self):
        self._tasks = (
            [InternFoxfordLessonTask(t, self) for t in self._info['tasks']]
            if len(self._info['tasks']) > 0
            else []
        )

    def get_stream(self):
        return next(iter(self.streams), None)
        
    def get_presentation(self):
        presentation = None
        index = 0
        for event in self._events:
            data = event.get('data', {})
            if not data: data = {}
            url = data.get('url', '')
            title = data.get('title', '')
            index += 1
            if 'welcome' in title: continue
            if '.pdf' in url:
                file_id = url[url.rfind('/')+1:]
                presentation = InternFoxfordLessonPresentation(file_id, title, self)
                if index > 50: break
        
        return presentation
    
class InternFoxfordLessonPresentation(FoxfordLessonPresentation):
    def __init__(self, file_id, title, parent) -> None:
        super().__init__(parent)
        self._refresh_token = session._refresh_token
        self._webinar_scope = parent._webinar_scope

        self._file_id = file_id
        self._title = title

    
class InternFoxfordLessonStream(FoxfordLessonStream):
    def __init__(self, stream, parent):
        super().__init__(parent)
        self._refresh_token = session._refresh_token

        self._video = stream.get('video')
        self._audio = stream.get('audio')

        if 'kinescope' in self._video:
            self._is_kinescope = True
        else:
            self._is_kinescope = False

        self._width = stream.get('width')
        self._height = stream.get('height')
        self._resolution = f'{self._width}x{self._height}'
        self._quality = int(self._height)

class InternFoxfordLessonTask(FoxfordLessonSingleTask):
    def __init__(self, task, parent):
        super().__init__(parent)

        self._id = task.get('id')
        self._name = task.get('name')
        self._number = task.get('number')

        self._answer_status = task.get('status')
    
    def fails(self):
        return session.fail_task(self._parent_id, self._id)
            
    def get(self):
        return session.fetch_task(self._parent_id, self._id)