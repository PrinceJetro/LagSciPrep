from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import TemplateView


urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/obj_questions/', views.get_obj_questions, name='get_obj_questions'),
    path('courses/<int:course_id>/all_obj_questions/', views.course_obj_questions, name='course_obj_questions'),
    path('courses/<int:course_id>/cbt/', views.start_cbt, name='start_cbt'),
    path('cbt/submit/', views.cbt_submit, name='cbt_submit'),
    path('topics/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('topics/<int:topic_id>/obj_questions/', views.get_topic_obj_questions, name='get_topic_obj_questions'),
    path('topics/<int:topic_id>/all_obj_questions/', views.topic_obj_questions, name='topic_obj_questions'),
    path('obj_questions/<int:question_id>/', views.obj_question_detail, name='obj_question_detail'),
    path('login/', views.custom_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('progress/', views.progress, name='progress'),
    path('topics/<int:topic_id>/cbt/', views.start_topic_cbt, name='start_topic_cbt'),
    path('topic_cbt/submit/', views.topic_cbt_submit, name='topic_cbt_submit'),
     path('cbt/start/<int:course_id>/', views.start_cbt, name='start_cbt'),
    path('cbt/exam/', views.cbt_exam, name='cbt_exam'),
    path('cbt/data/', views.cbt_data, name='cbt_data'),
    path('cbt/submit-answers/', views.cbt_submit_answers, name='cbt_submit_answers'),
    path('cbt/submit/', views.cbt_submit, name='cbt_submit'),
    path('topic-cbt/start/<int:topic_id>/', views.start_topic_cbt, name='start_topic_cbt'),
    path('topic-cbt/exam/', views.topic_cbt_exam, name='topic_cbt_exam'),
    path('topic-cbt/data/', views.topic_cbt_data, name='topic_cbt_data'),
    path('topic-cbt/submit-answers/', views.topic_cbt_submit_answers, name='topic_cbt_submit_answers'),
    path('topic-cbt/submit/', views.topic_cbt_submit, name='topic_cbt_submit'),

    
]