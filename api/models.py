from django.db import models


class KnowledgeBaseEntry(models.Model):
    domain = models.CharField(max_length=64)
    branch = models.CharField(max_length=64)
    title = models.CharField(max_length=128, blank=True)
    llm_version = models.CharField(max_length=64, blank=True)
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("domain", "branch")
        indexes = [
            models.Index(fields=["domain", "branch"]),
        ]

    def __str__(self):
        return f"{self.domain}:{self.branch}"
