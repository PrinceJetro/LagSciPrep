

from django.contrib import admin
from .models import Course, Topic, PastQuestionsObj, Student, CBTResult, FlaggedQuestion

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
	search_fields = ['name']
	list_display = ['id', 'name']

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    search_fields = ['name', 'course__name', 'external_url']
    list_display = ['id', 'name', 'course', 'external_url']
    list_filter = ['course']
    # Keep the admin simple: only allow editing the external_url (and basic metadata)
    fields = ('name', 'course', 'external_url')

@admin.register(PastQuestionsObj)
class PastQuestionsObjAdmin(admin.ModelAdmin):
	search_fields = ['question_text', 'course__name', 'topic__name']
	list_display = ['id', 'course', 'topic', 'question_text', 'correct_option']
	list_filter = ['course', 'topic', 'correct_option']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
	search_fields = ['user__username', 'user__email', 'department']
	list_display = ['id', 'user', 'department']
	list_filter = ['department']
	readonly_fields = ['user']

@admin.register(CBTResult)
class CBTResultAdmin(admin.ModelAdmin):
	search_fields = ['student__user__username', 'course__name', 'topic__name']
	list_display = ['id', 'student', 'course', 'topic', 'score', 'total_questions', 'date_taken']
	list_filter = ['course', 'topic', 'date_taken']
	readonly_fields = ['date_taken']
	ordering = ['-date_taken']

@admin.register(FlaggedQuestion)
class FlaggedQuestionAdmin(admin.ModelAdmin):
	search_fields = ['question__question_text', 'student__user__username', 'reason']
	list_display = ['id', 'question', 'student', 'flagged_at', 'resolved']
	list_filter = ['resolved', 'flagged_at']
	readonly_fields = ['flagged_at']
	ordering = ['-flagged_at']
	fields = ('question', 'student', 'reason', 'flagged_at', 'resolved')
