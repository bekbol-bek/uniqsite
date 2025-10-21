from django.contrib import admin
from .models import Test, StudentAnswer, Question, Answer, QuestionResult, TestResult

admin.site.register(Test)
admin.site.register(StudentAnswer)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(TestResult)
admin.site.register(QuestionResult)



