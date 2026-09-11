from django.db import migrations, models
import django.db.models.deletion


def set_project_creators(apps, schema_editor):
    UserProfile = apps.get_model('motion_app', 'UserProfile')
    Project = apps.get_model('motion_app', 'Project')

    user = UserProfile.objects.order_by('id').first()

    if user:
        Project.objects.filter(created_by__isnull=True).update(created_by=user.id)
    else:
        Project.objects.all().delete()


def remove_duplicate_project_members(apps, schema_editor):
    ProjectMember = apps.get_model('motion_app', 'ProjectMember')

    seen = set()

    for member in ProjectMember.objects.order_by('id'):
        key = (member.project_id, member.user_id)

        if key in seen:
            member.delete()
        else:
            seen.add(key)


def reset_system_permissions(apps, schema_editor):
    UserProfile = apps.get_model('motion_app', 'UserProfile')
    UserProfile.objects.all().update(is_staff=False, is_superuser=False)


class Migration(migrations.Migration):

    dependencies = [
        ('motion_app', '0003_alter_userprofile_user_role_review')
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Название команды')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_teams', to='motion_app.userprofile', verbose_name='Создал')),
            ],
            options={
                'verbose_name': 'Команда',
                'verbose_name_plural': 'Команды'
            }
        ),

        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_in_team', models.CharField(blank=True, max_length=100, verbose_name='Роль в команде')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='motion_app.team', verbose_name='Команда')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='team_membership', to='motion_app.userprofile', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Участник команды',
                'verbose_name_plural': 'Участники команд'
            }
        ),

        migrations.AddField(
            model_name='project',
            name='created_by',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='created_projects',
                to='motion_app.userprofile',
                verbose_name='Создал'
            )
        ),

        migrations.AddField(
            model_name='project',
            name='team',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projects',
                to='motion_app.team',
                verbose_name='Команда'
            )
        ),

        migrations.AddField(
            model_name='projectmember',
            name='joined_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
        ),

        migrations.AddField(
            model_name='task',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
        ),

        migrations.RunPython(
            set_project_creators,
            migrations.RunPython.noop
        ),

        migrations.RunPython(
            remove_duplicate_project_members,
            migrations.RunPython.noop
        ),

        migrations.RunPython(
            reset_system_permissions,
            migrations.RunPython.noop
        ),

        migrations.AlterField(
            model_name='project',
            name='created_by',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='created_projects',
                to='motion_app.userprofile',
                verbose_name='Создал'
            )
        ),

        migrations.AlterField(
            model_name='project',
            name='icon',
            field=models.CharField(blank=True, max_length=10, verbose_name='Иконка')
        ),

        migrations.AlterField(
            model_name='userprofile',
            name='position',
            field=models.CharField(blank=True, max_length=150, verbose_name='Должность')
        ),

        migrations.AlterField(
            model_name='userprofile',
            name='bio',
            field=models.TextField(blank=True, verbose_name='О себе')
        ),

        migrations.AlterField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Аватар')
        ),

        migrations.AlterField(
            model_name='userprofile',
            name='cv_file',
            field=models.FileField(blank=True, null=True, upload_to='cv/', verbose_name='Резюме')
        ),

        migrations.AlterField(
            model_name='userprofile',
            name='user_role',
            field=models.CharField(
                choices=[
                    ('admin', 'Администратор'),
                    ('employee', 'Сотрудник')
                ],
                default='employee',
                max_length=20,
                verbose_name='Роль'
            )
        ),

        migrations.AddConstraint(
            model_name='projectmember',
            constraint=models.UniqueConstraint(
                fields=('project', 'user'),
                name='unique_project_user'
            )
        ),

        migrations.AlterField(
            model_name='task',
            name='assigned_to',
            field=models.ManyToManyField(
                blank=True,
                related_name='tasks',
                to='motion_app.userprofile',
                verbose_name='Исполнители'
            )
        ),
    ]