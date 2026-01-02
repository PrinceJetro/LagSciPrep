from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
import uuid  # To generate unique submission IDs
from django.utils.timezone import now


class Course(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Topic(models.Model):
    name = models.CharField(max_length=255)
    content = RichTextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')

    def __str__(self):
        return self.name



class PastQuestionsObj(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='objective_questions')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')  # NEW FIELD
    question_text = RichTextField(help_text="CBT question")
    option_a = models.CharField(max_length=200, blank=True, null=True, help_text="Option A (leave blank for theory)")
    option_b = models.CharField(max_length=200, blank=True, null=True, help_text="Option B (leave blank for theory)")
    option_c = models.CharField(max_length=200, blank=True, null=True, help_text="Option C (leave blank for theory)")
    option_d = models.CharField(max_length=200, blank=True, null=True, help_text="Option D (leave blank for theory)")
    correct_option = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('A', 'Option A'), ('B', 'Option B'), ('C', 'Option C'), ('D', 'Option D')],
        help_text="Correct option (leave blank for theory)"
    )
    explanation = RichTextField(blank=True, null=True, help_text="AI-generated detailed explanation")  # NEW FIELD
    explanation_generated = models.BooleanField(default=False, help_text="Set True after the AI generates an explanation")
    hint = RichTextField(blank=True, null=True, help_text="AI-generated detailed hint")  # NEW FIELD
    hint_generated = models.BooleanField(default=False, help_text="Set True after the AI generates an hint")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.course.name} CBT Question: {self.question_text[:50]}'


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username




class CBTResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.course:
            return f"{self.student} - {self.course} - {self.score}/{self.total_questions}"
        elif self.topic:
            return f"{self.student} - {self.topic} - {self.score}/{self.total_questions}"
        return f"{self.student} - {self.score}/{self.total_questions}"



