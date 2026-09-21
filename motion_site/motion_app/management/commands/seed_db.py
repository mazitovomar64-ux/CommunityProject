"""
Management-команда для заполнения БД тестовыми данными.

КАК ПОДКЛЮЧИТЬ
---------------
1. Положите этот файл по пути:
       <ваше_приложение>/management/commands/seed_db.py
   Если папок management/ и management/commands/ ещё нет — создайте их
   и добавьте в каждую пустой файл __init__.py:
       <ваше_приложение>/management/__init__.py
       <ваше_приложение>/management/commands/__init__.py

2. Ниже, в блоке импортов, замените "myapp" на реальное имя приложения,
   в котором объявлены модели (UserProfile, Project, Task и т.д.) —
   в присланных вами файлах это app_label вашего models.py.

3. Запустите:
       python manage.py seed_db

   Команда идемпотентна — использует get_or_create, поэтому повторный
   запуск не создаст дублей.

4. Чтобы удалить ранее созданные тестовые данные перед повторным
   заполнением, запустите:
       python manage.py seed_db --flush

   Флаг удаляет только записи, связанные с тестовыми пользователями
   (домен почты SEED_DOMAIN ниже), реальные данные не затрагиваются.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from motion_app.models import (  # noqa: замените "myapp" на имя вашего приложения
    Activity,
    Chat,
    Direction,
    Message,
    Project,
    ProjectMember,
    Review,
    Service,
    SiteInfo,
    Task,
    Team,
    TeamMember,
    Translation,
    UserProfile,
)

SEED_DOMAIN = '@seed.local'
DEFAULT_PASSWORD = 'Qwerty123!'


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными для локальной разработки.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Перед заполнением удалить ранее созданные тестовые данные (по SEED_DOMAIN).',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options['flush']:
                self.flush_data()

            directions = self.create_directions()
            users = self.create_users(directions)
            teams = self.create_teams(users)
            projects = self.create_projects(users, teams, directions)
            self.create_tasks(projects, users)
            self.create_reviews(users, projects)
            self.create_services()
            self.create_translations()
            self.create_site_info()
            self.create_chat(users)
            self.create_activity(users)

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена тестовыми данными.'))

    # ------------------------------------------------------------------ #
    # Удаление предыдущих тестовых данных
    # ------------------------------------------------------------------ #
    def flush_data(self):
        self.stdout.write('Удаляю ранее созданные тестовые данные...')
        Message.objects.filter(sender__email__endswith=SEED_DOMAIN).delete()
        Activity.objects.filter(user__email__endswith=SEED_DOMAIN).delete()
        Review.objects.filter(user__email__endswith=SEED_DOMAIN).delete()
        Task.objects.filter(project__created_by__email__endswith=SEED_DOMAIN).delete()
        ProjectMember.objects.filter(project__created_by__email__endswith=SEED_DOMAIN).delete()
        Project.objects.filter(created_by__email__endswith=SEED_DOMAIN).delete()
        TeamMember.objects.filter(team__created_by__email__endswith=SEED_DOMAIN).delete()
        Team.objects.filter(created_by__email__endswith=SEED_DOMAIN).delete()
        UserProfile.objects.filter(email__endswith=SEED_DOMAIN).delete()

    # ------------------------------------------------------------------ #
    # Направления
    # ------------------------------------------------------------------ #
    def create_directions(self):
        self.stdout.write('Создаю направления...')
        data = [
            dict(slug='backend', icon='⚙️',
                 title='Backend-разработка', title_ky='Backend иштеп чыгуу',
                 description='Серверная логика, базы данных, API.',
                 description_ky='Сервердик логика, маалымат базалары, API.'),
            dict(slug='frontend', icon='🎨',
                 title='Frontend-разработка', title_ky='Frontend иштеп чыгуу',
                 description='Интерфейсы на React, вёрстка, UX.',
                 description_ky='React боюнча интерфейстер, вёрстка, UX.'),
            dict(slug='ml', icon='🤖',
                 title='Машинное обучение', title_ky='Машиналык окутуу',
                 description='Модели, анализ данных, нейросети.',
                 description_ky='Моделдер, маалыматтарды анализдөө, нейрондук тармактар.'),
            dict(slug='design', icon='🖌️',
                 title='UI/UX дизайн', title_ky='UI/UX дизайн',
                 description='Прототипирование и визуальный дизайн продуктов.',
                 description_ky='Продукттардын прототибин жана визуалдык дизайнын жасоо.'),
            dict(slug='devops', icon='🛠️',
                 title='DevOps', title_ky='DevOps',
                 description='CI/CD, инфраструктура, деплой.',
                 description_ky='CI/CD, инфраструктура, деплой.'),
            dict(slug='mobile', icon='📱',
                 title='Мобильная разработка', title_ky='Мобилдик иштеп чыгуу',
                 description='Приложения под iOS и Android.',
                 description_ky='iOS жана Android үчүн тиркемелер.'),
        ]
        directions = {}
        for item in data:
            slug = item.pop('slug')
            obj, _ = Direction.objects.get_or_create(slug=slug, defaults=item)
            directions[slug] = obj
        return directions

    # ------------------------------------------------------------------ #
    # Пользователи
    # ------------------------------------------------------------------ #
    def create_users(self, directions):
        self.stdout.write('Создаю пользователей...')
        data = [
            dict(username='admin', email=f'admin{SEED_DOMAIN}', first_name='Алина', last_name='Садыкова',
                 position='Администратор платформы', bio='Слежу за порядком на платформе.',
                 user_role='admin', work_status='busy', dirs=['backend', 'devops']),
            dict(username='nurlan_lead', email=f'nurlan{SEED_DOMAIN}', first_name='Нурлан', last_name='Беков',
                 position='Team Lead, Backend', bio='Веду backend-команду, люблю Django.',
                 user_role='team_lead', work_status='busy', dirs=['backend', 'devops']),
            dict(username='aigerim_lead', email=f'aigerim{SEED_DOMAIN}', first_name='Айгерим', last_name='Токтосунова',
                 position='Team Lead, ML', bio='Занимаюсь прикладным ML и NLP.',
                 user_role='team_lead', work_status='available', dirs=['ml']),
            dict(username='eldar', email=f'eldar{SEED_DOMAIN}', first_name='Эльдар', last_name='Мамбетов',
                 position='Frontend-разработчик', bio='React, TypeScript, люблю аккуратный UI.',
                 user_role='employee', work_status='available', dirs=['frontend']),
            dict(username='dinara', email=f'dinara{SEED_DOMAIN}', first_name='Динара', last_name='Осмонова',
                 position='Frontend-разработчик', bio='Верстаю адаптивные интерфейсы.',
                 user_role='employee', work_status='busy', dirs=['frontend', 'design']),
            dict(username='timur', email=f'timur{SEED_DOMAIN}', first_name='Тимур', last_name='Асанов',
                 position='Backend-разработчик', bio='Пишу API на DRF, люблю оптимизацию запросов.',
                 user_role='employee', work_status='available', dirs=['backend']),
            dict(username='meerim', email=f'meerim{SEED_DOMAIN}', first_name='Мээрим', last_name='Жумабекова',
                 position='ML-инженер', bio='Работаю с компьютерным зрением.',
                 user_role='employee', work_status='temporarily_unavailable', dirs=['ml']),
            dict(username='azamat', email=f'azamat{SEED_DOMAIN}', first_name='Азамат', last_name='Уулу',
                 position='DevOps-инженер', bio='Docker, Kubernetes, CI/CD.',
                 user_role='employee', work_status='available', dirs=['devops', 'backend']),
            dict(username='camila', email=f'camila{SEED_DOMAIN}', first_name='Камила', last_name='Рыскулова',
                 position='UI/UX дизайнер', bio='Проектирую пользовательские сценарии и прототипы в Figma.',
                 user_role='employee', work_status='available', dirs=['design']),
            dict(username='bakyt', email=f'bakyt{SEED_DOMAIN}', first_name='Бакыт', last_name='Иманов',
                 position='Mobile-разработчик', bio='Flutter и нативная разработка под Android.',
                 user_role='employee', work_status='busy', dirs=['mobile']),
        ]

        users = {}
        for item in data:
            dirs = item.pop('dirs')
            username = item.pop('username')
            user, created = UserProfile.objects.get_or_create(
                email=item['email'],
                defaults={**item, 'username': username},
            )
            if created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
            user.directions.set([directions[slug] for slug in dirs])
            users[username] = user
        return users

    # ------------------------------------------------------------------ #
    # Команды
    # ------------------------------------------------------------------ #
    def create_teams(self, users):
        self.stdout.write('Создаю команды...')
        data = [
            dict(name='Команда Backend', name_ky='Backend командасы',
                 description='Основная команда серверной разработки.',
                 description_ky='Сервердик иштеп чыгуунун негизги командасы.',
                 created_by='nurlan_lead',
                 members=[
                     ('nurlan_lead', 'Тимлид'),
                     ('timur', 'Backend-разработчик'),
                     ('azamat', 'DevOps-инженер'),
                 ]),
            dict(name='Команда ML & Продукт', name_ky='ML & Продукт командасы',
                 description='Команда, отвечающая за ML-продукты и их интерфейсы.',
                 description_ky='ML-продукттарды жана алардын интерфейстерин иштеп чыгуучу команда.',
                 created_by='aigerim_lead',
                 members=[
                     ('aigerim_lead', 'Тимлид'),
                     ('meerim', 'ML-инженер'),
                     ('eldar', 'Frontend-разработчик'),
                     ('dinara', 'Frontend-разработчик'),
                     ('camila', 'UI/UX дизайнер'),
                 ]),
        ]

        teams = {}
        for item in data:
            members = item.pop('members')
            created_by_key = item.pop('created_by')
            team, _ = Team.objects.get_or_create(
                name=item['name'],
                defaults={**item, 'created_by': users[created_by_key]},
            )
            for username, role in members:
                TeamMember.objects.get_or_create(
                    user=users[username],
                    defaults={'team': team, 'role_in_team': role},
                )
            teams[team.name] = team
        return teams

    # ------------------------------------------------------------------ #
    # Проекты
    # ------------------------------------------------------------------ #
    def create_projects(self, users, teams, directions):
        self.stdout.write('Создаю проекты...')
        data = [
            dict(title='Motion Community Platform', title_ky='Motion Community платформасы',
                 description='Платформа для поиска команды и публикации проектов.',
                 description_ky='Команда табуу жана долбоорлорду жарыялоо үчүн платформа.',
                 icon='🚀', category='Web', status='active',
                 github_url='https://github.com/example/motion-platform',
                 demo_url='https://motion.example.com',
                 created_by='nurlan_lead', team='Команда Backend',
                 dirs=['backend', 'frontend', 'devops'],
                 members=[('nurlan_lead', 'Тимлид проекта'), ('timur', 'Backend-разработчик'), ('azamat', 'DevOps')]),
            dict(title='Умный ассистент поддержки', title_ky='Колдоо кызматынын акылдуу ассистенти',
                 description='Чат-бот на базе LLM для ответов на частые вопросы клиентов.',
                 description_ky='Кардарлардын көп берилүүчү суроолоруна жооп берген LLM негизиндеги чат-бот.',
                 icon='💬', category='LLM', status='review',
                 github_url='https://github.com/example/support-assistant', demo_url='',
                 created_by='aigerim_lead', team='Команда ML & Продукт',
                 dirs=['ml', 'backend'],
                 members=[('aigerim_lead', 'Тимлид проекта'), ('meerim', 'ML-инженер'), ('timur', 'Backend-разработчик')]),
            dict(title='Дашборд аналитики проектов', title_ky='Долбоорлор аналитикасынын дашборду',
                 description='Визуализация метрик по командам и задачам для менеджеров.',
                 description_ky='Менеджерлер үчүн командалар жана тапшырмалар боюнча метрикаларды визуализациялоо.',
                 icon='📊', category='Frontend', status='active',
                 github_url='https://github.com/example/analytics-dashboard', demo_url='https://dashboard.example.com',
                 created_by='aigerim_lead', team='Команда ML & Продукт',
                 dirs=['frontend', 'design'],
                 members=[('eldar', 'Frontend-разработчик'), ('dinara', 'Frontend-разработчик'), ('camila', 'UI/UX дизайнер')]),
            dict(title='Мобильное приложение сообщества', title_ky='Коомчулуктун мобилдик тиркемеси',
                 description='Android/iOS-клиент для общения участников сообщества.',
                 description_ky='Коомчулук мүчөлөрүнүн баарлашуусу үчүн Android/iOS-клиент.',
                 icon='📱', category='Frontend', status='on_hold',
                 github_url='', demo_url='',
                 created_by='nurlan_lead', team=None,
                 dirs=['mobile'],
                 members=[('bakyt', 'Mobile-разработчик')]),
        ]

        projects = {}
        for item in data:
            dirs = item.pop('dirs')
            members = item.pop('members')
            created_by_key = item.pop('created_by')
            team_key = item.pop('team')

            project, _ = Project.objects.get_or_create(
                title=item['title'],
                defaults={
                    **{k: v for k, v in item.items() if k != 'title'},
                    'created_by': users[created_by_key],
                    'team': teams[team_key] if team_key else None,
                },
            )
            project.directions.set([directions[slug] for slug in dirs])

            for username, role in members:
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=users[username],
                    defaults={'role_in_project': role},
                )
            projects[project.title] = project
        return projects

    # ------------------------------------------------------------------ #
    # Задачи
    # ------------------------------------------------------------------ #
    def create_tasks(self, projects, users):
        self.stdout.write('Создаю задачи...')
        data = [
            dict(project='Motion Community Platform', title='Настроить CI/CD пайплайн',
                 description='Автоматизировать тесты и деплой при пуше в main.',
                 priority='high', status='in_progress', assigned_to=['azamat'],
                 github_url='', result_text=''),
            dict(project='Motion Community Platform', title='Реализовать эндпоинты профиля пользователя',
                 description='CRUD для профиля, загрузка аватара и резюме.',
                 priority='medium', status='done', assigned_to=['timur'],
                 github_url='https://github.com/example/motion-platform/pull/12',
                 result_text='Эндпоинты реализованы и покрыты тестами.', submitted=True),
            dict(project='Умный ассистент поддержки', title='Собрать датасет частых вопросов',
                 description='Выгрузить и разметить обращения пользователей за последний год.',
                 priority='high', status='review', assigned_to=['meerim'],
                 github_url='', result_text='Датасет из 2000 размеченных обращений готов.', submitted=True),
            dict(project='Дашборд аналитики проектов', title='Сверстать страницу дашборда',
                 description='Адаптивная вёрстка графиков и таблиц по макету из Figma.',
                 priority='medium', status='new', assigned_to=['eldar', 'dinara'],
                 github_url='', result_text=''),
            dict(project='Дашборд аналитики проектов', title='Подготовить UI-кит для дашборда',
                 description='Компоненты кнопок, карточек и графиков в едином стиле.',
                 priority='low', status='hold', assigned_to=['camila'],
                 github_url='', result_text=''),
            dict(project='Мобильное приложение сообщества', title='Прототип экрана ленты',
                 description='Кликабельный прототип главной ленты приложения.',
                 priority='medium', status='new', assigned_to=['bakyt'],
                 github_url='', result_text=''),
        ]

        for item in data:
            project = projects[item.pop('project')]
            assigned = item.pop('assigned_to')
            submitted = item.pop('submitted', False)
            task, _ = Task.objects.get_or_create(
                project=project,
                title=item['title'],
                defaults={
                    **{k: v for k, v in item.items() if k != 'title'},
                    'submitted_at': timezone.now() if submitted else None,
                },
            )
            task.assigned_to.set([users[u] for u in assigned])

    # ------------------------------------------------------------------ #
    # Отзывы
    # ------------------------------------------------------------------ #
    def create_reviews(self, users, projects):
        self.stdout.write('Создаю отзывы...')
        data = [
            dict(user='eldar', project='Motion Community Platform', rating=5,
                 text='Отличная платформа, удобно искать команду для проектов.'),
            dict(user='dinara', project='Дашборд аналитики проектов', rating=4,
                 text='Классный дашборд, но не хватает экспорта в PDF.'),
            dict(user='camila', project=None, rating=5,
                 text='Сообщество очень поддерживающее, быстро нашла ментора.'),
            dict(user='bakyt', project='Умный ассистент поддержки', rating=4,
                 text='Бот хорошо отвечает, но иногда путает контекст.'),
        ]
        for item in data:
            project = projects[item['project']] if item['project'] else None
            Review.objects.get_or_create(
                user=users[item['user']],
                project=project,
                defaults={'rating': item['rating'], 'text_review': item['text']},
            )

    # ------------------------------------------------------------------ #
    # Услуги
    # ------------------------------------------------------------------ #
    def create_services(self):
        self.stdout.write('Создаю услуги...')
        data = [
            dict(title='Менторство', title_ky='Менторлук', icon='🧑‍🏫', order=1,
                 description='Помощь опытных разработчиков начинающим участникам сообщества.',
                 description_ky='Тажрыйбалуу иштеп чыгуучулардын жаңы мүчөлөргө жардамы.'),
            dict(title='Поиск команды', title_ky='Команда табуу', icon='🤝', order=2,
                 description='Подбор участников под проект по направлению и уровню.',
                 description_ky='Долбоор үчүн багыты жана деңгээли боюнча мүчөлөрдү тандоо.'),
            dict(title='Портфолио проектов', title_ky='Долбоорлордун портфолиосу', icon='📁', order=3,
                 description='Публичная витрина проектов сообщества для резюме и грантов.',
                 description_ky='Резюме жана гранттар үчүн коомчулуктун долбоорлорунун витринасы.'),
        ]
        for item in data:
            Service.objects.get_or_create(title=item['title'], defaults=item)

    # ------------------------------------------------------------------ #
    # Переводы интерфейса
    # ------------------------------------------------------------------ #
    def create_translations(self):
        self.stdout.write('Создаю переводы...')
        data = {
            'home.title': ('Motion Community', 'Motion Community'),
            'home.subtitle': ('Платформа для тех, кто создаёт проекты вместе', 'Долбоорлорду чогуу жараткандар үчүн платформа'),
            'home.description': (
                'Находите команду, публикуйте проекты и растите вместе с сообществом.',
                'Команда табыңыз, долбоорлорду жарыялаңыз жана коомчулук менен чогуу өнүгүңүз.',
            ),
            'home.cta.projects': ('Смотреть проекты', 'Долбоорлорду көрүү'),
            'home.cta.work_with_us': ('Присоединиться', 'Кошулуу'),
            'about.title': ('О нас', 'Биз жөнүндө'),
            'about.mission': (
                'Наша миссия — объединять талантливых людей вокруг общих проектов.',
                'Биздин миссиябыз — таланттуу адамдарды жалпы долбоорлордун тегерегинде бириктирүү.',
            ),
            'about.goal': (
                'Помочь каждому участнику найти команду и вырасти профессионально.',
                'Ар бир мүчөгө команда табууга жана кесиптик жактан өсүүгө жардам берүү.',
            ),
            'about.focus.tech': ('Технологии', 'Технологиялар'),
            'about.focus.community': ('Сообщество', 'Коомчулук'),
            'about.focus.growth': ('Развитие', 'Өнүгүү'),
        }
        for key, (value_ru, value_ky) in data.items():
            Translation.objects.get_or_create(
                key=key,
                defaults={'value_ru': value_ru, 'value_ky': value_ky},
            )

    # ------------------------------------------------------------------ #
    # Информация о сайте
    # ------------------------------------------------------------------ #
    def create_site_info(self):
        self.stdout.write('Создаю информацию о сайте...')
        if SiteInfo.objects.exists():
            return
        SiteInfo.objects.create(
            about_text='Motion Community — сообщество разработчиков, дизайнеров и ML-инженеров.',
            about_text_ky='Motion Community — иштеп чыгуучулардын, дизайнерлердин жана ML-инженерлердин коомчулугу.',
            contact_email='[email protected]',
            phone='+996 700 000 000',
            instagram='@motion.community',
            telegram='@motion_community',
            linkedin='motion-community',
            location='Бишкек, Кыргызстан',
            location_ky='Бишкек, Кыргызстан',
        )

    # ------------------------------------------------------------------ #
    # Чат
    # ------------------------------------------------------------------ #
    def create_chat(self, users):
        self.stdout.write('Создаю чаты и сообщения...')
        general_chat, _ = Chat.objects.get_or_create(is_general=True, defaults={'name': 'Общий чат'})
        general_chat.person.add(*users.values())

        greetings = [
            ('nurlan_lead', 'Всем привет! Рад видеть новых участников в общем чате 👋'),
            ('eldar', 'Привет! Только присоединился, изучаю проекты на платформе.'),
            ('aigerim_lead', 'Кстати, на следующей неделе созвон по ML-проекту, подключайтесь.'),
            ('camila', 'Обновила прототип дашборда, гляньте в Figma, когда будет время.'),
        ]
        for username, text in greetings:
            Message.objects.get_or_create(
                chat=general_chat,
                sender=users[username],
                text=text,
            )

    # ------------------------------------------------------------------ #
    # Лента активности
    # ------------------------------------------------------------------ #
    def create_activity(self, users):
        self.stdout.write('Создаю ленту активности...')
        entries = [
            ('nurlan_lead', 'Создал проект «Motion Community Platform»'),
            ('aigerim_lead', 'Создал проект «Умный ассистент поддержки»'),
            ('timur', 'Обновил задачу «Реализовать эндпоинты профиля пользователя» (статус: done)'),
            ('meerim', 'Обновил задачу «Собрать датасет частых вопросов» (статус: review)'),
            ('camila', 'Оставил отзыв с оценкой 5'),
        ]
        for username, description in entries:
            Activity.objects.get_or_create(user=users[username], description=description)
