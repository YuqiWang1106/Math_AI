from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .langchain_service import (
    evaluate_assessment,
    ask_with_memory,
    classify_preference_query,
)


class EvaluateAPIView(APIView):
    """
    POST /api/evaluate/
    Body:
    {
        "student_id": "s001",
        "json_data": {...Raw JSON...}
    }

    Return structured evaluation report
    """
    def post(self, request):
        try:
            student_id = request.data.get("student_id", "anonymous")
            json_data = request.data.get("json_data")

            if not json_data:
                return Response({"error": "Missing json_data"}, status=status.HTTP_400_BAD_REQUEST)

            result = evaluate_assessment(student_id, json_data)

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AskAPIView(APIView):
    def post(self, request):
        student_id = request.data.get("student_id", "anonymous")
        question   = request.data.get("question")
        json_data  = request.data.get("json_data")

        if not question or not json_data:
            return Response({"error": "Missing question or json_data"}, status=400)

        try:
            answer = ask_with_memory(student_id, json_data, question)
            return Response({"response": answer}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class PreferenceClassifierAPIView(APIView):
    """
    POST /api/preference/
    Body:
    {
        "preference": "I want to plan a four-year university budget..."
    }
    """

    def post(self, request):
        preference_text = request.data.get("preference")
        if not preference_text:
            return Response({"error": "Missing preference text"}, status=400)
        try:
            result = classify_preference_query(preference_text)
            return Response(result, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)





# class AskAPIView(APIView):
#     """
#     POST /api/ask/
#     Body:
#     {
#         "student_id": "s001",
#         "question": "What is SADMEP?",
#         "json_data": {...Raw JSON...}
#     }

#     Retun AI Tutor Response
#     """
    
    # def post(self, request):
    #     try:
    #         student_id = request.data.get("student_id", "anonymous")
    #         question = request.data.get("question")
    #         json_data = request.data.get("json_data")

    #         if not question or not json_data:
    #             return Response({"error": "Missing question or json_data"}, status=status.HTTP_400_BAD_REQUEST)

    #         response = answer_student_question(question, student_id, json_data)

    #         return Response({"response": response}, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
