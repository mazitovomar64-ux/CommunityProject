"""
Management-команда для заполнения БД тестовыми данными.

КУДА ПОЛОЖИТЬ:
    your_app/management/commands/populate_db.py
(нужны также пустые файлы your_app/management/__init__.py
 и your_app/management/commands/__init__.py)

ВАЖНО: замени `your_app` в импорте ниже на реальное имя своего приложения.

УСТАНОВКА ЗАВИСИМОСТИ:
    pip install Faker

ЗАПУСК:
    python manage.py populate_db
    python manage.py populate_db --flush   # сначала очистить старые данные
"""

import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from faker import Faker

from motion_app.models import (
    UserProfile,
    Direction,
    Project,
    ProjectMember,
    Task,
    Activity,
    SiteInfo,
)

fake = Faker("ru_RU")

# Крошечный валидный PNG 1x1 — заглушка для аватара
FAKE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
)
FAKE_CV_BYTES = b"%PDF-1.4\n% Fake CV placeholder file\n"

ICONS = ["\U0001F4C1", "\U0001F680", "\U0001F916", "\U0001F4CA", "\U0001F310", "\U0001F4A1"]

DIRECTIONS_DATA = [
    ("Web-разработка", "Frontend и backend направление"),
    ("Machine Learning", "Модели, данные, эксперименты"),
    ("Computer Vision", "Обработка изображений и видео"),
    ("LLM / NLP", "Работа с языковыми моделями"),
    ("Design", "UI/UX и графический дизайн"),
]

PROJECT_TITLES = [
    "Geo Insights", "SmartCV Parser", "ChatOps Assistant", "VisionGuard",
    "OCR Scanner Pro", "Community Hub", "PortfolioBuilder", "DataMap",
]

TASK_TITLES = [
    "Настроить окружение", "Написать модели", "Сверстать главную страницу",
    "Подключить API", "Написать тесты", "Провести код-ревью",
    "Оптимизировать запросы", "Задеплоить на сервер", "Исправить баги",
    "Подготовить презентацию",
]

ROLES_IN_PROJECT = ["Team Lead", "Developer", "Designer", "QA", "Analyst", "Mentor"]


class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми данными"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Удалить существующие данные перед заполнением",
        )
        parser.add_argument(
            "--users",
            type=int,
            default=15,
            help="Количество пользователей для создания (по умолчанию 15)",
        )
        parser.add_argument(
            "--projects",
            type=int,
            default=6,
            help="Количество проектов для создания (по умолчанию 6)",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["flush"]:
                self._flush()

            self.stdout.write("Создаю SiteInfo...")
            self._create_site_info()

            self.stdout.write("Создаю направления (Direction)...")
            self._create_directions()

            self.stdout.write("Создаю пользователей...")
            users = self._create_users(options["users"])

            self.stdout.write("Создаю проекты...")
            projects = self._create_projects(options["projects"])

            self.stdout.write("Создаю участников проектов...")
            self._create_project_members(users, projects)

            self.stdout.write("Создаю задачи...")
            self._create_tasks(projects, users)

            self.stdout.write("Создаю активности...")
            self._create_activities(users)

        self.stdout.write(self.style.SUCCESS("База данных успешно заполнена!"))

    # ------------------------------------------------------------------

    def _flush(self):
        Activity.objects.all().delete()
        Task.objects.all().delete()
        ProjectMember.objects.all().delete()
        Project.objects.all().delete()
        Direction.objects.all().delete()
        SiteInfo.objects.all().delete()
        UserProfile.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.WARNING("Старые данные удалены."))

    def _create_site_info(self):
        SiteInfo.objects.get_or_create(
            id=1,
            defaults=dict(
                about_text=fake.paragraph(nb_sentences=5),
                contact_email="contact@example.com",
                instagram="@our_team",
                telegram="@our_team_chat",
                location=fake.city(),
            ),
        )

    def _create_directions(self):
        for title, desc in DIRECTIONS_DATA:
            Direction.objects.get_or_create(
                title=title,
                defaults=dict(description=desc, icon=random.choice(ICONS)),
            )

    def _create_users(self, count):
        users = []

        # один админ для удобства входа в систему
        admin, created = UserProfile.objects.get_or_create(
            email="admin@example.com",
            defaults=dict(
                username="admin",
                first_name="Админ",
                last_name="Админов",
                position="Администратор",
                bio=fake.paragraph(nb_sentences=3),
                user_role="admin",
                is_staff=True,
                is_superuser=True,
            ),
        )
        if created:
            admin.set_password("admin12345")
            self._attach_files(admin)
            admin.save()
        users.append(admin)

        roles = ["employee", "student"]
        for i in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"user{i}_{fake.user_name()}@example.com"
            role = random.choice(roles)

            user, created = UserProfile.objects.get_or_create(
                email=email,
                defaults=dict(
                    username=f"user_{i}_{fake.user_name()}",
                    first_name=first_name,
                    last_name=last_name,
                    position=fake.job(),
                    bio=fake.paragraph(nb_sentences=4),
                    user_role=role,
                    is_staff=(role == "employee"),
                ),
            )
            if created:
                user.set_password("password123")
                self._attach_files(user)
                user.save()
            users.append(user)

        return users

    def _attach_files(self, user):
        """Прикрепляем заглушки-файлы для обязательных полей avatar/cv_file."""
        user.avatar.save(
            f"avatar_{user.username}.png", ContentFile(FAKE_PNG_BYTES), save=False
        )
        user.cv_file.save(
            f"cv_{user.username}.pdf", ContentFile(FAKE_CV_BYTES), save=False
        )

    def _create_projects(self, count):
        categories = [c[0] for c in Project.CategoryChoices]
        statuses = [s[0] for s in Project.StatusChoices]
        projects = []

        titles = random.sample(PROJECT_TITLES, min(count, len(PROJECT_TITLES)))
        # если нужно больше проектов, чем уникальных названий — добираем с суффиксом
        while len(titles) < count:
            titles.append(f"{random.choice(PROJECT_TITLES)} {len(titles) + 1}")

        for title in titles:
            project, _ = Project.objects.get_or_create(
                title=title,
                defaults=dict(
                    description=fake.paragraph(nb_sentences=4),
                    icon=random.choice(ICONS),
                    category=random.choice(categories),
                    status=random.choice(statuses),
                ),
            )
            projects.append(project)

        return projects

    def _create_project_members(self, users, projects):
        for project in projects:
            members_count = random.randint(2, min(5, len(users)))
            members = random.sample(users, members_count)
            for user in members:
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=user,
                    defaults=dict(role_in_project=random.choice(ROLES_IN_PROJECT)),
                )

    def _create_tasks(self, projects, users):
        priorities = [p[0] for p in Task.PriorityChoices]
        statuses = [s[0] for s in Task.StatusChoices]

        for project in projects:
            project_users = list(
                UserProfile.objects.filter(project_memberships__project=project)
            ) or users

            tasks_count = random.randint(3, 6)
            titles = random.sample(TASK_TITLES, min(tasks_count, len(TASK_TITLES)))

            for title in titles:
                task = Task.objects.create(
                    project=project,
                    title=title,
                    description=fake.paragraph(nb_sentences=3),
                    priority=random.choice(priorities),
                    status=random.choice(statuses),
                )
                assignees = random.sample(
                    project_users, min(random.randint(1, 3), len(project_users))
                )
                task.assigned_to.set(assignees)

    def _create_activities(self, users):
        actions = [
            "обновил(а) профиль",
            "создал(а) новую задачу",
            "завершил(а) задачу",
            "присоединился(лась) к проекту",
            "оставил(а) комментарий",
            "загрузил(а) файл",
        ]
        for user in users:
            for _ in range(random.randint(2, 5)):
                Activity.objects.create(
                    user=user,
                    description=f"{random.choice(actions)}",
                )