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

def start_cbt(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        questions = list(course.objective_questions.all())
        selected_questions = random.sample(questions, min(15, len(questions)))
        request.session['cbt_course_id'] = course_id
        request.session['cbt_answers'] = {}
        request.session['cbt_question_index'] = 0
        request.session['cbt_selected_questions'] = [q.id for q in selected_questions]
        request.session['cbt_learn_mode'] = request.POST.get('learn_mode') == 'on'
        # Timer: 7min 30sec from now
        request.session['cbt_end_time'] = time.time() + 7*60 + 30
        return redirect('cbt_question')
    else:
        # Show modal to select mode
        course = get_object_or_404(Course, id=course_id)
        return render(request, 'cbt_mode_select.html', {'course': course})


def cbt_question(request):
    import time
    course_id = request.session.get('cbt_course_id')
    answers = request.session.get('cbt_answers', {})
    index = request.session.get('cbt_question_index', 0)
    selected_ids = request.session.get('cbt_selected_questions', [])
    end_time = request.session.get('cbt_end_time')
    learn_mode = request.session.get('cbt_learn_mode', False)
    if course_id is None or not selected_ids:
        return redirect('home')
    course = get_object_or_404(Course, id=course_id)
    questions = list(PastQuestionsObj.objects.filter(id__in=selected_ids))
    questions.sort(key=lambda q: selected_ids.index(q.id))
    if index < 0 or index >= len(questions):
        return redirect('cbt_submit')
    question = questions[index]
    # Timer logic
    remaining = int(end_time - time.time()) if end_time else None
    if remaining is not None and remaining <= 0:
        return redirect('cbt_submit')
    # Get all topics for this course
    topics = course.topics.all()
    
    # Check for feedback in learn mode
    feedback = None
    user_answer = answers.get(str(question.id))
    if user_answer:
        is_correct = user_answer == question.correct_option
        if not is_correct and learn_mode:
            # In learn mode, show feedback immediately
            def get_option_text(opt):
                if opt == 'A': return question.option_a
                if opt == 'B': return question.option_b
                if opt == 'C': return question.option_c
                if opt == 'D': return question.option_d
                return None
            feedback = {
                'is_correct': is_correct,
                'user_answer': get_option_text(user_answer),
                'correct_answer': get_option_text(question.correct_option),
                'explanation': question.explanation if question.explanation else "No explanation provided."
            }
    
    if request.method == 'POST':
        form = CBTForm(request.POST, question=question)
        if form.is_valid():
            selected = form.cleaned_data['selected_option']
            answers[str(question.id)] = selected
            request.session['cbt_answers'] = answers
            
            # In learn mode, don't allow progression until correct answer is selected
            if learn_mode and selected != question.correct_option:
                # Stay on same question and show feedback
                is_correct = selected == question.correct_option
                def get_option_text(opt):
                    if opt == 'A': return question.option_a
                    if opt == 'B': return question.option_b
                    if opt == 'C': return question.option_c
                    if opt == 'D': return question.option_d
                    return None
                feedback = {
                    'is_correct': is_correct,
                    'user_answer': get_option_text(selected),
                    'correct_answer': get_option_text(question.correct_option),
                    'explanation': question.explanation if question.explanation else "No explanation provided."
                }
                form = CBTForm(question=question, initial={'selected_option': selected})
                return render(request, 'cbt_question.html', {
                    'question': question,
                    'form': form,
                    'index': index,
                    'total': len(questions),
                    'course': course,
                    'remaining': remaining,
                    'topics': topics,
                    'learn_mode': learn_mode,
                    'feedback': feedback
                })
            
            # Normal mode or correct answer in learn mode - allow progression
            if 'next' in request.POST:
                request.session['cbt_question_index'] = index + 1
            elif 'prev' in request.POST:
                request.session['cbt_question_index'] = max(index - 1, 0)
            elif 'submit' in request.POST:
                return redirect('cbt_submit')
            return redirect('cbt_question')
    else:
        form = CBTForm(question=question, initial={
            'selected_option': answers.get(str(question.id), None)
        })
    return render(request, 'cbt_question.html', {
        'question': question,
        'form': form,
        'index': index,
        'total': len(questions),
        'course': course,
        'remaining': remaining,
        'topics': topics,
        'learn_mode': learn_mode,
        'feedback': feedback
    })


def cbt_submit(request):
    course_id = request.session.get('cbt_course_id')
    answers = request.session.get('cbt_answers', {})
    selected_ids = request.session.get('cbt_selected_questions', [])
    if course_id is None:
        return redirect('home')
    course = get_object_or_404(Course, id=course_id)
    # Only get the selected questions from the CBT, not all questions in the course
    questions = list(PastQuestionsObj.objects.filter(id__in=selected_ids))
    questions.sort(key=lambda q: selected_ids.index(q.id))
    score = 0
    failed_questions = []
    for q in questions:
        ans = answers.get(str(q.id))
        if ans and ans == q.correct_option:
            score += 1
        else:
            def get_option_text(q, opt):
                if opt == 'A': return q.option_a
                if opt == 'B': return q.option_b
                if opt == 'C': return q.option_c
                if opt == 'D': return q.option_d
                return None
            failed_questions.append({
                'question': q,
                'your_answer': get_option_text(q, ans),
                'correct_answer': get_option_text(q, q.correct_option),
                'explanation': q.explanation if q.explanation else "No explanation provided."
            })
    total = len(questions)
    percent = (score / total) * 100 if total > 0 else 0
    # Clear session
    request.session.pop('cbt_course_id', None)
    request.session.pop('cbt_answers', None)
    request.session.pop('cbt_question_index', None)
    request.session.pop('cbt_selected_questions', None)
    return render(request, 'cbt_submit.html', {
        'course': course,
        'score': score,
        'total': total,
        'percent': percent,
        'failed_questions': failed_questions
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
    obj_questions = course.objective_questions.all()
    return render(request, "course_detail.html", {
        "course": course,
        "topics": topics,
        "obj_questions": obj_questions,
    })


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    course = topic.course
    obj_questions = course.objective_questions.all()
    return render(request, "topic_detail.html", {
        "topic": topic,
        "course": course,
        "obj_questions": obj_questions,
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


def start_topic_cbt(request, topic_id):
    if request.method == 'POST':
        topic = get_object_or_404(Topic, id=topic_id)
        questions = list(topic.questions.all())
        if len(questions) < 1:
            messages.error(request, 'No CBT questions available for this topic.')
            return redirect('topic_detail', topic_id=topic_id)
        request.session['cbt_topic_id'] = topic_id
        request.session['cbt_topic_answers'] = {}
        request.session['cbt_topic_question_index'] = 0
        request.session['cbt_topic_selected_questions'] = [q.id for q in questions]
        request.session['cbt_topic_learn_mode'] = request.POST.get('learn_mode') == 'on'
        # Timer: 1 min per question (or adjust as needed)
        import time
        request.session['cbt_topic_end_time'] = time.time() + len(questions) * 60
        return redirect('topic_cbt_question')
    else:
        # Show modal to select mode
        topic = get_object_or_404(Topic, id=topic_id)
        return render(request, 'topic_cbt_mode_select.html', {'topic': topic})


def topic_cbt_question(request):
    import time
    topic_id = request.session.get('cbt_topic_id')
    answers = request.session.get('cbt_topic_answers', {})
    index = request.session.get('cbt_topic_question_index', 0)
    selected_ids = request.session.get('cbt_topic_selected_questions', [])
    end_time = request.session.get('cbt_topic_end_time')
    learn_mode = request.session.get('cbt_topic_learn_mode', False)
    if topic_id is None or not selected_ids:
        return redirect('home')
    topic = get_object_or_404(Topic, id=topic_id)
    questions = list(PastQuestionsObj.objects.filter(id__in=selected_ids))
    questions.sort(key=lambda q: selected_ids.index(q.id))
    if index < 0 or index >= len(questions):
        return redirect('topic_cbt_submit')
    question = questions[index]
    remaining = int(end_time - time.time()) if end_time else None
    if remaining is not None and remaining <= 0:
        return redirect('topic_cbt_submit')
    
    # Check for feedback in learn mode
    feedback = None
    user_answer = answers.get(str(question.id))
    if user_answer:
        is_correct = user_answer == question.correct_option
        if not is_correct and learn_mode:
            # In learn mode, show feedback immediately
            def get_option_text(opt):
                if opt == 'A': return question.option_a
                if opt == 'B': return question.option_b
                if opt == 'C': return question.option_c
                if opt == 'D': return question.option_d
                return None
            feedback = {
                'is_correct': is_correct,
                'user_answer': get_option_text(user_answer),
                'correct_answer': get_option_text(question.correct_option),
                'explanation': question.explanation if question.explanation else "No explanation provided."
            }
    
    if request.method == 'POST':
        form = CBTForm(request.POST, question=question)
        if form.is_valid():
            selected = form.cleaned_data['selected_option']
            answers[str(question.id)] = selected
            request.session['cbt_topic_answers'] = answers
            
            # In learn mode, don't allow progression until correct answer is selected
            if learn_mode and selected != question.correct_option:
                # Stay on same question and show feedback
                is_correct = selected == question.correct_option
                def get_option_text(opt):
                    if opt == 'A': return question.option_a
                    if opt == 'B': return question.option_b
                    if opt == 'C': return question.option_c
                    if opt == 'D': return question.option_d
                    return None
                feedback = {
                    'is_correct': is_correct,
                    'user_answer': get_option_text(selected),
                    'correct_answer': get_option_text(question.correct_option),
                    'explanation': question.explanation if question.explanation else "No explanation provided."
                }
                form = CBTForm(question=question, initial={'selected_option': selected})
                return render(request, 'topic_cbt_question.html', {
                    'question': question,
                    'form': form,
                    'index': index,
                    'total': len(questions),
                    'topic': topic,
                    'remaining': remaining,
                    'learn_mode': learn_mode,
                    'feedback': feedback
                })
            
            # Normal mode or correct answer in learn mode - allow progression
            if 'next' in request.POST:
                request.session['cbt_topic_question_index'] = index + 1
            elif 'prev' in request.POST:
                request.session['cbt_topic_question_index'] = max(index - 1, 0)
            elif 'submit' in request.POST:
                return redirect('topic_cbt_submit')
            return redirect('topic_cbt_question')
    else:
        form = CBTForm(question=question, initial={
            'selected_option': answers.get(str(question.id), None)
        })
    return render(request, 'topic_cbt_question.html', {
        'question': question,
        'form': form,
        'index': index,
        'total': len(questions),
        'topic': topic,
        'remaining': remaining,
        'learn_mode': learn_mode,
        'feedback': feedback
    })


def topic_cbt_submit(request):
    topic_id = request.session.get('cbt_topic_id')
    answers = request.session.get('cbt_topic_answers', {})
    if topic_id is None:
        return redirect('home')
    topic = get_object_or_404(Topic, id=topic_id)
    questions = list(topic.questions.all())
    score = 0
    failed_questions = []
    for q in questions:
        ans = answers.get(str(q.id))
        if ans and ans == q.correct_option:
            score += 1
        else:
            def get_option_text(q, opt):
                if opt == 'A': return q.option_a
                if opt == 'B': return q.option_b
                if opt == 'C': return q.option_c
                if opt == 'D': return q.option_d
                return None
            failed_questions.append({
                'question': q,
                'your_answer': get_option_text(q, ans),
                'correct_answer': get_option_text(q, q.correct_option),
                'explanation': q.explanation if q.explanation else "No explanation provided."
            })
    percent = (score / len(questions)) * 100 if questions else 0
    # No grade model update for topic-based practice (optional)
    request.session.pop('cbt_topic_id', None)
    request.session.pop('cbt_topic_answers', None)
    request.session.pop('cbt_topic_question_index', None)
    request.session.pop('cbt_topic_selected_questions', None)
    request.session.pop('cbt_topic_end_time', None)
    return render(request, 'topic_cbt_submit.html', {
        'topic': topic,
        'score': score,
        'total': len(questions),
        'percent': percent,
        'failed_questions': failed_questions
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