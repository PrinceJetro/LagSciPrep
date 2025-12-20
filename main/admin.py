

from django.contrib import admin
from .models import Course, Topic, PastQuestionsObj

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
	search_fields = ['name']
	list_display = ['id', 'name']

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
	search_fields = ['name', 'course__name']
	list_display = ['name', 'course', "id"]
	list_filter = ['course']

@admin.register(PastQuestionsObj)
class PastQuestionsObjAdmin(admin.ModelAdmin):
	search_fields = ['question_text', 'course__name', 'topic__name']
	list_display = ['id', 'course', 'topic', 'question_text', 'correct_option']
	list_filter = ['course', 'topic', 'correct_option']

