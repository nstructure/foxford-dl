import sys, os, foxford, json, shutil

from pathlib import Path
from utils import ImagesToPDF
from browser import FoxfordBrowser

class FoxfordSession(object):
    def __init__(self, username='', password='', dl_path='./courses'):
        self.foxford = foxford.init(username, password)
        self.browser = FoxfordBrowser(self.foxford._session)

        self.download_path = Path(dl_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    def list_courses(self):
        courses = self.foxford.courses
        for c in courses:
            print(f' + {c}')

    def download_lesson(self, lesson, dl_path):
        print(f'Урок: {lesson}')
        lesson_path = dl_path / str(lesson.position)
        
        lesson_path.mkdir(parents=True, exist_ok=True)

        if lesson.is_locked:
            print(' > Урок закрыт')
            return
    
        if lesson.preparation_materials:
            prepare = lesson_path / f'{lesson.position}_prepare.json'
            json.dump(
                lesson.preparation_materials,
                open(prepare, 'w', encoding='UTF-8'),
                indent=4,
                ensure_ascii=False,
            )

        stream = lesson.get_stream()
        if stream:
            print(' > Вебинар получен')
            stream.download(f'{lesson_path}/{lesson.position}.mp4')
        else:
            print(' > Вебинар не найден')
        
        presentation = lesson.get_presentation()
        if presentation:
            print(' > Найдена презентация', presentation)
            presentation.download(f'{lesson_path}/{lesson.position}_presentation.pdf')

        if lesson.tasks:
            tasks_path = lesson_path / 'tasks'
            tasks_path.mkdir(parents=True, exist_ok=True)

            for t in lesson.tasks:
                print(f' > Просмотр задания {t}')
                if t.status != 'success' and t.status != 'fail':
                    self.browser.print(t.url, f'{tasks_path}/{t.number}.png')
                    t.fails()
                    self.browser.print(t.url, f'{tasks_path}/{t.number}_a.png')
                else:
                    self.browser.print(t.url, f'{tasks_path}/{t.number}_a.png')
            
            tpath = lesson_path / f'{lesson.position}.pdf'
            spath = lesson_path / f'{lesson.position}a.pdf'
            ImagesToPDF(tasks_path).convert(tpath, '*[!_a].png')
            ImagesToPDF(tasks_path).convert(spath, '*_a.png')
            # shutil.rmtree(tasks_path)

    def download_course(self, course_id, start='', stop='', step=1):
        course = self.foxford.get_course(course_id)
        if not course:
            print('[Foxford] Курс не найден\n > Доступные курсы:')
            self.list_courses()
            return
        
        course_path = self.download_path / str(course.id)
        course_path.mkdir(parents=True, exist_ok=True)
    
        if start and stop:
            if start > stop:
                step = -1
                stop -= 2
            for l in range(start, stop+1, step):
                lesson = course.get_lesson(l)
                if not lesson: continue
                try:
                    self.download_lesson(lesson, course_path)
                except Exception as e:
                    print(f'[!] Ошибка, урок {lesson.position} [{str(e)}]')
        else:
            lessons = course.lessons
            for l in lessons:
                try:
                    self.download_lesson(l, course_path)
                except Exception as e:
                    print(f'[!] Ошибка, урок {l.position} [{str(e)}]')

def main():
    # email = os.getenv('username')
    # password = os.getenv('password')

    sys.stdout.write(' > EMAIL: ')
    sys.stdout.flush()
    email = input()

    sys.stdout.write(' > PASSWORD: ')
    sys.stdout.flush()
    password = input()

    sys.stdout.write(' > ID: ')
    sys.stdout.flush()
    course_id = int(input())
    
    sys.stdout.write(' > Начальный урок: ')
    sys.stdout.flush()
    start = int(input())

    sys.stdout.write(' > Конечный урок: ')
    sys.stdout.flush()
    stop = int(input())

    if email and password:
        foxford = FoxfordSession(username=email, password=password)
        foxford.download_course(course_id, start, stop)
    else:
        print('Не указаны логин или пароль')
        sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('[*] Прервано')
        sys.exit(0)
