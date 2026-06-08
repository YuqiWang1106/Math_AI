from rest_framework import serializers

from .models import AssessmentAttempt, KnowledgeObservation, KnowledgeTrace, Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["external_id", "display_name", "created_at", "updated_at"]


class KnowledgeTraceSerializer(serializers.ModelSerializer):
    knowledge_point = serializers.CharField(source="knowledge_point.name")
    dimension = serializers.CharField(source="knowledge_point.dimension")
    mastery_threshold = serializers.FloatField(source="knowledge_point.mastery_threshold")
    is_mastered = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeTrace
        fields = [
            "knowledge_point",
            "dimension",
            "mastery_probability",
            "mastery_threshold",
            "is_mastered",
            "attempts_count",
            "correct_count",
            "incorrect_count",
            "last_observed_at",
            "last_evidence",
        ]

    def get_is_mastered(self, obj):
        return obj.mastery_probability >= obj.knowledge_point.mastery_threshold


class KnowledgeObservationSerializer(serializers.ModelSerializer):
    knowledge_point = serializers.CharField(source="knowledge_point.name")
    dimension = serializers.CharField(source="knowledge_point.dimension")
    attempt_id = serializers.IntegerField(source="attempt.id")

    class Meta:
        model = KnowledgeObservation
        fields = [
            "attempt_id",
            "knowledge_point",
            "dimension",
            "is_correct",
            "confidence",
            "mastery_before",
            "mastery_after",
            "evidence",
            "created_at",
        ]


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentAttempt
        fields = ["id", "problem", "evaluation_report", "created_at"]
