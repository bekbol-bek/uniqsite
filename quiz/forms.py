from django import forms
from .models import Test
from django.forms import ModelForm, inlineformset_factory
from .models import Test, Question, Answer


class TestCreateForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'test_type']


class TestForm(ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'test_type', 'timer_seconds', 'shuffle_questions', 'shuffle_answers']

QuestionFormSet = inlineformset_factory(Test, Question, fields=['text', 'order'], extra=3)  # 3 вопроса по умолчанию
AnswerFormSet = inlineformset_factory(Question, Answer, fields=['text', 'is_correct'], extra=3)  # 3 ответа на вопрос

class VoiceQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'audio_file']
        widgets = {
            'audio_file': forms.FileInput(attrs={'accept': 'audio/*'})
        }

class VoiceAnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'audio_file', 'is_correct']
        widgets = {
            'audio_file': forms.FileInput(attrs={'accept': 'audio/*'})
        }

VoiceAnswerFormSet = forms.inlineformset_factory(
    Question, Answer, form=VoiceAnswerForm, extra=3, can_delete=True
)


# forms.py
class PhotoTestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'test_type']


class PhotoQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_format', 'image']
        widgets = {
            'question_format': forms.Select(attrs={'class': 'format-selector'}),
            'image': forms.FileInput(attrs={'accept': 'image/*'})
        }


class PhotoAnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'image', 'is_correct', 'matching_text']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'})
        }


PhotoAnswerFormSet = forms.inlineformset_factory(
    Question, Answer, form=PhotoAnswerForm, extra=4, can_delete=True
)



