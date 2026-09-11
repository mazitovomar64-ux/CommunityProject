from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from motion_app.models import Activity, Direction, Project, ProjectMember, SiteInfo, Task, Team, TeamMember, UserProfile


FAKE_PNG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82'

FAKE_CV_BYTES = b'%PDF-1.4\n% Test CV\n'


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными для проверки сайта'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Удалить старые тестовые данные перед заполнением')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['flush']:
            self.flush_data()

        admin = self.create_admin()
        employees = self.create_employees()

        self.create_site_info()
        self.create_directions()

        team = self.create_team(admin, employees)
        projects = self.create_projects(admin, team, employees)

        self.create_tasks(projects, employees)
        self.create_activities(admin, employees)

        self.print_data()

    def flush_data(self):
        Activity.objects.all().delete()
        Task.objects.all().delete()
        ProjectMember.objects.all().delete()
        Project.objects.all().delete()
        TeamMember.objects.all().delete()
        Team.objects.all().delete()
        Direction.objects.all().delete()
        SiteInfo.objects.all().delete()
        UserProfile.objects.exclude(email='admin@example.com').delete()

        self.stdout.write(
            self.style.WARNING(
                'Старые тестовые данные удалены.'
            )
        )

    def create_admin(self):
        admin, _ = UserProfile.objects.get_or_create(
            email='admin@example.com',
            defaults={'username': 'admin'}
        )

        admin.username = 'admin'
        admin.first_name = 'Айбек'
        admin.last_name = 'К.'
        admin.position = 'Администратор'
        admin.bio = 'Администратор платформы Motion Community.'
        admin.user_role = 'admin'

        admin.is_staff = False
        admin.is_superuser = False

        admin.set_password('admin12345')

        self.attach_files(admin)

        admin.save()

        return admin

    def create_employees(self):
        data = [
            ('user1@example.com', 'Нурбек', 'Абдрахманов', 'Backend-разработчик'),
            ('user2@example.com', 'Алина', 'Иванова', 'Frontend-разработчик'),
            ('user3@example.com', 'Данияр', 'Садыков', 'ML-разработчик'),
            ('user4@example.com', 'Мадина', 'Токтосунова', 'UI/UX-дизайнер'),
            ('user5@example.com', 'Тимур', 'Осмонов', 'Тестировщик'),
        ]

        employees = []

        for index, (email, first_name, last_name, position) in enumerate(data, 1):
            user, _ = UserProfile.objects.get_or_create(
                email=email,
                defaults={'username': f'user{index}'}
            )

            user.username = f'user{index}'
            user.first_name = first_name
            user.last_name = last_name
            user.position = position
            user.bio = f'Сотрудник команды Motion Community. Специализация: {position}.'
            user.user_role = 'employee'

            user.is_staff = False
            user.is_superuser = False

            user.set_password('password123')

            self.attach_files(user)

            user.save()

            employees.append(user)

        return employees

    def attach_files(self, user):
        user.avatar.save(
            f'avatar_{user.username}.png',
            ContentFile(FAKE_PNG_BYTES),
            save=False
        )

        user.cv_file.save(
            f'cv_{user.username}.pdf',
            ContentFile(FAKE_CV_BYTES),
            save=False
        )

    def create_site_info(self):
        SiteInfo.objects.update_or_create(
            id=1,
            defaults={
                'about_text': 'Motion Community — платформа для команд, проектов и совместной работы.',
                'contact_email': 'contact@example.com',
                'instagram': '@motion_community',
                'telegram': '@motion_community',
                'location': 'Бишкек, Кыргызстан'
            }
        )

    def create_directions(self):
        directions = [
            ('Веб-разработка', 'Frontend и backend-разработка.', '💻'),
            ('Машинное обучение', 'Модели, данные и эксперименты.', '📊'),
            ('Computer Vision', 'Работа с изображениями и видео.', '👁'),
            ('LLM / NLP', 'Работа с языковыми моделями и текстом.', '🤖'),
            ('Дизайн', 'UI/UX и визуальный дизайн.', '🎨')
        ]

        for title, description, icon in directions:
            Direction.objects.update_or_create(
                title=title,
                defaults={
                    'description': description,
                    'icon': icon
                }
            )

    def create_team(self, admin, employees):
        team, _ = Team.objects.get_or_create(
            name='Основная команда',
            defaults={
                'description': 'Основная команда Motion Community.',
                'created_by': admin
            }
        )

        team.description = 'Основная команда Motion Community.'
        team.created_by = admin
        team.save()

        roles = [
            'Backend',
            'Frontend',
            'ML',
            'Дизайн',
            'Тестирование'
        ]

        for user, role in zip(employees, roles):
            TeamMember.objects.update_or_create(
                team=team,
                user=user,
                defaults={
                    'role_in_team': role
                }
            )

        return team

    def create_projects(self, admin, team, employees):
        data = [
            (
                'AI-помощник',
                'Разработка интеллектуального помощника для команды.',
                'AI',
                'active'
            ),
            (
                'Сайт Motion Community',
                'Backend API для личного кабинета и команд.',
                'Web',
                'review'
            ),
            (
                'Лаборатория Computer Vision',
                'Эксперименты с обработкой изображений.',
                'ML',
                'done'
            )
        ]

        projects = []

        for title, description, category, project_status in data:
            project, _ = Project.objects.update_or_create(
                title=title,
                defaults={
                    'description': description,
                    'icon': '🚀',
                    'category': category,
                    'status': project_status,
                    'created_by': admin,
                    'team': team
                }
            )

            projects.append(project)

            roles = [
                'Backend-разработчик',
                'Frontend-разработчик',
                'ML-разработчик',
                'UI/UX-дизайнер',
                'Тестировщик'
            ]

            for user, role in zip(employees, roles):
                ProjectMember.objects.update_or_create(
                    project=project,
                    user=user,
                    defaults={
                        'role_in_project': role
                    }
                )

        return projects

    def create_tasks(self, projects, employees):
        for project in projects:
            task1, _ = Task.objects.update_or_create(
                project=project,
                title='Подключить API',
                defaults={
                    'description': 'Подключить API проекта к frontend.',
                    'priority': 'high',
                    'status': 'review'
                }
            )

            task1.assigned_to.set([employees[0]])

            task2, _ = Task.objects.update_or_create(
                project=project,
                title='Подготовить интерфейс',
                defaults={
                    'description': 'Подготовить интерфейс страницы проекта.',
                    'priority': 'medium',
                    'status': 'in_progress'
                }
            )

            task2.assigned_to.set([employees[1]])

            task3, _ = Task.objects.update_or_create(
                project=project,
                title='Проверить результат',
                defaults={
                    'description': 'Провести проверку готовой задачи.',
                    'priority': 'medium',
                    'status': 'new'
                }
            )

            task3.assigned_to.set([employees[4]])

    def create_activities(self, admin, employees):
        Activity.objects.create(
            user=admin,
            description='Создал проект «AI-помощник»'
        )

        Activity.objects.create(
            user=admin,
            description='Добавил нового участника в команду'
        )

        Activity.objects.create(
            user=admin,
            description='Изменил задачу «Подключить API»'
        )

        Activity.objects.create(
            user=employees[0],
            description='Добавлен в команду «Основная команда»'
        )

        Activity.objects.create(
            user=employees[0],
            description='Добавлен в проект «AI-помощник»'
        )

        Activity.objects.create(
            user=employees[0],
            description='Задача «Подключить API» переведена на проверку'
        )

        Activity.objects.create(
            user=employees[1],
            description='Добавлен в проект «Сайт Motion Community»'
        )

        Activity.objects.create(
            user=employees[1],
            description='Назначена новая задача'
        )

    def print_data(self):
        self.stdout.write(
            self.style.SUCCESS(
                'Тестовые данные готовы.'
            )
        )

        self.stdout.write(
            'Администратор: admin@example.com / admin12345'
        )

        self.stdout.write(
            'Сотрудники: user1@example.com ... user5@example.com / password123'
        )