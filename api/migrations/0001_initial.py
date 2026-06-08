# Generated manually for student growth tracking.
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(max_length=128, unique=True)),
                ('display_name', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='KnowledgePoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('dimension', models.CharField(choices=[('facts', 'Facts'), ('strategies', 'Strategies'), ('procedures', 'Procedures'), ('rationales', 'Rationales'), ('other', 'Other')], default='other', max_length=32)),
                ('description', models.TextField(blank=True)),
                ('prior_probability', models.FloatField(default=0.35)),
                ('learn_probability', models.FloatField(default=0.18)),
                ('guess_probability', models.FloatField(default=0.2)),
                ('slip_probability', models.FloatField(default=0.1)),
                ('mastery_threshold', models.FloatField(default=0.95)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['dimension', 'name'],
            },
        ),
        migrations.CreateModel(
            name='AssessmentAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem', models.TextField(blank=True)),
                ('raw_payload', models.JSONField(default=dict)),
                ('evaluation_report', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assessment_attempts', to='api.student')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='KnowledgeTrace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mastery_probability', models.FloatField(default=0.35)),
                ('attempts_count', models.PositiveIntegerField(default=0)),
                ('correct_count', models.PositiveIntegerField(default=0)),
                ('incorrect_count', models.PositiveIntegerField(default=0)),
                ('last_observed_at', models.DateTimeField(blank=True, null=True)),
                ('last_evidence', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('knowledge_point', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_traces', to='api.knowledgepoint')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='knowledge_traces', to='api.student')),
            ],
            options={
                'ordering': ['knowledge_point__dimension', 'knowledge_point__name'],
                'unique_together': {('student', 'knowledge_point')},
            },
        ),
        migrations.CreateModel(
            name='KnowledgeObservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_correct', models.BooleanField()),
                ('confidence', models.FloatField(default=0.7)),
                ('mastery_before', models.FloatField()),
                ('mastery_after', models.FloatField()),
                ('evidence', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='knowledge_observations', to='api.assessmentattempt')),
                ('knowledge_point', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='observations', to='api.knowledgepoint')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='knowledge_observations', to='api.student')),
            ],
            options={
                'ordering': ['created_at', 'knowledge_point__dimension'],
            },
        ),
    ]
