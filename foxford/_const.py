BASE = 'https://foxford.ru'
ACTIVATE = 'https://foxford.ru/courses/{course_id}/activate/{promocode}'
CSRF_TOKEN = 'https://foxford.ru/api/csrf_token'
USER_LOGIN = 'https://foxford.ru/user/login'
ME = 'https://foxford.ru/api/user/me'
BOOKMARKS = 'https://foxford.ru/api/user/bookmarks?{query}'
COURSE = 'https://foxford.ru/api/courses/{course_id}'
LESSONS = 'https://foxford.ru/api/courses/{course_id}/lessons?{query}'
LESSON = 'https://foxford.ru/api/courses/{course_id}/lessons/{lesson_id}'
GROUPS = 'https://foxford.ru/groups/{webinar_id}'
TASKS = 'https://foxford.ru/api/lessons/{lesson_id}/tasks'
TASK = 'https://foxford.ru/api/lessons/{lesson_id}/tasks/{task_id}'
TASK_URL = 'https://foxford.ru/lessons/{lesson_id}/tasks/{task_id}'
FAILS = 'https://foxford.ru/api/lessons/{lesson_id}/tasks/{task_id}/fails'
ANSWER_ATTEMPTS = 'https://foxford.ru/api/lessons/{lesson_id}/tasks/{task_id}/answer_attempts'


REFRESH_API = 'https://foxford.ru/api/ulms/accounts/me/refresh'

MASTER = 'https://storage.svc.netology-group.services/api/v2/backends/yandex/sets/hls.webinar.foxford.ru::{stream_id}/objects/long.v2.yandex.master.m3u8'
WEBINAR_SCOPE = 'https://dispatcher-vod-ng.svc.netology-group.services/api/v1/audiences/foxford.ru/webinars/{scope}'
EVENTS = 'https://storage.svc.netology-group.services/api/v2/sets/eventsdump.foxford.ru::{event_room_id}/objects/json'
CONTENT = 'https://storage.svc.netology-group.services/api/v2/sets/content.webinar.foxford.ru::{scope}/objects/{filename}'

HEADERS = {
    'Referer': 'https://foxford.vod.netology-group.services/',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Macintosh; PPC Mac OS X 10_8_5) AppleWebKit/5332 (KHTML, like Gecko) Chrome/39.0.844.0 Mobile Safari/5332'
}

TASK_ELEMENT = 'taskContent'

JS_INJECT = (
    """
    var head = document.getElementsByTagName("head")[0];
    var style = document.createElement("style");
    style.type = "text/css";
    style.innerHTML = `{styles}`;
    head.appendChild(style); 
    """
)

STYLES = (
    """
    #footerComponent {
        display: none;
    }

    .RightPanel_root__lurYQ {
        display: none;
    }

    #joyrideNavigation {
        display: none;
    }

    .lessonView_laptopHeader__2lwcE {
        visibility:hidden;
    }

    #headerComponent {
        display: none;
    }

    #cc_div {
        visibility:hidden;
    }

    .Toastify {
        display: none;
    }

    .bottom-slide-panel__Root-ida-dEJ {
        display: none;
    }

    #taskContent::after {
        content: 'Telegram: @no_structure';
        font-weight: 500;
        margin-top: 30px;
        padding: 10px;
        display: block;
        background: linear-gradient(270deg, white 30%, orange 200%);
        font-size: 25px;
        z-index: 1000;
        border-radius: 5px;
    }

    .PadMarg_padding-top-20__3BlHh {
        display: none;
    }
    """
)