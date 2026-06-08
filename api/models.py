from django.db import models
from django.utils import timezone


class Student(models.Model):
    external_id = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.external_id


class KnowledgePoint(models.Model):
    DIMENSION_CHOICES = [
        ("facts", "Facts"),
        ("strategies", "Strategies"),
        ("procedures", "Procedures"),
        ("rationales", "Rationales"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=255, unique=True)
    dimension = models.CharField(max_length=32, choices=DIMENSION_CHOICES, default="other")
    description = models.TextField(blank=True)
    prior_probability = models.FloatField(default=0.35)
    learn_probability = models.FloatField(default=0.18)
    guess_probability = models.FloatField(default=0.2)
    slip_probability = models.FloatField(default=0.1)
    mastery_threshold = models.FloatField(default=0.95)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["dimension", "name"]

    def __str__(self):
        return self.name


class AssessmentAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="assessment_attempts")
    problem = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict)
    evaluation_report = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.external_id} @ {self.created_at:%Y-%m-%d %H:%M}"


class KnowledgeTrace(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="knowledge_traces")
    knowledge_point = models.ForeignKey(KnowledgePoint, on_delete=models.CASCADE, related_name="student_traces")
    mastery_probability = models.FloatField(default=0.35)
    attempts_count = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    last_observed_at = models.DateTimeField(null=True, blank=True)
    last_evidence = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "knowledge_point")
        ordering = ["knowledge_point__dimension", "knowledge_point__name"]

    def __str__(self):
        return f"{self.student.external_id} - {self.knowledge_point.name}: {self.mastery_probability:.2f}"


class KnowledgeObservation(models.Model):
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name="knowledge_observations")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="knowledge_observations")
    knowledge_point = models.ForeignKey(KnowledgePoint, on_delete=models.CASCADE, related_name="observations")
    is_correct = models.BooleanField()
    confidence = models.FloatField(default=0.7)
    mastery_before = models.FloatField()
    mastery_after = models.FloatField()
    evidence = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at", "knowledge_point__dimension"]

    def __str__(self):
        result = "correct" if self.is_correct else "needs work"
        return f"{self.student.external_id} - {self.knowledge_point.name} - {result}"
