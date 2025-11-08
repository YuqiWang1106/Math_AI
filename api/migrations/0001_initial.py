from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="KnowledgeBaseEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain", models.CharField(max_length=64)),
                ("branch", models.CharField(max_length=64)),
                ("title", models.CharField(blank=True, max_length=128)),
                ("llm_version", models.CharField(blank=True, max_length=64)),
                ("content", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "unique_together": {("domain", "branch")},
            },
        ),
        migrations.AddIndex(
            model_name="knowledgebaseentry",
            index=models.Index(fields=["domain", "branch"], name="api_knowled_domain_46fef2_idx"),
        ),
    ]
