from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import TemplateView


urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/cbt/', views.start_cbt, name='start_cbt'),
    path('cbt/question/', views.cbt_question, name='cbt_question'),
    path('cbt/submit/', views.cbt_submit, name='cbt_submit'),
    path('topics/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('obj_questions/<int:question_id>/', views.obj_question_detail, name='obj_question_detail'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('topics/<int:topic_id>/cbt/', views.start_topic_cbt, name='start_topic_cbt'),
    path('topic_cbt/question/', views.topic_cbt_question, name='topic_cbt_question'),
    path('topic_cbt/submit/', views.topic_cbt_submit, name='topic_cbt_submit'),
]