import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class School(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название школы")
    number = models.CharField(max_length=10, verbose_name="Номер школы")
    city = models.CharField(max_length=100, verbose_name="Город")
    address = models.TextField(blank=True, verbose_name="Адрес")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['name', 'number', 'city']

    def __str__(self):
        return f"{self.name} №{self.number}, {self.city}"

class Test(models.Model):
    TEST_TYPES = [
            ('mixed', 'Смешанный тест'),
            ('text', 'Обычный тест'),
            ('voice', 'Голосовой тест'),
            ('image', 'Фото тест'),
            ('math', 'Математический тест')
    ]

    # for public
    VISIBILITY_CHOICES = [
        ('private',  'Приватный'),
        ('public', 'Публичный'),
        ('unlisted', 'По ссылке')
    ]


    test_format = models.CharField(max_length=10, choices=TEST_TYPES, default='text')


    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    test_type = models.CharField(max_length=10, choices=TEST_TYPES, default='mixed')
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)  # дата создается автоматически
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    timer_seconds = models.PositiveIntegerField(default=0, )  # таймер в секундах
    shuffle_questions = models.BooleanField(default=False, )
    shuffle_answers = models.BooleanField(default=False, )


    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)

    # ⚠️ ИСПРАВЬТЕ ЭТИ ДВЕ СТРОКИ:
    is_published = models.BooleanField(default=False, verbose_name="Опубликован")  # default=True
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='private',  # default='public'
        verbose_name="Видимость теста"
    )

    allow_copying = models.BooleanField(default=True, verbose_name="Разрешить копирование")
    copied_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Скопирован из"
    )
    # ДОБАВЬТЕ ЭТИ ПОЛЯ ДЛЯ ШКОЛЫ:
    school_name = models.CharField(max_length=200, blank=True, verbose_name="Название школы")
    school_number = models.CharField(max_length=10, blank=True, verbose_name="Номер школы")
    school_city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    teacher_name = models.CharField(max_length=100, blank=True, verbose_name="ФИО учителя")



    def __str__(self):
        return self.title

    @property
    def test_link(self):
        return f'/test/{self.public_id}/'

    def can_be_accessed_by(self, user):
        """Проверяет, может ли пользователь получить доступ к тесту"""
        if self.creator == user:
            return True
        if not self.is_published:
            return False
        if self.visibility == "public":
            return True
        if self.visibility == "unlisted":
            return True  # ИСПРАВЛЕНО: должно быть True для доступа по ссылке
        return False





class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Текстовый'),
        ('voice', 'Голосовой'),
        ('photo', 'Фото'),
        ('math', 'Математический тест'),
        ('mixed', 'Смешанный тест'),
    ]

    math_expression = models.TextField(blank=True, null=True, verbose_name="Математическое выражение")
    Question_Formats = [
        ('text_answers', '📸 Вопрос с фото, текстовые ответы'),
        ('photo_answers', '🖼️ Текст вопрос, ответы с фото'),
        ('matching', '🎯 Сопоставление фото'),
        ('find_error', '🔍 Найди ошибку на фото'),
        ('math_formula', '🧮 Математическая формула'),  # ДОБАВЬТЕ ЭТО
        ('math_equation', '═ Математическое уравнение')
    ]

    test = models.ForeignKey("Test", related_name="questions", on_delete=models.CASCADE)
    text = models.TextField()
    image = models.ImageField(upload_to="questions/", blank=True, null=True)
    audio = models.FileField(upload_to="questions/", blank=True, null=True)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='text')
    question_format = models.CharField(max_length=20, choices=Question_Formats, default='text_answers')
    audio_file = models.FileField(upload_to='questions/audio/', blank=True, null=True)
    order = models.IntegerField(default=0)




class Answer(models.Model):
    ANSWER_TYPES = [
        ('text', 'Текстовый'),
        ('voice', 'Голосовой'),
        ('photo', 'Фото'),
    ]

    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='answers/images/', blank=True, null=True)  # Добавьте это поле
    math_expression = models.TextField(blank=True, null=True, verbose_name="Математическое выражение")  # ДОБАВЬТЕ ЭТО

    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    audio_file = models.FileField(upload_to='answers/audio/', blank=True, null=True)
    answer_type = models.CharField(max_length=10, choices=ANSWER_TYPES, default='text')
    matching_text = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0, verbose_name="Порядок")

    def __str__(self):
        return self.text or f"Answer {self.id}"



class StudentAnswer(models.Model):
    test = models.ForeignKey('Test', on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    answer = models.ForeignKey('Answer', on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    student_name = models.CharField(max_length=200, blank=True, null=True)
    student_session = models.CharField(max_length=200, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    solution_image = models.ImageField(upload_to='student_solutions/', blank=True, null=True)  # Фото решения


    # ДОБАВЬТЕ ЭТИ ПОЛЯ:
    selected_answer = models.ForeignKey('Answer', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='student_answers')
    text_answer = models.TextField(blank=True, null=True)  # Для find_error
    matching_data = models.JSONField(blank=True, null=True)  # Для matching

    def __str__(self):
        return f"{self.student_name} - {self.question.text[:50]}"


class ClassGroup(models.Model):
    GRADE_CHOICES = [(str(i), f"{i} класс") for i in range(1, 12)]
    LETTER_CHOICES = [
        ('А', 'А'), ('Б', 'Б'), ('В', 'В'), ('Г', 'Г'), ('Д', 'Д'),
        ('Е', 'Е'), ('Ж', 'Ж'), ('З', 'З'), ('И', 'И'), ('К', 'К'),
    ]

    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, verbose_name="Класс")
    letter = models.CharField(max_length=1, choices=LETTER_CHOICES, verbose_name="Буква")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='class_groups')
    academic_year = models.CharField(max_length=9, default="2024-2025")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        unique_together = ['grade', 'letter', 'teacher', 'academic_year']
        ordering = ['grade', 'letter']

    @property
    def name(self):
        return f"{self.grade}-{self.letter}"

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

    def get_students_count(self):
        return self.students.count()


class Student(models.Model):
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name='students')
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    student_id = models.CharField(max_length=20, blank=True, verbose_name="ID ученика")

    class Meta:
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"

    def __str__(self):
        return f"{self.full_name} ({self.class_group.name})"






class TestResult(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=100, blank=True)
    student_session = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    time_taken = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class_name = models.CharField(max_length=20, blank=True, null=True, verbose_name="Класс")
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Класс")
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ученик")

    class Meta:
        ordering = ['-completed_at']

class QuestionResult(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='question_results')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    time_spent = models.IntegerField(default=0)







