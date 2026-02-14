from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Course, Topic, PastQuestionsObj, Student, CBTResult, FlaggedQuestion
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
                ('D', question.option_d),
                ('E', question.option_e),
            ],
            widget=forms.RadioSelect,
            required=False,
        )


class StudentRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label='First name',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Last name',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")

        # Validate uniqueness of username and email (case-insensitive)
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        if username:
            if User.objects.filter(username__iexact=username).exists():
                self.add_error('username', 'A user with that username already exists.')
        if email:
            if User.objects.filter(email__iexact=email).exists():
                self.add_error('email', 'A user with that email address already exists.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.username.lower()
        user.email = user.email.lower()
        # save provided names
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    department = forms.ChoiceField(
        choices=Student.DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': 'required'
        }),
        required=False
    )
    
    class Meta:
        model = Student
        fields = ['department']


class NameUpdateForm(forms.Form):
    first_name = forms.CharField(
        label='First name',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        label='Last name',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )


import random, time

import random, time, json, uuid
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
        # unique session key for this CBT attempt (used by frontend to scope saved progress)
        request.session['cbt_session_key'] = str(uuid.uuid4())

        return redirect('cbt_exam')

    course = get_object_or_404(Course, id=course_id)
    return render(request, 'cbt_mode_select.html', {'course': course})


def cbt_exam(request):
    """Serves the CBT page (HTML only)"""
    course_id = request.session.get('cbt_course_id')
    if not course_id:
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)

    # Collect topic documents (topics with external_url) to show in the exam modal
    topic_docs = []
    try:
        topics_with_docs = course.topics.filter(external_url__isnull=False).exclude(external_url__exact='')
        for t in topics_with_docs:
            try:
                topic_docs.append({
                    'id': t.id,
                    'name': t.name,
                    'external_url': t.external_url,
                    'embed_url': t.get_embed_url() if hasattr(t, 'get_embed_url') else None,
                })
            except Exception:
                topic_docs.append({
                    'id': t.id,
                    'name': t.name,
                    'external_url': t.external_url,
                    'embed_url': None,
                })
    except Exception:
        topic_docs = []

    return render(request, 'cbt_exam.html', {'course': course, 'topic_docs': topic_docs})


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
                'E': q.option_e,
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
        'session_key': request.session.get('cbt_session_key'),
        'end_time': end_time,
    })


@csrf_exempt
def cbt_submit_answers(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid'}, status=400)

    data = json.loads(request.body)
    request.session['cbt_answers'] = data.get('answers', {})

    return JsonResponse({'status': 'ok'})


@csrf_exempt
def flag_question(request):
    """Flag a question for review (course or topic mode)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        reason = data.get('reason', '')

        if not question_id:
            return JsonResponse({'error': 'Question ID required'}, status=400)

        question = PastQuestionsObj.objects.get(id=question_id)
        
        # Get Student if user is authenticated
        student = None
        if request.user.is_authenticated:
            try:
                student = Student.objects.get(user=request.user)
            except Student.DoesNotExist:
                pass

        # Create or update flag
        flag, created = FlaggedQuestion.objects.get_or_create(
            question=question,
            student=student,
            defaults={'reason': reason}
        )
        
        # If it already existed and was marked resolved, unmark it
        if not created and flag.resolved:
            flag.resolved = False
            flag.save()

        return JsonResponse({
            'status': 'ok',
            'message': f'Question flagged for review{"(re-opened)" if not created else ""}'
        })

    except PastQuestionsObj.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



def get_option_text(question, option_letter):
    """Get the text content of an option given the letter"""
    if not option_letter:
        return None
    option_map = {
        'A': question.option_a,
        'B': question.option_b,
        'C': question.option_c,
        'D': question.option_d,
        'E': question.option_e,
    }
    return option_map.get(option_letter)


def cbt_submit(request):
    course_id = request.session.get('cbt_course_id')
    # Prevent submission when in learn mode
    learn_mode = request.session.get('cbt_learn_mode', False)
    if learn_mode:
        messages.error(request, 'Cannot submit while in Learn Mode.')
        return redirect('cbt_exam')
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
                'your_answer_text': get_option_text(q, ans),
                'correct_answer': q.correct_option,
                'correct_answer_text': get_option_text(q, q.correct_option),
                'explanation': q.explanation
            })

    total = len(questions)
    percent = (score / total) * 100 if total else 0

    # Save result if user is authenticated
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            CBTResult.objects.create(
                student=student,
                course=course,
                score=score,
                total_questions=total
            )
        except Student.DoesNotExist:
            pass

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
    context = {"courses": courses}
    
    # If user is authenticated, offer quick stats and optionally prompt for missing names
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            results = CBTResult.objects.filter(student=student)
            total_exams = results.count()
            if total_exams > 0:
                avg_score = sum(r.score for r in results) / total_exams
                avg_total = sum(r.total_questions for r in results) / total_exams
                avg_percent = (avg_score / avg_total) * 100 if avg_total else 0
            else:
                avg_percent = 0
            context.update({
                'total_exams': total_exams,
                'avg_percent': avg_percent,
            })
        except Student.DoesNotExist:
            pass
    # Handle name update POST from modal for users missing names
    name_form = None
    show_name_modal = False
    if request.user.is_authenticated:
        missing_names = not (request.user.first_name and request.user.last_name)
        if missing_names:
            show_name_modal = True
            if request.method == 'POST' and request.POST.get('name_update'):
                name_form = NameUpdateForm(request.POST)
                if name_form.is_valid():
                    request.user.first_name = name_form.cleaned_data['first_name']
                    request.user.last_name = name_form.cleaned_data['last_name']
                    request.user.save()
                    messages.success(request, 'Name saved successfully.')
                    return redirect('home')
            else:
                name_form = NameUpdateForm()

    context['name_form'] = name_form
    context['show_name_modal'] = show_name_modal

    return render(request, "home.html", context)

def course_list(request):
    courses = Course.objects.all()
    return render(request, "course_list.html", {"courses": courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    topics = course.topics.all()
    obj_questions_count = course.objective_questions.count()
    
    # Enrich topics with practice stats
    topics_with_stats = []
    
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            results = CBTResult.objects.filter(student=student, course=course, topic__isnull=False)
            
            # Build stats dict
            stats_dict = {}
            for result in results:
                topic_id = result.topic.id
                if topic_id not in stats_dict:
                    stats_dict[topic_id] = {'scores': []}
                percentage = (result.score / result.total_questions * 100) if result.total_questions else 0
                stats_dict[topic_id]['scores'].append(percentage)
            
            # Calculate averages
            for topic_id in stats_dict:
                scores = stats_dict[topic_id]['scores']
                stats_dict[topic_id]['avg'] = sum(scores) / len(scores) if scores else 0
                stats_dict[topic_id]['attempts'] = len(scores)
            
            # Enrich topics
            for topic in topics:
                topic_data = {'topic': topic}
                if topic.id in stats_dict:
                    topic_data['stats'] = stats_dict[topic.id]
                topics_with_stats.append(topic_data)
        except Student.DoesNotExist:
            topics_with_stats = [{'topic': t} for t in topics]
    else:
        topics_with_stats = [{'topic': t} for t in topics]
    
    return render(request, "course_detail.html", {
        "course": course,
        "topics_with_stats": topics_with_stats,
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
    obj_questions = list(topic.questions.all())

    # Get saved answers (if coming from a CBT session)
    answers = request.session.get('cbt_topic_answers', {})

    # Build a lightweight nav structure so templates don't need complex lookups
    question_nav = []
    for idx, q in enumerate(obj_questions):
        answered = False
        try:
            # answers keys are stored as strings in session
            answered = bool(answers.get(str(q.id)))
        except Exception:
            answered = False
        question_nav.append({
            'id': q.id,
            'number': idx + 1,
            'answered': answered,
        })

    return render(request, "obj_questions_topic.html", {
        "topic": topic,
        "course": course,
        "obj_questions": obj_questions,
        "question_nav": question_nav,
    })


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    course = topic.course
    obj_questions_count = course.objective_questions.count()
    embed_url = None
    try:
        embed_url = topic.get_embed_url() if hasattr(topic, 'get_embed_url') else None
    except Exception:
        embed_url = None
    return render(request, "topic_detail.html", {
        "topic": topic,
        "course": course,
        "obj_questions_count": obj_questions_count,
        "embed_url": embed_url,
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

        # Determine mode: learn_mode True means the user selected Learn Mode
        learn_mode = request.POST.get('learn_mode') == 'on'

        # Practice mode batching: use sliding-window batches of fixed size
        BATCH_SIZE = 15
        OVERLAP = 4  # number of questions to repeat between consecutive batches

        if learn_mode:
            selected = [q.id for q in questions]
        else:
            # Ensure deterministic ordering (by id)
            ordered_questions = list(topic.questions.order_by('id'))
            total = len(ordered_questions)

            # If not enough questions, return them all
            if total <= BATCH_SIZE:
                selected = [q.id for q in ordered_questions]
            else:
                step = max(1, BATCH_SIZE - OVERLAP)

                # session key for tracking batch start for this topic
                batch_key = f'cbt_topic_batch_start_{topic.id}'
                last_start = request.session.get(batch_key, 0)

                # On first run last_start will be 0 (start at beginning)
                start = last_start

                # Build window and then advance for next time
                end = start + BATCH_SIZE
                if end <= total:
                    window = ordered_questions[start:end]
                else:
                    # If window would overflow, wrap to the end and then pad from start
                    window = ordered_questions[start:total]
                    needed = BATCH_SIZE - len(window)
                    window += ordered_questions[0:needed]

                selected = [q.id for q in window]

                # Advance start for next batch and wrap if necessary
                new_start = start + step
                if new_start > total - 1:
                    # wrap back to 0 once past the last index
                    new_start = 0
                request.session[batch_key] = new_start

        request.session['cbt_topic_id'] = topic.id
        request.session['cbt_topic_selected_questions'] = selected
        request.session['cbt_topic_learn_mode'] = learn_mode
        # Set end time proportional to number of selected questions (approx 60s per question)
        request.session['cbt_topic_end_time'] = time.time() + len(selected) * 60
        # unique session key for this topic CBT attempt
        request.session['cbt_topic_session_key'] = str(uuid.uuid4())

        return redirect('topic_cbt_exam')

    topic = get_object_or_404(Topic, id=topic_id)
    return render(request, 'topic_cbt_mode_select.html', {'topic': topic})


# ---------------------------
# Mock exam (scheduled multi-course mock)
# ---------------------------
from django.utils import timezone
from datetime import time as dtime, datetime

MOCK_START_HOUR = 18
MOCK_START_MIN = 00
MOCK_END_HOUR = 19
MOCK_END_MIN = 40
MOCK_DURATION_SECONDS = (MOCK_END_HOUR * 3600 + MOCK_END_MIN * 60) - (MOCK_START_HOUR * 3600 + MOCK_START_MIN * 60)

def _is_mock_open(now=None):
    """Return True if current local time is within the mock window (18:00–19:40)."""
    now = now or timezone.localtime()
    t = now.time()
    return (t >= dtime(MOCK_START_HOUR, MOCK_START_MIN)) and (t <= dtime(MOCK_END_HOUR, MOCK_END_MIN))


def _student_has_mock_result_today(student, course):
    """Return True if student already has a CBTResult for `course` taken today during the mock window."""
    if not student:
        return False
    today = timezone.localtime().date()
    start_dt = datetime.combine(today, dtime(MOCK_START_HOUR, MOCK_START_MIN))
    end_dt = datetime.combine(today, dtime(MOCK_END_HOUR, MOCK_END_MIN))
    return CBTResult.objects.filter(student=student, course=course, date_taken__range=(start_dt, end_dt)).exists()


@login_required
def start_mock(request):
    """Initialize mock session for a set of courses. GET shows selectable courses; POST creates session state.

    Selection rules (per your spec):
      - For ZOO 101, BIO 101, GST 111, PHY 101, CHM 101, COM 101: draw 50 random questions from topics whose name contains "Past Questions" (case-insensitive).
      - For MTH 101: draw 50 random questions from any topic (i.e. from the course pool).
      - Fallback: if fewer than 50 available, use all available.

    The mock is only startable/accessed between 18:00 and 19:40 local time.
    """
    # only get BIO 101, ZOO 101, GST 111 AND COM 101

    courses = Course.objects.filter(name__in=['BIO 101', 'ZOO 101', 'GST 111', 'COM 101']).order_by('name')
        # ---------------------------
    from django.utils import timezone
    from datetime import time as dtime, datetime

    print("SERVER NOW:", timezone.now())
    print("LOCAL NOW :", timezone.localtime())

    if request.method == 'POST':
        # Enforce availability window
        if not _is_mock_open():
            print("Attempt to start mock outside of window")
            messages.error(request, 'Mock is only available between 18:00 and 19:40 local time.')
            return redirect('home')
        print("Starting mock session for courses:", request.POST.getlist('courses'))

        # Determine which courses to include (check boxes in form). Default: include all.
        selected_course_ids = request.POST.getlist('courses') or [str(c.id) for c in courses]
        selected_courses = Course.objects.filter(id__in=selected_course_ids)

        # Prevent students from re-attempting same mock after it ends (server-side check)
        student_obj = None
        if request.user.is_authenticated:
            try:
                student_obj = Student.objects.get(user=request.user)
            except Student.DoesNotExist:
                student_obj = None

        # Set mock session window (use today's 18:00..19:40)
        from django.utils import timezone

        today = timezone.localdate()

        start_dt = timezone.make_aware(
            datetime.combine(today, dtime(MOCK_START_HOUR, MOCK_START_MIN)),
            timezone.get_current_timezone()
        )

        end_dt = timezone.make_aware(
            datetime.combine(today, dtime(MOCK_END_HOUR, MOCK_END_MIN)),
            timezone.get_current_timezone()
        )
        request.session['mock_start_time'] = start_dt.timestamp()
        request.session['mock_end_time'] = end_dt.timestamp()
        request.session['mock_courses'] = [c.id for c in selected_courses]

        # For each course prepare 50-question selection according to rules
        for course in selected_courses:
            # If student already has a saved mock result for this course today, skip
            if student_obj and _student_has_mock_result_today(student_obj, course):
                continue

            qs = PastQuestionsObj.objects.filter(course=course)
            # Default filter: topics with "Past Questions" in the name (case-insensitive)
            if course.name.strip().upper() == 'MTH 101':
                pool = list(qs)
            else:
                pool = list(qs.filter(topic__name__icontains='Past Questions'))
                if not pool:
                    # fallback to whole-course pool if no matching topic exists
                    pool = list(qs)

            selected = []
            if pool:
                import random
                selected = random.sample(pool, min(50, len(pool)))
                selected_ids = [q.id for q in selected]
            else:
                selected_ids = []

            # Store per-course mock session data so student can switch courses while preserving progress
            request.session[f'mock_{course.id}_selected_questions'] = selected_ids
            request.session[f'mock_{course.id}_answers'] = {}
            request.session[f'mock_{course.id}_session_key'] = str(uuid.uuid4())
            request.session[f'mock_{course.id}_end_time'] = end_dt.timestamp()
            request.session[f'mock_{course.id}_completed'] = False

        messages.success(request, 'Mock session initialized — good luck!')
        return redirect('mock_exam')

    # GET: show selection form
    return render(request, 'mock_mode_select.html', {'courses': courses, 'mock_open': _is_mock_open()})


def mock_exam(request):
    """Render the mock exam shell. The frontend will request per-course questions via `mock_data`.

    Access restricted to mock window only.
    """
    # Ensure mock has been initialized in session
    course_ids = request.session.get('mock_courses')
    end_time = request.session.get('mock_end_time')
    if not course_ids or not end_time:
        messages.error(request, 'Mock session not initialized.')
        return redirect('home')

    # Block access outside window
    if not _is_mock_open():
        messages.error(request, 'Mock is only accessible between 18:00 and 19:40 local time.')
        return redirect('home')

    courses = Course.objects.filter(id__in=course_ids)
    # active course defaults to first
    active_course = courses.first() if courses.exists() else None

    # Ensure we pass an integer UNIX timestamp (seconds) to the template
    end_time_ts = int(end_time) if end_time else None

    return render(request, 'mock_exam.html', {
        'courses': courses,
        'active_course': active_course,
        'end_time': end_time_ts,
    })


def mock_data(request):
    """Return questions for a specific course within the mock session.

    GET param `course_id` required (or falls back to first mock course in session).
    """
    course_ids = request.session.get('mock_courses')
    end_time = request.session.get('mock_end_time')
    if not course_ids or not end_time:
        return JsonResponse({'error': 'Mock session not initialized'}, status=400)

    # Block access outside window
    if not _is_mock_open():
        return JsonResponse({'error': 'Mock is only available between 18:00 and 19:40'}, status=403)

    course_id = request.GET.get('course_id')
    try:
        course_id = int(course_id) if course_id else int(course_ids[0])
    except Exception:
        return JsonResponse({'error': 'Invalid course id'}, status=400)

    if course_id not in course_ids:
        return JsonResponse({'error': 'Course not part of the current mock session'}, status=400)

    ids = request.session.get(f'mock_{course_id}_selected_questions', [])
    answers = request.session.get(f'mock_{course_id}_answers', {})
    session_key = request.session.get(f'mock_{course_id}_session_key')
    from django.utils import timezone
    now_ts = timezone.now().timestamp()
    remaining = int(end_time - now_ts) if end_time else None


    questions = list(PastQuestionsObj.objects.filter(id__in=ids))
    # Preserve order
    questions.sort(key=lambda q: ids.index(q.id) if q.id in ids else 0)

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
                'E': q.option_e,
            },
            'correct': q.correct_option,
            'explanation': q.explanation or "No explanation provided",
            'hint': q.hint or "",
            'your_answer': answers.get(str(q.id))
        })

    return JsonResponse({
        'questions': payload,
        'remaining': remaining,
        'session_key': session_key,
        'end_time': end_time,
        'course_id': course_id,
    })


@csrf_exempt
def mock_submit_answers(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    data = json.loads(request.body)
    course_id = data.get('course_id')
    answers = data.get('answers', {})
    if not course_id:
        return JsonResponse({'error': 'course_id required'}, status=400)

    # Ensure course is part of session
    course_ids = request.session.get('mock_courses', [])
    if int(course_id) not in course_ids:
        return JsonResponse({'error': 'Course not in current mock session'}, status=400)

    request.session[f'mock_{course_id}_answers'] = answers
    return JsonResponse({'status': 'ok'})


def mock_submit(request):
    """Finalize and save a student's mock result for a specific course.

    Submission allowed only inside mock window or immediately after when finalizing.
    """
    course_id = request.POST.get('course_id') or request.session.get('mock_courses', [None])[0]
    if not course_id:
        messages.error(request, 'Course not specified')
        return redirect('mock_exam')

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, 'Course not found')
        return redirect('mock_exam')

    # If student already has a mock result today for this course, block re-submit
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            if _student_has_mock_result_today(student, course):
                messages.error(request, 'You have already submitted this mock for today.')
                return redirect('mock_exam')
        except Student.DoesNotExist:
            student = None
    else:
        student = None

    # Use saved answers in session for the course
    ids = request.session.get(f'mock_{course.id}_selected_questions', [])
    answers = request.session.get(f'mock_{course.id}_answers', {})
    questions = list(PastQuestionsObj.objects.filter(id__in=ids))
    questions.sort(key=lambda q: ids.index(q.id) if q.id in ids else 0)

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
                'your_answer_text': get_option_text(q, ans),
                'correct_answer': q.correct_option,
                'correct_answer_text': get_option_text(q, q.correct_option),
                'explanation': q.explanation
            })

    total = len(questions)
    percent = (score / total) * 100 if total else 0

    # Save CBTResult to record the mock attempt per course
    if student:
        CBTResult.objects.create(
            student=student,
            course=course,
            score=score,
            total_questions=total
        )

    # mark as completed in session so user cannot reattempt this course in the same mock
    request.session[f'mock_{course.id}_completed'] = True

    return render(request, 'cbt_submit.html', {
        'course': course,
        'score': score,
        'total': total,
        'percent': percent,
        'failed_questions': failed
    })


def mock_submit_all(request):
    """Submit and save mock results for all courses in the current mock session.

    - Iterates over session['mock_courses']
    - Uses session answers for each course
    - Creates a CBTResult per course (if user/student exists and not already submitted today)
    - Marks each course as completed in session
    - Renders a summary page showing scores per course and failed questions
    """
    course_ids = request.session.get('mock_courses', [])
    if not course_ids:
        messages.error(request, 'Mock session not initialized.')
        return redirect('home')

    # Allow submission up to a short grace period after the session end_time stored in session
    session_end = request.session.get('mock_end_time')
    now_ts = time.time()
    if session_end:
        # allow submissions until 5 minutes after end_time (grace for client-side submission)
        if now_ts > (session_end + 300):
            messages.error(request, 'Mock submissions are only accepted during or shortly after the mock window.')
            return redirect('mock_exam')
    else:
        # fallback: enforce regular mock window check
        if not _is_mock_open():
            messages.error(request, 'Mock submissions are only accepted between 18:00 and 19:40 local time.')
            return redirect('mock_exam')

    student = None
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            student = None

    summary = []

    for cid in course_ids:
        try:
            course = Course.objects.get(id=cid)
        except Course.DoesNotExist:
            continue

        # skip if already submitted today for this course
        if student and _student_has_mock_result_today(student, course):
            summary.append({'course': course, 'skipped': True, 'reason': 'Already submitted today'})
            continue

        ids = request.session.get(f'mock_{course.id}_selected_questions', [])
        answers = request.session.get(f'mock_{course.id}_answers', {})
        questions = list(PastQuestionsObj.objects.filter(id__in=ids))
        questions.sort(key=lambda q: ids.index(q.id) if q.id in ids else 0)

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
                    'your_answer_text': get_option_text(q, ans),
                    'correct_answer': q.correct_option,
                    'correct_answer_text': get_option_text(q, q.correct_option),
                    'explanation': q.explanation
                })

        total = len(questions)
        percent = (score / total) * 100 if total else 0

        # persist
        if student:
            CBTResult.objects.create(student=student, course=course, score=score, total_questions=total)

        request.session[f'mock_{course.id}_completed'] = True

        summary.append({
            'course': course,
            'score': score,
            'total': total,
            'percent': percent,
            'failed_questions': failed,
            'skipped': False,
        })

    # After saving all, clear the mock session keys so user can't resubmit the same session
    request.session.pop('mock_courses', None)
    request.session.pop('mock_start_time', None)
    request.session.pop('mock_end_time', None)

    return render(request, 'mock_submit_summary.html', {'summary': summary})



def topic_cbt_exam(request):
    topic_id = request.session.get('cbt_topic_id')
    if not topic_id:
        return redirect('home')

    topic = get_object_or_404(Topic, id=topic_id)
    embed_url = None
    try:
        embed_url = topic.get_embed_url() if hasattr(topic, 'get_embed_url') else None
    except Exception:
        embed_url = None
    return render(request, 'topic_cbt_exam.html', {'topic': topic, 'embed_url': embed_url})


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
                'E': q.option_e,
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
        'session_key': request.session.get('cbt_topic_session_key'),
        'end_time': end_time,
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
    # Prevent submission when in learn mode for topic CBT
    learn_mode = request.session.get('cbt_topic_learn_mode', False)
    if learn_mode:
        messages.error(request, 'Cannot submit while in Learn Mode.')
        return redirect('topic_cbt_exam')
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
                'your_answer_text': get_option_text(q, ans),
                'correct_answer': q.correct_option,
                'correct_answer_text': get_option_text(q, q.correct_option),
                'explanation': q.explanation
            })

    percent = (score / len(questions)) * 100 if questions else 0

    # Save result if user is authenticated
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            CBTResult.objects.create(
                student=student,
                course=topic.course,
                topic=topic,
                score=score,
                total_questions=len(questions)
            )
        except Student.DoesNotExist:
            pass

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
        logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect('home')
    

def register(request):
    if request.method == 'POST':
        user_form = StudentRegistrationForm(request.POST)
        profile_form = StudentProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            student = profile_form.save(commit=False)
            student.user = user
            student.save()
            messages.success(request, 'Registration successful. You can now log in.')
            # login the user directly and redirect to dashboard page
            login(request, user)
            return redirect('home')

            
    else:
        user_form = StudentRegistrationForm()
        profile_form = StudentProfileForm()
    return render(request, 'student_register.html', {'form': user_form, 'profile_form': profile_form})


def custom_login(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').lower()
        password = request.POST.get('password')
        user = None
        try:
            # Try to get user by username (case-insensitive)
            user = User.objects.get(username__iexact=username_or_email)
        except User.DoesNotExist:
            try:
                # Try to get user by email (case-insensitive)
                user = User.objects.get(email__iexact=username_or_email)
            except User.DoesNotExist:
                pass
        if user and user.check_password(password):
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')


@login_required
def progress(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('home')
    
    results = CBTResult.objects.filter(student=student).order_by('-date_taken')
    
    # Overall stats
    total_exams = results.count()
    if total_exams > 0:
        avg_score = sum(r.score for r in results) / total_exams
        avg_total = sum(r.total_questions for r in results) / total_exams
        avg_percent = (avg_score / avg_total) * 100 if avg_total else 0
    else:
        avg_percent = 0
    
    # Per course
    course_stats = {}
    for result in results:
        if result.course:
            c = result.course
            if c not in course_stats:
                course_stats[c] = {'scores': [], 'total': 0}
            course_stats[c]['scores'].append((result.score / result.total_questions) * 100)
            course_stats[c]['total'] += 1
    
    for c in course_stats:
        scores = course_stats[c]['scores']
        course_stats[c]['avg'] = sum(scores) / len(scores) if scores else 0
    
    # Per topic
    topic_stats = {}
    for result in results:
        if result.topic:
            t = result.topic
            if t not in topic_stats:
                topic_stats[t] = {'scores': [], 'total': 0}
            topic_stats[t]['scores'].append((result.score / result.total_questions) * 100)
            topic_stats[t]['total'] += 1
    
    for t in topic_stats:
        scores = topic_stats[t]['scores']
        topic_stats[t]['avg'] = sum(scores) / len(scores) if scores else 0
    
    # Strengths: avg > 70%
    all_stats = {**course_stats, **topic_stats}
    strengths = [{'item': k, 'avg': v['avg']} for k, v in all_stats.items() if v['avg'] > 70]
    weaknesses = [{'item': k, 'avg': v['avg']} for k, v in all_stats.items() if v['avg'] < 50]
    
    # Add percentage to results
    results_with_percent = []
    for r in results:
        percent = (r.score / r.total_questions) * 100 if r.total_questions else 0
        results_with_percent.append({
            'result': r,
            'percentage': percent
        })
    
    return render(request, 'progress.html', {
        'results': results_with_percent,
        'total_exams': total_exams,
        'avg_percent': avg_percent,
        'course_stats': course_stats,
        'topic_stats': topic_stats,
        'strengths': strengths,
        'weaknesses': weaknesses,
    })



# json search endpoint defined later (deduplicated)



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




def load_random_questions_from_file(filepath='random_questions.json'):
    """Load questions from a JSON file into the database.

    This helper does NOT run on import. Call it explicitly from a script,
    the Django shell, or a management command. Example:
      from main.views import load_random_questions_from_file
      load_random_questions_from_file()
    """
    import json
    from main.models import Course, Topic, PastQuestionsObj

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for course_name, questions in data.items():
        course, _ = Course.objects.get_or_create(name=course_name)
        for q in questions:
            topic_name = q.get("topic", "")
            if topic_name:
                topic, _ = Topic.objects.get_or_create(name=topic_name, course=course)
            else:
                topic = None
            options = q.get("options", {})
            # Use get_or_create to avoid duplicates based on course and question_text
            obj, created = PastQuestionsObj.objects.get_or_create(
                course=course,
                question_text=q.get("question", ""),
                defaults={
                    'topic': topic,
                    'option_a': options.get("A", ""),
                    'option_b': options.get("B", ""),
                    'option_c': options.get("C", ""),
                    'option_d': options.get("D", ""),
                    'option_e': options.get("E", ""),
                    'correct_option': q.get("correct_option", ""),
                    'explanation': q.get("explanation", ""),
                    'hint': q.get("hint", ""),
                }
            )
            if created:
                print("Created", obj.question_text)
            else:
                print("Exists", obj.question_text)

# NOTE: For safety and reproducibility, prefer moving this logic into a Django
# management command (see `python manage.py help`) or run it from the shell.

# load_random_questions_from_file()


from django.db.models import Q

def search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return render(request, 'search_results.html', {'query': query, 'results': []})
    
    # Search in Courses
    courses = Course.objects.filter(name__icontains=query)
    
    # Search in Topics (search name and document link)
    topics = Topic.objects.filter(
        Q(name__icontains=query) | Q(external_url__icontains=query)
    )
    
    # Search in Questions
    questions = PastQuestionsObj.objects.filter(
        Q(question_text__icontains=query) |
        Q(option_a__icontains=query) |
        Q(option_b__icontains=query) |
        Q(option_c__icontains=query) |
        Q(option_d__icontains=query) |
        Q(option_e__icontains=query) |
        Q(explanation__icontains=query) |
        Q(hint__icontains=query)
    )
    
    results = {
        'courses': courses,
        'topics': topics,
        'questions': questions,
    }
    
    return render(request, 'search_results.html', {
        'query': query,
        'results': results,
    })

from django.http import JsonResponse

def search_json(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    
    # Search in Topics (search name and document link)
    topics = Topic.objects.filter(
        Q(name__icontains=query) | Q(external_url__icontains=query)
    ).values('id', 'name', 'course__name', 'external_url')

    
    results = {
        'topics': list(topics),
    }
    
    return JsonResponse({'query': query, 'results': results})


@login_required
def student_list(request):
    """List registered students (full name, username, department). Only staff members can access this page."""

    students = Student.objects.select_related('user').order_by('user__username').all()
    return render(request, 'student_list.html', {'students': students})



# Act as an expert educator and instructional designer. I am going to provide you with lecture notes from a PowerPoint presentation. Your task is to generate as many multiple-choice questions as possible (aiming for 100) based strictly and exclusively on the content of the provided text.

# Requirements:

# Source Material: Do not use outside knowledge. Use only the provided notes.

# Output Format: You must output the response as a JSON array of objects following this exact schema: { "question": "string", "topic": "string", "options": { "A": "string", "B": "string", "C": "string", "D": "string" }, "correct_option": "char", "explanation": "string", "hint": "string" },

# Tone & Style: In the explanation and hint fields, do not use phrases like 'according to the text,' 'as mentioned in the notes,' or 'the text states.' Write the explanations and hints as objective facts.

# Volume: Generate as many unique questions as the text allows, up to 100. If the text is exhausted before 100, provide as many as are logically possible.

# Here is the lecture text: 



# Act as a specialized tutor. I am going to provide you with slides from my class. Your goal is to create a comprehensive Gap-Fill (Fill-in-the-blanks) study guide that covers every single fact, term, and definition found on these slides.

# Rules for the questions:

# No skipping: Every bullet point, label, and heading must be turned into a question.

# Key terms only: Replace the most important technical terms, numbers, or names with a blank line (__________).

# Context: Provide enough of the sentence so I understand the context, but leave the 'answer' blank.

# Organization: Group the questions by slide title so I can follow along.

# Answer Key: Provide a numbered answer key at the very bottom so I can check my work after I finish writing them in my notes.

# Please process these slides now


