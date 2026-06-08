from django.db import transaction
from django.db.models import Avg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .growth_algorithms import extract_knowledge_observations, update_bkt_probability
from .langchain_service import answer_student_question, evaluate_self_assessment, create_self_assessment_text
from .models import AssessmentAttempt, KnowledgeObservation, KnowledgePoint, KnowledgeTrace, Student
from .serializers import AssessmentAttemptSerializer, KnowledgeObservationSerializer, KnowledgeTraceSerializer


class EvaluateAPIView(APIView):
    """
    POST /api/evaluate/
    Body:
    {
        "student_id": "s001",
        "json_data": {...Raw JSON...}
    }

    Return structured evaluation report plus persisted growth tracking metadata.
    """

    def post(self, request):
        try:
            student_id = request.data.get("student_id", "anonymous")
            json_data = request.data.get("json_data")

            if not json_data:
                return Response({"error": "Missing json_data"}, status=status.HTTP_400_BAD_REQUEST)

            student_text = create_self_assessment_text(json_data)
            result = evaluate_self_assessment(student_text, student_id)
            growth_summary = record_assessment_growth(student_id, json_data, result)

            response_payload = dict(result) if isinstance(result, dict) else {"evaluation": result}
            response_payload["growth_tracking"] = growth_summary
            return Response(response_payload, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AskAPIView(APIView):
    def post(self, request):
        student_id = request.data.get("student_id", "anonymous")
        question = request.data.get("question")
        json_data = request.data.get("json_data")

        if not question or not json_data:
            return Response({"error": "Missing question or json_data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            answer = answer_student_question(question, student_id, json_data)
            return Response({"response": answer}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentGrowthAPIView(APIView):
    """Return a student's longitudinal mastery traces and observations."""

    def get(self, request, student_id):
        student = Student.objects.filter(external_id=normalize_student_id(student_id)).first()
        if not student:
            return Response(
                {
                    "student_id": normalize_student_id(student_id),
                    "overall_mastery": 0,
                    "attempt_count": 0,
                    "knowledge_traces": [],
                    "observations": [],
                    "attempts": [],
                    "latest_report": None,
                },
                status=status.HTTP_200_OK,
            )

        return Response(build_student_growth_payload(student), status=status.HTTP_200_OK)


@transaction.atomic
def record_assessment_growth(student_id, json_data, evaluation_report):
    normalized_student_id = normalize_student_id(student_id)
    student, _ = Student.objects.get_or_create(external_id=normalized_student_id)
    problem = json_data.get("self_assessment", {}).get("problem", "") if isinstance(json_data, dict) else ""

    attempt = AssessmentAttempt.objects.create(
        student=student,
        problem=problem,
        raw_payload=json_data,
        evaluation_report=evaluation_report if isinstance(evaluation_report, dict) else {"value": evaluation_report},
    )

    observations = extract_knowledge_observations(json_data, attempt.evaluation_report)
    updated_traces = []
    for observation in observations:
        knowledge_point, _ = KnowledgePoint.objects.get_or_create(
            name=observation["knowledge_point"],
            defaults={
                "dimension": observation["dimension"],
                "description": f"Knowledge dimension inferred from self-assessment: {observation['dimension']}",
            },
        )
        trace, _ = KnowledgeTrace.objects.get_or_create(
            student=student,
            knowledge_point=knowledge_point,
            defaults={"mastery_probability": knowledge_point.prior_probability},
        )

        mastery_before = trace.mastery_probability
        mastery_after = update_bkt_probability(
            prior=mastery_before,
            is_correct=observation["is_correct"],
            learn_probability=knowledge_point.learn_probability,
            guess_probability=knowledge_point.guess_probability,
            slip_probability=knowledge_point.slip_probability,
        )

        KnowledgeObservation.objects.create(
            attempt=attempt,
            student=student,
            knowledge_point=knowledge_point,
            is_correct=observation["is_correct"],
            confidence=observation["confidence"],
            mastery_before=mastery_before,
            mastery_after=mastery_after,
            evidence=observation["evidence"],
        )

        trace.mastery_probability = mastery_after
        trace.attempts_count += 1
        if observation["is_correct"]:
            trace.correct_count += 1
        else:
            trace.incorrect_count += 1
        trace.last_observed_at = attempt.created_at
        trace.last_evidence = observation["evidence"]
        trace.save()
        updated_traces.append(trace)

    overall_mastery = compute_overall_mastery(student)
    return {
        "student_id": student.external_id,
        "attempt_id": attempt.id,
        "overall_mastery": overall_mastery,
        "updated_knowledge_points": KnowledgeTraceSerializer(updated_traces, many=True).data,
        "algorithm": {
            "name": "Bayesian Knowledge Tracing",
            "parameters": ["prior_probability", "learn_probability", "guess_probability", "slip_probability"],
            "mastery_threshold": 0.95,
            "source": "Corbett and Anderson knowledge tracing model",
        },
    }


def build_student_growth_payload(student):
    traces = KnowledgeTrace.objects.filter(student=student).select_related("knowledge_point")
    observations = KnowledgeObservation.objects.filter(student=student).select_related("knowledge_point", "attempt")
    attempts = AssessmentAttempt.objects.filter(student=student)
    latest_attempt = attempts.first()

    return {
        "student_id": student.external_id,
        "overall_mastery": compute_overall_mastery(student),
        "attempt_count": attempts.count(),
        "knowledge_traces": KnowledgeTraceSerializer(traces, many=True).data,
        "observations": KnowledgeObservationSerializer(observations, many=True).data,
        "attempts": AssessmentAttemptSerializer(attempts, many=True).data,
        "latest_report": latest_attempt.evaluation_report if latest_attempt else None,
    }


def compute_overall_mastery(student):
    aggregate = KnowledgeTrace.objects.filter(student=student).aggregate(value=Avg("mastery_probability"))
    return round(aggregate["value"] or 0, 4)


def normalize_student_id(student_id):
    return str(student_id or "anonymous").strip() or "anonymous"
