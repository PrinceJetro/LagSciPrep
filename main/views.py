from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Course, Topic, PastQuestionsObj
from django import forms
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.db.models import Avg

class CBTForm(forms.Form):
    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        super().__init__(*args, **kwargs)
        self.fields['selected_option'] = forms.ChoiceField(
            choices=[
                ('A', question.option_a),
                ('B', question.option_b),
                ('C', question.option_c),
                ('D', question.option_d)
            ],
            widget=forms.RadioSelect,
            required=False,
        )


import random, time

import random, time, json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Course, PastQuestionsObj


def start_cbt(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        questions = list(course.objective_questions.all())
        selected = random.sample(questions, min(15, len(questions)))

        request.session['cbt_course_id'] = course.id
        request.session['cbt_selected_questions'] = [q.id for q in selected]
        request.session['cbt_learn_mode'] = request.POST.get('learn_mode') == 'on'
        request.session['cbt_end_time'] = time.time() + (7 * 60 + 30)

        return redirect('cbt_exam')

    course = get_object_or_404(Course, id=course_id)
    return render(request, 'cbt_mode_select.html', {'course': course})


def cbt_exam(request):
    """Serves the CBT page (HTML only)"""
    course_id = request.session.get('cbt_course_id')
    if not course_id:
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    return render(request, 'cbt_exam.html', {'course': course})


def cbt_data(request):
    """Returns ALL questions ONCE"""
    course_id = request.session.get('cbt_course_id')
    ids = request.session.get('cbt_selected_questions', [])
    learn_mode = request.session.get('cbt_learn_mode', False)
    end_time = request.session.get('cbt_end_time')

    if not course_id or not ids:
        return JsonResponse({'error': 'Session expired'}, status=400)

    questions = list(PastQuestionsObj.objects.filter(id__in=ids))
    questions.sort(key=lambda q: ids.index(q.id))

    payload = []
    for q in questions:
        payload.append({
            'id': q.id,
            'question': q.question_text,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d,
            },
            'correct': q.correct_option,
            'explanation': q.explanation or "No explanation provided",
            'hint': q.hint or "",
        })

    remaining = int(end_time - time.time()) if end_time else None

    return JsonResponse({
        'questions': payload,
        'learn_mode': learn_mode,
        'remaining': remaining,
    })


@csrf_exempt
def cbt_submit_answers(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid'}, status=400)

    data = json.loads(request.body)
    request.session['cbt_answers'] = data.get('answers', {})

    return JsonResponse({'status': 'ok'})


def cbt_submit(request):
    course_id = request.session.get('cbt_course_id')
    answers = request.session.get('cbt_answers', {})
    ids = request.session.get('cbt_selected_questions', [])

    if not course_id:
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    questions = list(PastQuestionsObj.objects.filter(id__in=ids))
    questions.sort(key=lambda q: ids.index(q.id))

    score = 0
    failed = []

    for q in questions:
        ans = answers.get(str(q.id))
        if ans == q.correct_option:
            score += 1
        else:
            failed.append({
                'question': q,
                'your_answer': ans,
                'correct_answer': q.correct_option,
                'explanation': q.explanation
            })

    total = len(questions)
    percent = (score / total) * 100 if total else 0

    # clear session
    for key in [
        'cbt_course_id',
        'cbt_selected_questions',
        'cbt_learn_mode',
        'cbt_answers',
        'cbt_end_time'
    ]:
        request.session.pop(key, None)

    return render(request, 'cbt_submit.html', {
        'course': course,
        'score': score,
        'total': total,
        'percent': percent,
        'failed_questions': failed
    })

def home(request):
    courses = Course.objects.all()
    return render(request, "home.html", {"courses": courses})

def course_list(request):
    courses = Course.objects.all()
    return render(request, "course_list.html", {"courses": courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    topics = course.topics.all()
    obj_questions_count = course.objective_questions.count()
    return render(request, "course_detail.html", {
        "course": course,
        "topics": topics,
        "obj_questions_count": obj_questions_count,
    })


def get_obj_questions(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    obj_questions = course.objective_questions.all()
    return render(request, "partials/obj_questions_list.html", {
        "obj_questions": obj_questions,
    })


def course_obj_questions(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    obj_questions = course.objective_questions.all()
    return render(request, "obj_questions_course.html", {
        "course": course,
        "obj_questions": obj_questions,
    })


def get_topic_obj_questions(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    obj_questions = topic.course.objective_questions.all()
    return render(request, "partials/obj_questions_topic_list.html", {
        "obj_questions": obj_questions,
    })


def topic_obj_questions(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    course = topic.course
    # get the objective questions for this topic
    obj_questions = topic.questions.all()
    return render(request, "obj_questions_topic.html", {
        "topic": topic,
        "course": course,
        "obj_questions": obj_questions,
    })


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    course = topic.course
    obj_questions_count = course.objective_questions.count()
    return render(request, "topic_detail.html", {
        "topic": topic,
        "course": course,
        "obj_questions_count": obj_questions_count,
    })


def obj_question_detail(request, question_id):
    question = get_object_or_404(PastQuestionsObj, id=question_id)
    if question.explanation:
        question.explanation = question.explanation.replace("\n", "<br>").replace("---", "<hr>")
    else:
        question.explanation = "No explanation provided."
    
    # Get all questions from the same course, ordered by id
    all_questions = list(PastQuestionsObj.objects.filter(course=question.course).order_by('id'))
    current_index = all_questions.index(question)
    
    # Get next and previous questions
    prev_question = all_questions[current_index - 1] if current_index > 0 else None
    next_question = all_questions[current_index + 1] if current_index < len(all_questions) - 1 else None
    
    return render(request, "obj_question_detail.html", {
        "question": question,
        "prev_question": prev_question,
        "next_question": next_question,
        "current_index": current_index + 1,  # 1-indexed for display
        "total_questions": len(all_questions)
    })


import time, json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Topic, PastQuestionsObj


def start_topic_cbt(request, topic_id):
    if request.method == 'POST':
        topic = get_object_or_404(Topic, id=topic_id)
        questions = list(topic.questions.all())

        if not questions:
            messages.error(request, 'No CBT questions available for this topic.')
            return redirect('topic_detail', topic_id=topic_id)

        request.session['cbt_topic_id'] = topic.id
        request.session['cbt_topic_selected_questions'] = [q.id for q in questions]
        request.session['cbt_topic_learn_mode'] = request.POST.get('learn_mode') == 'on'
        request.session['cbt_topic_end_time'] = time.time() + len(questions) * 60

        return redirect('topic_cbt_exam')

    topic = get_object_or_404(Topic, id=topic_id)
    return render(request, 'topic_cbt_mode_select.html', {'topic': topic})


def topic_cbt_exam(request):
    topic_id = request.session.get('cbt_topic_id')
    if not topic_id:
        return redirect('home')

    topic = get_object_or_404(Topic, id=topic_id)
    return render(request, 'topic_cbt_exam.html', {'topic': topic})


def topic_cbt_data(request):
    topic_id = request.session.get('cbt_topic_id')
    ids = request.session.get('cbt_topic_selected_questions', [])
    learn_mode = request.session.get('cbt_topic_learn_mode', False)
    end_time = request.session.get('cbt_topic_end_time')

    if not topic_id or not ids:
        return JsonResponse({'error': 'Session expired'}, status=400)

    questions = list(PastQuestionsObj.objects.filter(id__in=ids))
    questions.sort(key=lambda q: ids.index(q.id))

    payload = []
    for q in questions:
        payload.append({
            'id': q.id,
            'question': q.question_text,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d,
            },
            'correct': q.correct_option,
            'explanation': q.explanation or "No explanation provided",
            'hint': q.hint or "",
        })

    remaining = int(end_time - time.time()) if end_time else None

    return JsonResponse({
        'questions': payload,
        'learn_mode': learn_mode,
        'remaining': remaining,
    })


@csrf_exempt
def topic_cbt_submit_answers(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    data = json.loads(request.body)
    request.session['cbt_topic_answers'] = data.get('answers', {})

    return JsonResponse({'status': 'ok'})


def topic_cbt_submit(request):
    topic_id = request.session.get('cbt_topic_id')
    answers = request.session.get('cbt_topic_answers', {})
    ids = request.session.get('cbt_topic_selected_questions', [])

    if not topic_id:
        return redirect('home')

    topic = get_object_or_404(Topic, id=topic_id)
    questions = list(PastQuestionsObj.objects.filter(id__in=ids))
    questions.sort(key=lambda q: ids.index(q.id))

    score = 0
    failed = []

    for q in questions:
        ans = answers.get(str(q.id))
        if ans == q.correct_option:
            score += 1
        else:
            failed.append({
                'question': q,
                'your_answer': ans,
                'correct_answer': q.correct_option,
                'explanation': q.explanation
            })

    percent = (score / len(questions)) * 100 if questions else 0

    # clear session
    for key in [
        'cbt_topic_id',
        'cbt_topic_answers',
        'cbt_topic_selected_questions',
        'cbt_topic_learn_mode',
        'cbt_topic_end_time'
    ]:
        request.session.pop(key, None)

    return render(request, 'topic_cbt_submit.html', {
        'topic': topic,
        'score': score,
        'total': len(questions),
        'percent': percent,
        'failed_questions': failed
    })

def custom_logout(request):
    """
    Custom logout view with confirmation page
    """
    if request.method == 'POST':
        # User confirmed logout
        print("Here")
        logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect('home')
    
"""
from main.models import Course, Topic, PastQuestionsObj, PastQuestionsTheory

# Create Courses
course1 = Course.objects.create(name="Mathematics")
course2 = Course.objects.create(name="English")

# Create Topics
topic1 = Topic.objects.create(name="Algebra", content="Algebra basics", course=course1)
topic2 = Topic.objects.create(name="Grammar", content="Grammar rules", course=course2)

# Create PastQuestionsObj
# Mathematics - Algebra
PastQuestionsObj.objects.create(
    course=course1,
    topic=topic1,
    question_text="Solve for x: 3x + 7 = 22",
    option_a="x = 3",
    option_b="x = 5",
    option_c="x = 6",
    option_d="x = 4",
    correct_option="B",
)

PastQuestionsObj.objects.create(
    course=course1,
    topic=topic1,
    question_text="What is the value of y in 2y - 8 = 12?",
    option_a="y = 8",
    option_b="y = 12",
    option_c="y = 10",
    option_d="y = 6",
    correct_option="C",
)

PastQuestionsObj.objects.create(
    course=course1,
    topic=topic1,
    question_text="Factorize: x² + 5x + 6",
    option_a="(x+2)(x+3)",
    option_b="(x+1)(x+6)",
    option_c="(x+2)(x+4)",
    option_d="(x+3)(x+3)",
    correct_option="A",
)

PastQuestionsObj.objects.create(
    course=course1,
    topic=topic1,
    question_text="Simplify: (3x²y³)²",
    option_a="6x⁴y⁶",
    option_b="9x⁴y⁵",
    option_c="9x⁴y⁶",
    option_d="3x⁴y⁶",
    correct_option="C",
)

PastQuestionsObj.objects.create(
    course=course1,
    topic=topic1,
    question_text="Solve the equation: 4(x-3) = 20",
    option_a="x = 5",
    option_b="x = 8",
    option_c="x = 7",
    option_d="x = 6",
    correct_option="B",
)

# English - Grammar
PastQuestionsObj.objects.create(
    course=course2,
    topic=topic2,
    question_text="Which sentence is grammatically correct?",
    option_a="She don't like apples.",
    option_b="She doesn't likes apples.",
    option_c="She doesn't like apples.",
    option_d="She don't likes apples.",
    correct_option="C",
)

PastQuestionsObj.objects.create(
    course=course2,
    topic=topic2,
    question_text="Choose the correct plural form of 'child'",
    option_a="childs",
    option_b="children",
    option_c="childes",
    option_d="childern",
    correct_option="B",
)

PastQuestionsObj.objects.create(
    course=course2,
    topic=topic2,
    question_text="Identify the correct past tense of 'go'",
    option_a="goed",
    option_b="went",
    option_c="gone",
    option_d="goes",
    correct_option="B",
)

PastQuestionsObj.objects.create(
    course=course2,
    topic=topic2,
    question_text="Which is the correct comparative form of 'good'?",
    option_a="gooder",
    option_b="more good",
    option_c="better",
    option_d="best",
    correct_option="C",
)

PastQuestionsObj.objects.create(
    course=course2,
    topic=topic2,
    question_text="Select the properly punctuated sentence",
    option_a="I like apples oranges and bananas.",
    option_b="I like apples, oranges and bananas.",
    option_c="I like apples, oranges, and bananas.",
    option_d="I like apples oranges, and bananas.",
    correct_option="C",
)

# Create PastQuestionsTheory
# Mathematics Theory Questions
PastQuestionsTheory.objects.create(
    course=course1,
    question_text="Explain the difference between linear equations and quadratic equations with examples.",
PastQuestionsTheory.objects.create(
    course=course1,
    question_text="Describe the process of solving simultaneous equations using both substitution and elimination methods.",
PastQuestionsTheory.objects.create(
    course=course1,
    question_text="Discuss the importance of algebraic expressions in real-world problem solving.",
PastQuestionsTheory.objects.create(
    course=course1,
    question_text="Explain the concept of variables and constants in algebra with practical examples.",
PastQuestionsTheory.objects.create(
    course=course1,
    question_text="Describe how to factorize quadratic expressions and solve quadratic equations.",
# English Theory Questions
PastQuestionsTheory.objects.create(
    course=course2,
    question_text="Explain the rules of subject-verb agreement with five different examples.",
PastQuestionsTheory.objects.create(
    course=course2,
    question_text="Discuss the importance of tenses in English grammar and provide examples of each major tense.",
PastQuestionsTheory.objects.create(
    course=course2,
    question_text="Describe the different types of sentences based on structure with examples for each type.",
PastQuestionsTheory.objects.create(
    course=course2,
    question_text="Explain the concept of active and passive voice, illustrating with appropriate examples.",
PastQuestionsTheory.objects.create(
    course=course2,
    question_text="Discuss the role of conjunctions in sentence construction and list the main types with examples.","""

# from webapp.models import Course, PastQuestionsObj  # replace 'yourapp' with your actual app name
# from django.db.models import Prefetch
# import random


# import json
# import random

# # Step 1: Get 5 random courses that have at least one question
# courses = list(Course.objects.filter(objective_questions__isnull=False).distinct())
# random_courses = random.sample(courses, min(5, len(courses)))

# data = {}
# for course in random_courses:
#     questions = list(PastQuestionsObj.objects.filter(course=course))
#     random_questions = random.sample(questions, min(20, len(questions)))
#     data[course.name] = [
#         {
#             "question": q.question_text,
#             "options": {
#                 "A": q.option_a,
#                 "B": q.option_b,
#                 "C": q.option_c,
#                 "D": q.option_d,
#             },
#             "correct_option": q.correct_option,
#             "explanation": q.explanation,
#             "hint": q.hint,
#             "year": q.year,
#             "body": q.body,
#         }
#         for q in random_questions
#     ]

# with open("random_questions.json", "w", encoding="utf-8") as f:
#     json.dump(data, f, indent=4, ensure_ascii=False)

# print("✅ Exported random questions to random_questions.json")




# import json
# from main.models import Course, Topic, PastQuestionsObj

# with open('questions/bio101.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)

# for course_name, questions in data.items():
#     course, _ = Course.objects.get_or_create(name=course_name)
#     # Use a generic topic if not specified
#     topic, _ = Topic.objects.get_or_create(name="Evolution: The Core Theme of Biology", course=course)
#     for q in questions:
#         options = q.get("options", {})
#         PastQuestionsObj.objects.create(
#             course=course,
#             topic=topic,
#             question_text=q.get("question", ""),
#             option_a=options.get("A", ""),
#             option_b=options.get("B", ""),
#             option_c=options.get("C", ""),
#             option_d=options.get("D", ""),
#             correct_option=q.get("correct_option", ""),
#             explanation=q.get("explanation", ""),
#             hint=q.get("hint", ""),
#         )