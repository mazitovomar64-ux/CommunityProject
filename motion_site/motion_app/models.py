from django.contrib.auth.models import AbstractUser
from django.db import models


class UserProfile(AbstractUser):
    email = models.EmailField('Почта', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    position = models.CharField('Должность', max_length=150, blank=True)
    bio = models.TextField('О себе', blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    cv_file = models.FileField('Резюме', upload_to='cv/', blank=True, null=True)
    RoleChoices = (('admin', 'Администратор'), ('employee', 'Сотрудник'))
    user_role = models.CharField('Роль', max_length=20, choices=RoleChoices, default='employee')

    def __str__(self):
        return self.get_full_name() or self.email

    def get_average_rating(self):
        ratings = self.review_user.all()
        if ratings.exists():
            return round(sum(i.rating for i in ratings) / ratings.count(), 2)
        return 0

    def get_count_people(self):
        return self.review_user.count()


class Direction(models.Model):
    title = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    icon = models.CharField('Иконка', max_length=10)

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'

    def __str__(self):
        return self.title


class Team(models.Model):
    name = models.CharField('Название команды', max_length=150)
    description = models.TextField('Описание', blank=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.PROTECT, related_name='created_teams', verbose_name='Создал')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members', verbose_name='Команда')
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='team_membership', verbose_name='Пользователь')
    role_in_team = models.CharField('Роль в команде', max_length=100, blank=True)
    joined_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Участник команды'
        verbose_name_plural = 'Участники команд'

    def __str__(self):
        return f'{self.user} — {self.team}'


class Project(models.Model):
    title = models.CharField('Название проекта', max_length=150)
    description = models.TextField('Описание')
    icon = models.CharField('Иконка', max_length=10, blank=True)
    CategoryChoices = (('AI', 'Искусственный интеллект'), ('Web', 'Веб-разработка'), ('LLM', 'LLM / NLP'), ('ML', 'Машинное обучение'), ('Backend', 'Backend'), ('Frontend', 'Frontend'), ('Design', 'Дизайн'))
    category = models.CharField('Категория', max_length=50, choices=CategoryChoices)
    StatusChoices = (('active', 'Активен'), ('review', 'На проверке'), ('done', 'Завершён'), ('on_hold', 'Приостановлен'))
    status = models.CharField('Статус', max_length=20, choices=StatusChoices, default='active')
    created_at = models.DateField('Дата создания', auto_now_add=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.PROTECT, related_name='created_projects', verbose_name='Создал')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name='Команда')

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

    def __str__(self):
        return self.title

    def get_average_rating(self):
        ratings = self.project_review.all()
        if ratings.exists():
            return round(sum(i.rating for i in ratings) / ratings.count(), 2)
        return 0

    def get_count_people(self):
        return self.participants.count()


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='participants', verbose_name='Проект')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='project_memberships', verbose_name='Пользователь')
    role_in_project = models.CharField('Роль в проекте', max_length=100)
    joined_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Участник проекта'
        verbose_name_plural = 'Участники проектов'
        constraints = [models.UniqueConstraint(fields=['project', 'user'], name='unique_project_user')]

    def __str__(self):
        return f'{self.user} — {self.project}'


class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name='Проект')
    title = models.CharField('Название задачи', max_length=200)
    description = models.TextField('Описание')
    PriorityChoices = (('low', 'Низкий'), ('medium', 'Средний'), ('high', 'Высокий'))
    priority = models.CharField('Приоритет', max_length=20, choices=PriorityChoices, default='medium')
    StatusChoices = (('new', 'Новая'), ('hold', 'На паузе'), ('in_progress', 'В работе'), ('review', 'На проверке'), ('done', 'Выполнена'))
    status = models.CharField('Статус', max_length=20, choices=StatusChoices, default='new')
    assigned_to = models.ManyToManyField(UserProfile, related_name='tasks', blank=True, verbose_name='Исполнители')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return self.title


class Activity(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='activities', verbose_name='Пользователь')
    description = models.CharField('Действие', max_length=255)
    created_at = models.DateTimeField('Дата действия', auto_now_add=True)

    class Meta:
        verbose_name = 'Активность'
        verbose_name_plural = 'Активности'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user}: {self.description}'


class SiteInfo(models.Model):
    about_text = models.TextField('О сайте')
    contact_email = models.EmailField('Контактная почта')
    instagram = models.CharField('Instagram', max_length=100)
    telegram = models.CharField('Telegram', max_length=100)
    location = models.CharField('Местоположение', max_length=150)

    class Meta:
        verbose_name = 'Информация о сайте'
        verbose_name_plural = 'Информация о сайте'

    def __str__(self):
        return 'Информация о сайте'


class Review(models.Model):
    text_review = models.TextField('Текст отзыва')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='review_user', verbose_name='Пользователь')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_review', null=True, blank=True, verbose_name='Проект')
    rating = models.PositiveIntegerField('Оценка', choices=[(i, str(i)) for i in range(1, 6)])
    created_date = models.DateTimeField('Дата отзыва', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.user} — {self.rating}'