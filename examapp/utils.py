from .models import *
from datetime import datetime, timedelta, time, date
from django.utils.timezone import now, localtime
import random
from django.utils import timezone


def auto_create_exams(number):
    exams_created = 0
    created_exam_ids = []
    
    if timezone.localtime(timezone.now()).weekday() == 6:  # Sunday is represented by 6
        print("❌ No exams created on Sundays.")
        return exams_created, created_exam_ids
    for i in range(number):
        try:
            exam_type, _ = ExamType.objects.get_or_create(name='Ibivanze')
            questions = Question.objects.order_by('?')[:20]
            if questions.count() < 20:
                continue

            last_exam = Exam.objects.filter(for_scheduling=True).order_by('-created_at').first()
            next_hour = (last_exam.schedule_hour.hour + 1 if last_exam and last_exam.schedule_hour else 8) % 24
            next_hour = next_hour if next_hour >= 8 and next_hour <= 15 else 8

            exam_schedule_hour = time(next_hour, 0)

            exam = Exam.objects.create(
                exam_type=exam_type,
                schedule_hour=exam_schedule_hour,
                duration=20,
                for_scheduling=True,
                is_active=False,
            )
            exam.questions.set(questions)
            created_exam_ids.append(exam.id)
            exams_created += 1

        except Exception as e:
            print(f"Error: {e}")

    return exams_created, created_exam_ids

