from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import translation

from motion_app.chat import get_general_chat
from motion_app.models import Direction, Project, ProjectMember, Service, SiteInfo, Task, Translation, UserProfile

DIRECTIONS = [
    # slug, ru, ky, описание ru, описание ky, иконка
    ('django', 'Django', 'Django', 'Backend-разработка на Django и Django REST Framework.', 'Django жана Django REST Framework менен backend иштеп чыгуу.', '🐍'),
    ('flask', 'Flask', 'Flask', 'Лёгкие веб-сервисы и API на Flask.', 'Flask менен жеңил веб-кызматтар жана API.', '🧪'),
    ('frontend', 'Frontend', 'Frontend', 'Пользовательские интерфейсы и клиентская часть сайтов.', 'Колдонуучу интерфейстери жана сайттардын клиенттик бөлүгү.', '🖥'),
    ('ai', 'Искусственный интеллект', 'Жасалма интеллект', 'Решения на основе искусственного интеллекта.', 'Жасалма интеллектке негизделген чечимдер.', '🤖'),
    ('ml', 'Машинное обучение', 'Машиналык окутуу', 'Модели, данные и эксперименты.', 'Моделдер, маалыматтар жана эксперименттер.', '📊'),
    ('computer-vision', 'Computer Vision', 'Computer Vision', 'Работа с изображениями и видео.', 'Сүрөттөр жана видео менен иштөө.', '👁'),
    ('docker', 'Docker', 'Docker', 'Контейнеризация и запуск проектов.', 'Контейнеризация жана долбоорлорду ишке киргизүү.', '🐳'),
]

TRANSLATIONS = [
    # ключ, ru, ky
    ('nav.home', 'Главная', 'Башкы бет'),
    ('nav.projects', 'Проекты', 'Долбоорлор'),
    ('nav.team', 'Команда', 'Команда'),
    ('nav.about', 'О нас', 'Биз жөнүндө'),
    ('nav.services', 'Услуги', 'Кызматтар'),
    ('nav.contacts', 'Контакты', 'Байланыш'),
    ('home.title', 'Motion Community', 'Motion Community'),
    ('home.subtitle', 'Мы превращаем идею в работающий продукт.', 'Биз идеяны иштеп турган продуктка айландырабыз.'),
    ('home.description',
     'IT-сообщество Motion Community — это команда, состоящая из студентов. Мы развиваемся благодаря практике и работе над реальными проектами.',
     'Motion Community IT-жамааты — студенттерден турган команда. Биз практика жана реалдуу долбоорлор менен иштөө аркылуу өнүгөбүз.'),
    ('home.cta.projects', 'Проекты', 'Долбоорлор'),
    ('home.cta.work_with_us', 'Работа с нами', 'Биз менен иштөө'),
    ('projects.title', 'Проекты', 'Долбоорлор'),
    ('team.title', 'Команда', 'Команда'),
    ('services.title', 'Услуги', 'Кызматтар'),
    ('contacts.title', 'Контакты', 'Байланыш'),
    ('about.title', 'О нас', 'Биз жөнүндө'),
    ('about.mission',
     'Motion Community — IT-команда, которая развивается благодаря реальным проектам и практике.',
     'Motion Community — реалдуу долбоорлор жана практика аркылуу өнүгүп жаткан IT-команда.'),
    ('about.goal',
     'Создать среду, в которой студенты могут обучаться через реальные проекты, работать в команде и развивать практические навыки.',
     'Студенттер реалдуу долбоорлор аркылуу окуп, командада иштеп, практикалык көндүмдөрдү өнүктүрө турган чөйрө түзүү.'),
    ('about.focus.1_web', 'Веб-разработка', 'Веб-иштеп чыгуу'),
    ('about.focus.2_ai', 'Искусственный интеллект', 'Жасалма интеллект'),
    ('about.focus.3_ml', 'Машинное обучение', 'Машиналык окутуу'),
    ('about.focus.4_bots', 'Telegram-боты', 'Telegram-боттор'),
    ('about.focus.5_automation', 'Автоматизация', 'Автоматташтыруу'),
    ('about.focus.6_backend', 'Backend-разработка', 'Backend иштеп чыгуу'),
    ('about.focus.7_frontend', 'Frontend-разработка', 'Frontend иштеп чыгуу'),
]

SERVICES = [
    # порядок, ru, ky, описание ru, описание ky, иконка
    (1, 'Решения на основе искусственного интеллекта', 'Жасалма интеллектке негизделген чечимдер',
     'Разрабатываем и внедряем решения на основе искусственного интеллекта для ваших задач.',
     'Сиздин милдеттериңиз үчүн жасалма интеллектке негизделген чечимдерди иштеп чыгабыз жана киргизебиз.', '🤖'),
    (2, 'Запуск и поддержка автоматизации', 'Автоматташтырууну ишке киргизүү жана колдоо',
     'Запускаем и поддерживаем автоматизацию рабочих процессов.',
     'Жумуш процесстерин автоматташтырууну ишке киргизип, колдоп беребиз.', '⚙️'),
    (3, 'Telegram-боты', 'Telegram-боттор',
     'Создаём Telegram-ботов для бизнеса, обучения и сервисов.',
     'Бизнес, окутуу жана сервистер үчүн Telegram-боттор түзөбүз.', '💬'),
    (4, 'Веб-системы', 'Веб-системалар',
     'Проектируем и разрабатываем веб-системы под задачи заказчика.',
     'Кардардын милдеттерине ылайык веб-системаларды долбоорлоп, иштеп чыгабыз.', '🧩'),
    (5, 'Backend и API', 'Backend жана API',
     'Создаём надёжный backend и API для сайтов и мобильных приложений.',
     'Сайттар жана мобилдик тиркемелер үчүн ишенимдүү backend жана API түзөбүз.', '🔌'),
    (6, 'UI/UX дизайн', 'UI/UX дизайн',
     'Проектируем удобные и понятные интерфейсы.',
     'Ыңгайлуу жана түшүнүктүү интерфейстерди долбоорлойбуз.', '🎨'),
    (7, 'Веб-сайты', 'Веб-сайттар',
     'Разрабатываем сайты: от визиток до корпоративных порталов.',
     'Визиткалардан корпоративдик порталдарга чейин сайттарды иштеп чыгабыз.', '🌐'),
    (8, 'Landing pages', 'Landing pages',
     'Делаем лендинги, которые ясно доносят ценность продукта.',
     'Продукттун баалуулугун так жеткирген лендингдерди жасайбыз.', '🚀'),
]

SITE_INFO = {
    'about_text': 'Motion Community — IT-команда, которая развивается благодаря реальным проектам и практике.',
    'about_text_ky': 'Motion Community — реалдуу долбоорлор жана практика аркылуу өнүгүп жаткан IT-команда.',
    'contact_email': 'ElmirabekToktoraliev06@gmail.com',
    'phone': '+996 224 243 7',
    'telegram': '@Elmirbek1',
    'instagram': '@Motion_Community',
    'linkedin': 'Motion Community',
    'location': 'Бишкек, Кыргызстан',
    'location_ky': 'Бишкек, Кыргызстан',
}

# Демонстрационные проекты (учебные): название, описание ru/ky, статус, направления
PROJECTS = [
    ('Табель', 'Табель', 'Учебный проект Motion Community (демо-данные).', 'Motion Community окуу долбоору (демо-маалыматтар).', 'active', ['django', 'docker']),
    ('IBO', 'IBO', 'Учебный проект Motion Community (демо-данные).', 'Motion Community окуу долбоору (демо-маалыматтар).', 'review', ['frontend', 'ai']),
]

DEMO_USERS = [
    # email, username, имя, фамилия, роль, должность
    ('teamlead@example.com', 'teamlead', 'Демо', 'Тимлид', 'team_lead', 'Team Lead'),
    ('employee1@example.com', 'employee1', 'Демо', 'Сотрудник 1', 'employee', 'Backend-разработчик'),
    ('employee2@example.com', 'employee2', 'Демо', 'Сотрудник 2', 'employee', 'Frontend-разработчик'),
]


class Command(BaseCommand):
    help = (
        'Создаёт стартовый публичный контент Motion Community: направления, переводы RU/KY, услуги, '
        'контакты и демо-проекты. По умолчанию ничего не перезаписывает — только добавляет отсутствующее.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--overwrite', action='store_true', help='Привести контент к значениям по умолчанию (перезаписать правки).')
        parser.add_argument('--demo-users', metavar='PASSWORD', help='Создать демо-пользователей (тимлид и 2 сотрудника) с указанным паролем.')

    def handle(self, *args, **options):
        # русский — основной язык: значения без суффикса пишутся в *_ru, кыргызские — в *_ky
        with translation.override('ru'):
            self.run(options)

    @transaction.atomic
    def run(self, options):
        self.overwrite = options['overwrite']

        self.seed_directions()
        self.seed_translations()
        self.seed_services()
        self.seed_site_info()
        get_general_chat()

        demo_users = self.seed_demo_users(options['demo_users']) if options['demo_users'] else []
        self.seed_projects(demo_users)

        self.stdout.write(self.style.SUCCESS('Готово.'))

    def upsert(self, model, lookup, defaults):
        obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
        if not created and self.overwrite:
            for field, value in defaults.items():
                setattr(obj, field, value)
            obj.save()
        return obj

    def seed_directions(self):
        for slug, title, title_ky, description, description_ky, icon in DIRECTIONS:
            defaults = {'title': title, 'title_ky': title_ky, 'description': description, 'description_ky': description_ky, 'icon': icon}
            # если такое направление уже есть (по slug или названию) — используем его, а не создаём дубль
            direction = Direction.objects.filter(slug=slug).first() or Direction.objects.filter(title=title, slug__isnull=True).first()
            if direction:
                if not direction.slug:
                    direction.slug = slug
                if not direction.title_ky:
                    direction.title_ky = title_ky
                if not direction.description_ky:
                    direction.description_ky = description_ky
                if self.overwrite:
                    for field, value in defaults.items():
                        setattr(direction, field, value)
                direction.save()
            else:
                Direction.objects.create(slug=slug, **defaults)
        self.stdout.write(f'Направления: {Direction.objects.count()}')

    def seed_translations(self):
        for key, ru, ky in TRANSLATIONS:
            self.upsert(Translation, {'key': key}, {'value': ru, 'value_ky': ky})
        self.stdout.write(f'Переводы: {Translation.objects.count()}')

    def seed_services(self):
        for order, title, title_ky, description, description_ky, icon in SERVICES:
            self.upsert(Service, {'order': order}, {'title': title, 'title_ky': title_ky, 'description': description, 'description_ky': description_ky, 'icon': icon, 'is_active': True})
        self.stdout.write(f'Услуги: {Service.objects.count()}')

    def seed_site_info(self):
        info = SiteInfo.objects.first()
        if not info:
            SiteInfo.objects.create(**SITE_INFO)
        else:
            for field, value in SITE_INFO.items():
                if self.overwrite or not getattr(info, field):
                    setattr(info, field, value)
            info.save()
        self.stdout.write('Контакты и About: заполнены')

    def seed_demo_users(self, password):
        users = []
        for email, username, first_name, last_name, role, position in DEMO_USERS:
            user, created = UserProfile.objects.get_or_create(email=email, defaults={'username': username, 'first_name': first_name, 'last_name': last_name, 'user_role': role, 'position': position})
            if created or self.overwrite:
                user.user_role = role
                user.set_password(password)
                user.save()
            users.append(user)
        self.stdout.write(f'Демо-пользователи: {len(users)}')
        return users

    def seed_projects(self, demo_users):
        owner = UserProfile.objects.filter(user_role='admin').order_by('id').first() or UserProfile.objects.filter(is_superuser=True).order_by('id').first()
        if not owner:
            self.stdout.write(self.style.WARNING('Демо-проекты пропущены: нет пользователя-администратора.'))
            return

        for title, title_ky, description, description_ky, project_status, slugs in PROJECTS:
            project = Project.objects.filter(title=title).first()
            if not project:
                project = Project.objects.create(title=title, title_ky=title_ky, description=description, description_ky=description_ky, category='Web', status=project_status, created_by=owner)
                project.directions.set(Direction.objects.filter(slug__in=slugs))

            for user in demo_users:
                ProjectMember.objects.get_or_create(project=project, user=user, defaults={'role_in_project': user.position or 'Участник'})

            if demo_users:
                employee = next((u for u in demo_users if u.user_role == 'employee'), None)
                if employee and not project.tasks.exists():
                    task = Task.objects.create(project=project, title='Первое задание', description='Демонстрационное задание для проверки личного кабинета.', priority='medium')
                    task.assigned_to.set([employee])
        self.stdout.write(f'Проекты: {Project.objects.count()}')