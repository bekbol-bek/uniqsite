from django.urls import path
from . import views

app_name = 'quiz'



urlpatterns = [
    path('', views.main, name='main'),
    path('profile/', views.profile, name='profile'),
    path('create/', views.select_test_type, name='select_test_type'),

    path('create/<str:test_type>/', views.create_test, name='create_test'),


    path('create-mixed-test/<int:test_id>/', views.create_mixed_test, name='create_mixed_test'),
    path('create/text/<int:test_id>/', views.create_text_test, name='create_text_test'),
    path('create/voice/<int:test_id>/', views.create_voice_test, name='create_voice_test'),
    path('create/photo/<int:test_id>/', views.create_photo_test, name='create_photo_test'),
    path('create/math/<int:test_id>/', views.create_math_test, name='create_math_test'),


    path('created/<uuid:public_id>/', views.test_created, name='test_created'),
    path('take/<uuid:public_id>/thanks/', views.take_thanks, name='take_thanks'),

    path('<int:test_id>/', views.test_detail, name='test_detail'),
    path('delete/<int:test_id>/', views.delete_test, name='delete_test'),

    path('delete/<uuid:public_id>/', views.delete_test, name='delete_test'),

    path('take/photo/<uuid:public_id>/', views.take_photo_test, name='take_photo_test'),
    path('take/voice/<uuid:public_id>/', views.take_voice_test, name='take_voice_test'),
    path('take/text/<uuid:public_id>/', views.take_text_test, name='take_text_test'),
    path('take/<uuid:public_id>/', views.take_test, name='take_test'),
    path('math-test/<uuid:public_id>/', views.take_math_test, name='take_math_test'),
    path('test/<uuid:public_id>/mixed/', views.take_mixed_test, name='take_mixed_test'),
    path('result/<int:result_id>/', views.show_result, name='show_result'),
    path('process-results/<uuid:public_id>/', views.process_test_results, name='process_test_results'),



    path('student-results/', views.student_results, name='student_results'),
    path('student-results/<uuid:public_id>/', views.test_student_results, name='test_student_results'),
    path('classes/', views.class_groups, name='class_groups'),
    path('classes/<int:class_id>/', views.class_group_detail, name='class_group_detail'),



    path('math-test/<uuid:public_id>/', views.take_math_test, name='take_math_test'),
    path('math-thanks/<uuid:public_id>/', views.take_math_thanks, name='take_math_thanks'),

    path('student-result-details/<int:result_id>/', views.student_result_details, name='student_result_details'),
    path('test-json/<int:result_id>/', views.test_json, name='test_json'),

]

