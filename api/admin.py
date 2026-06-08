from django.contrib import admin

from .models import AssessmentAttempt, KnowledgeObservation, KnowledgePoint, KnowledgeTrace, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("external_id", "display_name", "created_at", "updated_at")
    search_fields = ("external_id", "display_name")


@admin.register(KnowledgePoint)
class KnowledgePointAdmin(admin.ModelAdmin):
    list_display = ("name", "dimension", "prior_probability", "learn_probability", "guess_probability", "slip_probability")
    list_filter = ("dimension",)
    search_fields = ("name", "description")


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "created_at")
    list_filter = ("created_at",)
    search_fields = ("student__external_id", "problem")


@admin.register(KnowledgeTrace)
class KnowledgeTraceAdmin(admin.ModelAdmin):
    list_display = ("student", "knowledge_point", "mastery_probability", "attempts_count", "correct_count", "incorrect_count")
    list_filter = ("knowledge_point__dimension",)
    search_fields = ("student__external_id", "knowledge_point__name")


@admin.register(KnowledgeObservation)
class KnowledgeObservationAdmin(admin.ModelAdmin):
    list_display = ("student", "knowledge_point", "is_correct", "mastery_before", "mastery_after", "created_at")
    list_filter = ("is_correct", "knowledge_point__dimension", "created_at")
    search_fields = ("student__external_id", "knowledge_point__name")
