from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('instructions/', views.exam_instructions, name='instructions'),
    path('start/<int:exam_id>/', views.start_exam, name='start_exam'),
    path('take/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('section/<int:exam_id>/<str:section>/', views.exam_section, name='exam_section'),
    path('submit/<int:exam_id>/', views.submit_exam, name='submit_exam'),
    path('submit-section/<int:exam_id>/', views.submit_section, name='submit_section'),
    path('results/<int:exam_id>/', views.exam_results, name='results'),
    
    # API endpoints
    path('api/questions/<int:exam_id>/', views.get_questions, name='get_questions'),
    path('api/save-answer/', views.save_answer, name='save_answer'),
    path('api/time-remaining/<int:exam_id>/', views.check_time_remaining, name='check_time_remaining'),
    path('api/auto-save/', views.auto_save_progress, name='auto_save_progress'),
    path('api/session-status/<int:exam_id>/', views.get_session_status, name='get_session_status'),
    path('recover-session/<int:exam_id>/', views.recover_session, name='recover_session'),
]
