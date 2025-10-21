import uuid

from django.contrib import messages
from django.db.models import Avg, Max, Prefetch
from django.shortcuts import render,get_object_or_404, redirect
from django import template
from .forms import TestCreateForm
from .models import Test,ClassGroup ,Question, Answer, StudentAnswer, TestResult, QuestionResult
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import TestForm, QuestionFormSet, AnswerFormSet
from django.urls import reverse
import random
from django.utils import timezone
import re
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseServerError, HttpResponseNotFound
from django.views.decorators.http import require_http_methods





def select_test_type(request):
    return render(request, 'quiz/select_test_type.html')


def test_detail(request, test_id):
    test = get_object_or_404(Test, pk=test_id)
    question = test.question_set.all()
    return render(request, 'quiz/test_detail.html', {'test': test,
                                                     'question': question})


def main(request):
    tests = Test.objects.all()
    return render(request, 'quiz/main.html', {'tests': tests})



@login_required
def profile(request):
    tests = Test.objects.filter(creator=request.user)

    # Фильтрация по типу теста
    test_type = request.GET.get('type')
    if test_type in ['text', 'voice', 'photo']:
        tests = tests.filter(test_format=test_type)

    return render(request, 'quiz/profile.html', {
        'tests': tests,
        'current_type': test_type})



@login_required
def create_test(request, test_type):
    """Создание базовой информации теста"""
    if test_type not in ['text', 'voice', 'photo', 'math', 'mixed']:
        return redirect('quiz:select_test_type')

    if request.method == 'POST':
        form = TestForm(request.POST)

        if form.is_valid():
            test = form.save(commit=False)
            test.creator = request.user
            test.test_format = test_type
            test.save()

            # Редирект на соответствующую страницу создания контента
            if test_type == 'text':
                return redirect('quiz:create_text_test', test_id=test.id)
            elif test_type == 'voice':
                return redirect('quiz:create_voice_test', test_id=test.id)
            elif test_type == 'photo':
                return redirect('quiz:create_photo_test', test_id=test.id)
            elif test_type == 'math':
                return redirect('quiz:create_math_test', test_id=test.id)
            elif test_type == "mixed":
                return redirect("quiz:create_mixed_test", test_id=test.id)
        else:
            print("Form errors:", form.errors)
    else:
        form = TestForm(initial={'test_type': 'public'})

    return render(request, 'quiz/create_test_base.html', {
        'form': form,
        'test_type': test_type,
    })


@login_required
def create_mixed_test(request, test_id):
    """Создание смешанного теста с динамическими вопросами"""
    test = get_object_or_404(Test, id=test_id, creator=request.user)

    if request.method == 'POST':
        try:
            print("🎯 НАЧАЛО СОЗДАНИЯ СМЕШАННОГО ТЕСТА")
            print("📋 POST данные:", dict(request.POST))
            print("📁 FILES данные:", list(request.FILES.keys()))

            # ДЕТАЛЬНАЯ ОТЛАДКА FILES
            for file_key in request.FILES.keys():
                file_obj = request.FILES[file_key]
                print(f"📄 Файл {file_key}: {file_obj.name}, размер: {file_obj.size}, тип: {file_obj.content_type}")

            # Обрабатываем вопросы
            i = 0
            questions_created = 0

            while f'question_text[{i}]' in request.POST:
                question_text = request.POST.get(f'question_text[{i}]')
                question_format = request.POST.get(f'question_format_{i}', 'text')

                print(f"📝 Вопрос {i}: текст='{question_text}', формат='{question_format}'")

                if question_text and question_text.strip():
                    # СОЗДАЕМ ВОПРОС
                    question = Question.objects.create(
                        test=test,
                        text=question_text.strip(),
                        question_format=question_format,
                        question_type='mixed',
                        order=i
                    )
                    print(f"✅ Создан вопрос {i} с форматом: {question_format}")

                    # Обрабатываем медиа вопроса
                    if f'question_image_{i}' in request.FILES:
                        question_image = request.FILES[f'question_image_{i}']
                        question.image = question_image
                        print(f"🖼️ Добавлено изображение к вопросу {i}: {question_image.name}")

                    if f'question_audio_{i}' in request.FILES:
                        question_audio = request.FILES[f'question_audio_{i}']
                        question.audio = question_audio
                        print(f"🎵 Добавлено аудио к вопросу {i}: {question_audio.name}")

                    question.save()

                    # Обрабатываем ответы для этого вопроса
                    j = 0
                    answers_created = 0

                    while f'answer_text_{i}[{j}]' in request.POST:
                        answer_text = request.POST.get(f'answer_text_{i}[{j}]')
                        answer_type = request.POST.get(f'answer_type_{i}[{j}]', 'text')
                        correct_answer = request.POST.get(f'correct_answer_{i}')

                        print(
                            f"  📝 Ответ {j}: текст='{answer_text}', тип='{answer_type}', правильный='{correct_answer}'")

                        if answer_text and answer_text.strip():
                            is_correct = str(j) == correct_answer

                            # СОЗДАЕМ ОТВЕТ
                            answer = Answer.objects.create(
                                question=question,
                                text=answer_text.strip(),
                                answer_type=answer_type,
                                is_correct=is_correct,
                                order=j
                            )
                            print(f"  ✅ Создан ответ {j} с типом: {answer_type}")

                            # Обрабатываем медиа ответов
                            image_key = f'answer_image_{i}_{j}'
                            audio_key = f'answer_audio_{i}_{j}'

                            if image_key in request.FILES:
                                answer_image = request.FILES[image_key]
                                answer.image = answer_image
                                print(f"  🖼️ Добавлено изображение к ответу {j}: {answer_image.name}")

                            # ВАЖНО: Используем audio_file вместо audio
                            if audio_key in request.FILES:
                                answer_audio = request.FILES[audio_key]
                                answer.audio_file = answer_audio
                                print(f"  🎵 Добавлено аудио к ответу {j}: {answer_audio.name}")

                            # ВАЖНО: Сохраняем ответ после добавления медиа
                            answer.save()
                            print(f"  💾 Ответ {j} сохранен")

                            answers_created += 1

                        j += 1

                    # ИСПРАВЛЕНО: answers_created вместо answers_answers
                    print(f"✅ Вопрос {i} создан с {answers_created} ответами")
                    questions_created += 1

                i += 1

            print(f"🎉 СОЗДАНО ВОПРОСОВ: {questions_created}")

            if questions_created == 0:
                return render(request, 'quiz/create_mixed_test.html', {
                    'test': test,
                    'error': 'Не создано ни одного вопроса. Проверьте заполнение формы.'
                })

            return redirect('quiz:test_created', public_id=str(test.public_id))

        except Exception as e:
            print(f"💥 ОШИБКА: {str(e)}")
            import traceback
            print(traceback.format_exc())

            return render(request, 'quiz/create_mixed_test.html', {
                'test': test,
                'error': f'Ошибка при создании вопросов: {str(e)}'
            })

    return render(request, 'quiz/create_mixed_test.html', {'test': test})



def take_mixed_test(request, public_id):
    """Прохождение смешанного теста"""
    test = get_object_or_404(Test, public_id=public_id)
    questions = test.questions.prefetch_related('answers').order_by('order')

    # Проверяем, не проходил ли уже пользователь этот тест
    session_key = _ensure_session(request)
    existing_result = TestResult.objects.filter(
        test=test,
        student_session=session_key
    ).first()

    if existing_result:
        return render(request, 'quiz/take_mixed_test.html', {
            'test': test,
            'questions': questions,
            'already_completed': True,
            'existing_result': existing_result
        })

    return render(request, 'quiz/take_mixed_test.html', {
        'test': test,
        'questions': questions,
        'already_completed': False
    })

@login_required
def create_text_test(request, test_id):
    """Создание текстового теста с динамическими вопросами"""
    test = get_object_or_404(Test, id=test_id, creator=request.user)

    if request.method == 'POST':
        # Обрабатываем вопросы
        question_texts = request.POST.getlist('question_text')

        for i, question_text in enumerate(question_texts):
            if question_text.strip():  # только если вопрос не пустой
                question = Question.objects.create(
                    test=test,
                    text=question_text,
                    order=i
                )

                # Обрабатываем ответы для этого вопроса
                answer_texts = request.POST.getlist(f'answers_{i}')
                is_correct_index = int(request.POST.get(f'correct_answer_{i}', -1))

                for j, answer_text in enumerate(answer_texts):
                    if answer_text.strip():  # только если ответ не пустой
                        Answer.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=(j == is_correct_index)  # правильный ответ по индексу
                        )

        return redirect('quiz:test_created', public_id=str(test.public_id))

    return render(request, 'quiz/create_text_test.html', {'test': test})

def take_text_test(request, public_id):
    """Прохождение текстового теста"""
    test = get_object_or_404(Test, public_id=public_id)

    # ОБРАБОТКА POST ЗАПРОСА - ТОЛЬКО ОДИН БЛОК!
    if request.method == "POST":
        return process_test_results(request, public_id)

    # ПОДГОТОВКА ДАННЫХ ДЛЯ ОТОБРАЖЕНИЯ (ТОЛЬКО ДЛЯ GET ЗАПРОСА)
    questions = list(test.questions.all().order_by("order", "id"))
    if test.shuffle_questions:
        random.shuffle(questions)

    display_questions = []
    for q in questions:
        answers = list(q.answers.all())
        if test.shuffle_answers:
            random.shuffle(answers)
        display_questions.append({"question": q, "answers": answers})

    return render(request, "quiz/take_test.html", {
        "test": test,
        "display_questions": display_questions
    })
# views.py
@login_required
def create_voice_test(request, test_id):
    """Создание голосового теста с несколькими вопросами"""
    test = get_object_or_404(Test, id=test_id, creator=request.user)

    if request.method == 'POST':
        try:
            # Очищаем старые вопросы (если пересоздаем)
            test.questions.all().delete()

            # Обрабатываем все вопросы
            question_count = 0
            questions_created = 0

            # Ищем все вопросы в POST данных
            while True:
                # Проверяем существование вопроса по разным полям
                question_text = request.POST.get(f'question_text_{question_count}')
                question_audio = request.FILES.get(f'question_audio_{question_count}')

                # Если нет ни текста, ни аудио - выходим из цикла
                if not question_text and not question_audio:
                    # Проверяем следующий вопрос, возможно пропуск
                    next_question_text = request.POST.get(f'question_text_{question_count + 1}')
                    next_question_audio = request.FILES.get(f'question_audio_{question_count + 1}')
                    if not next_question_text and not next_question_audio:
                        break

                # Получаем ответы для этого вопроса
                answer_texts = request.POST.getlist(f'answer_text_{question_count}[]')
                correct_answer_index = request.POST.get(f'correct_answer_{question_count}')

                # Проверяем, есть ли данные для создания вопроса
                if answer_texts and correct_answer_index is not None:
                    try:
                        correct_answer_index = int(correct_answer_index)

                        # Создаем вопрос
                        question = Question.objects.create(
                            test=test,
                            text=question_text or f"Голосовой вопрос {question_count + 1}",
                            question_type='voice',
                            audio_file=question_audio,
                            order=question_count
                        )

                        # Получаем аудио файлы ответов для этого вопроса
                        answer_audio_files = {}

                        # Обрабатываем файлы с именами answer_audio_{question_index}[]
                        audio_files = request.FILES.getlist(f'answer_audio_{question_count}[]')
                        for i, audio_file in enumerate(audio_files):
                            if i < len(answer_texts):
                                answer_audio_files[i] = audio_file

                        # Создаем ответы
                        for i, answer_text in enumerate(answer_texts):
                            answer_audio = answer_audio_files.get(i)

                            Answer.objects.create(
                                question=question,
                                text=answer_text or f"Ответ {i + 1}",
                                audio_file=answer_audio,
                                answer_type='voice',
                                is_correct=(i == correct_answer_index)
                            )

                        questions_created += 1
                        print(f"✅ Создан вопрос {question_count} с {len(answer_texts)} ответами")

                    except Exception as e:
                        print(f"❌ Ошибка при создании вопроса {question_count}: {str(e)}")
                        messages.error(request, f"Ошибка при создании вопроса {question_count + 1}: {str(e)}")

                question_count += 1

            if questions_created > 0:
                messages.success(request, f"Тест создан успешно! Добавлено {questions_created} вопросов.")
                return redirect('quiz:test_created', public_id=str(test.public_id))
            else:
                messages.error(request, "Не удалось создать ни одного вопроса. Проверьте заполнение формы.")
                return render(request, 'quiz/create_voice_test.html', {'test': test})

        except Exception as e:
            print(f"💥 Общая ошибка: {str(e)}")
            messages.error(request, f"Ошибка при создании теста: {str(e)}")
            return render(request, 'quiz/create_voice_test.html', {'test': test})

    return render(request, 'quiz/create_voice_test.html', {'test': test})

def take_voice_test(request, public_id):
    """Прохождение голосового теста"""
    test = get_object_or_404(Test, public_id=public_id)
    questions = test.questions.filter(question_type='voice').order_by('order')

    if not questions.exists():
        questions = test.questions.all().order_by('order')

    # Проверка на повторное прохождение
    session_key = _ensure_session(request)
    existing_result = TestResult.objects.filter(
        test=test,
        student_session=session_key
    ).first()

    if existing_result:
        return render(request, "quiz/take_voice_test.html", {
            "test": test,
            "questions": questions,
            "already_completed": True,
            "existing_result": existing_result
        })

    if request.method == 'POST':
        # Сохраняем данные в сессии для process_test_results
        request.session['voice_test_data'] = {
            'student_name': request.POST.get("student_name", "").strip() or "Аноним",
            'class_group': request.POST.get('class_group', '').strip(),
            'public_id': public_id
        }

        # Перенаправляем в process_test_results
        return redirect('quiz:process_test_results', public_id=public_id)

    return render(request, "quiz/take_voice_test.html", {
        "test": test,
        "questions": questions,
        "already_completed": False
    })


def _ensure_session(request):
    """Создает или возвращает session key с фиксами для iOS"""
    # iOS ФИКС: Сначала пробуем получить существующую сессию
    if not request.session.session_key:
        request.session.create()
        print(f"🆕 Создана НОВАЯ сессия: {request.session.session_key}")
    else:
        print(f"🔁 Используется СУЩЕСТВУЮЩАЯ сессия: {request.session.session_key}")

    # iOS ФИКС: Принудительно сохраняем и обновляем сессию
    request.session.modified = True
    request.session.save()

    return request.session.session_key

def take_test(request, public_id):
    """Умная функция, которая определяет тип теста и перенаправляет"""
    test = get_object_or_404(Test, public_id=public_id)

    # Проверяем, проходил ли уже ученик этот тест
    session_key = _ensure_session(request)
    existing_result = TestResult.objects.filter(
        test=test,
        student_session=session_key
    ).first()

    if existing_result:
        # Если уже проходил, показываем результат
        return redirect('quiz:show_result', result_id=existing_result.id)

    # Определяем тип теста и перенаправляем на соответствующую страницу
    if test.test_format == 'voice':
        return redirect('quiz:take_voice_test', public_id=public_id)
    elif test.test_format == 'photo':
        return redirect('quiz:take_photo_test', public_id=public_id)
    elif test.test_format == 'math':
        return redirect('quiz:take_math_test', public_id=public_id)
    elif test.test_format == 'mixed':
        return redirect('quiz:take_mixed_test', public_id=public_id)
    else:
        # По умолчанию текстовый тест
        return take_text_test(request, public_id)


def take_thanks(request, public_id):
    score = request.session.get('last_score')
    test = get_object_or_404(Test, public_id=public_id)
    return render(request, 'quiz/thanks.html', {'test': test, 'score': score})



@login_required
def test_created(request, public_id):
    test = get_object_or_404(Test, public_id=public_id)
    test_link = request.build_absolute_uri(
        reverse('quiz:take_test', args=[str(test.public_id)])
    )
    return render(request, 'quiz/test_created.html', {'test_link': test_link})



@require_http_methods(["POST"])
@login_required
def delete_test(request, test_id):
    """Удаление теста через AJAX"""
    try:
        # Ищем тест который принадлежит текущему пользователю
        test = Test.objects.get(id=test_id, creator=request.user)
        test_title = test.title
        test.delete()

        return JsonResponse({
            'success': True,
            'message': f'Тест "{test_title}" успешно удален'
        })

    except Test.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Тест не найден или у вас нет прав для его удаления'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при удалении: {str(e)}'
        }, status=500)


@login_required
def create_photo_test(request, test_id):
    """Создание фото теста"""
    test = get_object_or_404(Test, id=test_id, creator=request.user)

    if request.method == 'POST':
        # Получаем все вопросы из формы
        question_count = 0
        while True:
            # ИСПРАВЛЕНО: получаем формат для КАЖДОГО вопроса отдельно
            question_text = request.POST.get(f'question_text_{question_count}', '')
            question_format = request.POST.get(f'question_format_{question_count}', 'text_answers')  # ИСПРАВЛЕНО

            # Если нет вопроса с таким индексом, выходим из цикла
            if not any(key.startswith(f'question_text_{question_count}') or
                       key.startswith(f'answer_text_{question_count}') for key in request.POST.keys()):
                break

            question_image = request.FILES.get(f'question_image_{question_count}')

            print(f"DEBUG: Вопрос {question_count} - Формат: {question_format}")
            print(f"DEBUG: Вопрос {question_count} - Текст: {question_text}")
            print(f"DEBUG: Вопрос {question_count} - Изображение: {question_image}")

            # Определяем порядок вопроса
            last_question = test.questions.order_by('-order').first()
            next_order = last_question.order + 1 if last_question else 0

            # Создаем вопрос
            question = Question.objects.create(
                test=test,
                text=question_text,
                question_type='photo',
                question_format=question_format,  # Сохраняем индивидуальный формат
                image=question_image,
                order=next_order
            )

            print(f"DEBUG: Создан вопрос ID {question.id} с форматом: {question_format}")

            # Обрабатываем ответы в зависимости от формата
            if question_format == 'text_answers':
                # 📸 Вопрос с фото, текстовые ответы
                answer_texts = request.POST.getlist(f'answer_text_{question_count}[]')
                correct_answer_index = int(request.POST.get(f'correct_answer_{question_count}', 0))

                print(f"DEBUG: Текстовые ответы - {answer_texts}")
                print(f"DEBUG: Правильный ответ индекс - {correct_answer_index}")

                for i, text in enumerate(answer_texts):
                    if text.strip():
                        Answer.objects.create(
                            question=question,
                            text=text,
                            answer_type='text',
                            is_correct=(i == correct_answer_index)
                        )
                        print(f"DEBUG: Создан ответ '{text}', правильный: {i == correct_answer_index}")

            elif question_format == 'photo_answers':
                # 🖼️ Текст вопрос, ответы с фото
                answer_texts = request.POST.getlist(f'answer_text_{question_count}[]')
                answer_images = request.FILES.getlist(f'answer_image_{question_count}[]')
                correct_answer_index = int(request.POST.get(f'correct_answer_{question_count}', 0))

                print(f"DEBUG: Тексты ответов - {answer_texts}")
                print(f"DEBUG: Изображения ответов - {[img.name for img in answer_images]}")
                print(f"DEBUG: Правильный ответ индекс - {correct_answer_index}")

                for i in range(len(answer_texts)):
                    text = answer_texts[i]
                    image = answer_images[i] if i < len(answer_images) else None

                    if text.strip() or image:
                        Answer.objects.create(
                            question=question,
                            text=text,
                            image=image,
                            answer_type='photo',
                            is_correct=(i == correct_answer_index)
                        )
                        print(f"DEBUG: Создан ответ с фото: текст='{text}', изображение={image}")

            elif question_format == 'matching':
                # 🎯 Сопоставление фото
                matching_texts = request.POST.getlist(f'matching_text_{question_count}[]')
                answer_images = request.FILES.getlist(f'answer_image_{question_count}[]')

                print(f"DEBUG: Тексты для сопоставления - {matching_texts}")
                print(f"DEBUG: Изображения для сопоставления - {[img.name for img in answer_images]}")

                for i in range(max(len(matching_texts), len(answer_images))):
                    text = matching_texts[i] if i < len(matching_texts) else ""
                    image = answer_images[i] if i < len(answer_images) else None

                    if text.strip() or image:
                        Answer.objects.create(
                            question=question,
                            image=image,
                            matching_text=text,
                            answer_type='photo',
                            is_correct=True
                        )
                        print(f"DEBUG: Создан элемент сопоставления: текст='{text}', изображение={image}")

            elif question_format == 'find_error':
                # 🔍 Найди ошибку на фото
                correct_answer = request.POST.get(f'correct_answer_{question_count}', '')

                print(f"DEBUG: Правильный ответ для 'найди ошибку' - '{correct_answer}'")

                if correct_answer.strip():
                    Answer.objects.create(
                        question=question,
                        text=correct_answer,
                        answer_type='text',
                        is_correct=True
                    )

            question_count += 1

        if 'add_another' in request.POST:
            return redirect('quiz:create_photo_test', test_id=test.id)
        else:
            return redirect('quiz:test_created', public_id=str(test.public_id))

    return render(request, 'quiz/create_photo_test.html', {'test': test})

def take_photo_test(request, public_id):
    """Прохождение фото теста"""
    test = get_object_or_404(Test, public_id=public_id)

    # ДЕБАГ: Проверим все вопросы теста
    all_questions = test.questions.all()
    print(f"DEBUG: Все вопросы теста: {all_questions.count()}")
    for q in all_questions:
        print(f"DEBUG: Вопрос {q.id}: тип={q.question_type}, формат={q.question_format}")

    # ИСПРАВЛЕНО: Получаем ВСЕ вопросы теста, а не только фото
    questions = test.questions.all()  # Убрали фильтрацию
    print(f"DEBUG: Все вопросы теста (без фильтрации): {questions.count()}")

    # Предзагружаем ответы
    questions = questions.prefetch_related('answers').order_by('order')

    print(f"DEBUG: Финальное количество вопросов: {questions.count()}")
    for question in questions:
        print(f"DEBUG: Вопрос {question.id}:")
        print(f"  - Формат: {question.question_format}")
        print(f"  - Тип: {question.question_type}")
        print(f"  - Текст: {question.text}")
        print(f"  - Изображение: {question.image}")
        print(f"  - Аудио: {question.audio}")
        print(f"  - Ответов: {question.answers.count()}")
        for answer in question.answers.all():
            print(f"    Ответ {answer.id}: текст='{answer.text}', изображение={answer.image}, аудио={answer.audio_file}")

    if not request.session.session_key:
        request.session.create()
    request.session.modified = True

    # Проверяем, не проходил ли уже пользователь этот тест
    session_key = request.session.session_key
    print(f'DEBUG: Финальная сессия: {session_key}')
    existing_result = TestResult.objects.filter(
        test=test,
        student_session=session_key
    ).first()

    if existing_result:
        print(f'DEBUG: Найден существующий результат: {existing_result.id}')
        return render(request, "quiz/take_photo_test.html", {
            "test": test,
            "questions": questions,
            "already_completed": True,
            "existing_result": existing_result
        })
    else:
        print(f'DEBUG: Результат не найден, можно проходить тест')

    if request.method == "POST":
        return process_test_results(request, public_id)

    return render(request, "quiz/take_photo_test.html", {
        "test": test,
        "questions": questions,
        "already_completed": False
    })


def process_test_results(request, public_id):
    """УНИВЕРСАЛЬНАЯ обработка результатов ВСЕХ типов тестов"""
    test = get_object_or_404(Test, public_id=public_id)
    questions = test.questions.all().prefetch_related('answers')

    session_key = _ensure_session(request)
    existing_result = TestResult.objects.filter(
        test=test,
        student_session=session_key
    ).first()

    if existing_result:
        print(f"DEBUG: Обнаружена повторная отправка! Результат: {existing_result.id}")
        return render(request, "quiz/take_photo_test.html", {
            "test": test,
            "questions": test.questions.all(),
            "already_completed": True,
            "existing_result": existing_result
        })

    student_name = request.POST.get("student_name") or "Аноним"
    class_group = request.POST.get("class_group", "")

    total = 0
    correct = 0
    student_answers = []

    print("=== ОБРАБОТКА РЕЗУЛЬТАТОВ ТЕСТА ===")
    print(f"Тест: {test.title}, сессия: {session_key}")
    print(f"POST данные: {list(request.POST.keys())}")
    print(f"FILES данные: {list(request.FILES.keys())}")  # Добавим отладку файлов

    for question in questions:
        total += 1
        is_correct = False
        selected_answer = None
        text_answer = None
        matching_data = None
        solution_photo = None

        print(f"Вопрос {question.id} ({question.question_format}): {question.text[:50]}...")

        # Обрабатываем фото решения
        solution_photo = request.FILES.get(f'solution_photo_{question.id}')
        if solution_photo:
            print(f"📸 Найдено фото решения для вопроса {question.id}: {solution_photo.name}")
        else:
            print(f"📸 Фото решения для вопроса {question.id} не найдено")

        # ОБРАБОТКА ПО ФОРМАТУ ВОПРОСА
        if question.question_format in ['text_answers', 'photo_answers', 'default', 'text', 'image', 'voice', 'math',
                                        'mixed']:
            # ПРОБУЕМ РАЗНЫЕ ВАРИАНТЫ ИМЕН ПОЛЕЙ
            answer_id = (request.POST.get(f"q_{question.id}") or
                         request.POST.get(f"question_{question.id}") or
                         request.POST.get(f"answer_{question.id}"))

            print(f"  Поиск ответа для вопроса {question.id}:")
            print(f"    q_{question.id} = {request.POST.get(f'q_{question.id}')}")
            print(f"    question_{question.id} = {request.POST.get(f'question_{question.id}')}")
            print(f"    answer_{question.id} = {request.POST.get(f'answer_{question.id}')}")
            print(f"  Выбранный ID: {answer_id}")

            if answer_id:
                try:
                    selected_answer = Answer.objects.get(id=int(answer_id))
                    is_correct = selected_answer.is_correct
                    print(f"  ✅ Ответ найден: '{selected_answer.text}' (правильный: {is_correct})")
                except (Answer.DoesNotExist, ValueError) as e:
                    is_correct = False
                    print(f"  ❌ Ошибка поиска ответа: {e}")

        elif question.question_format == 'matching':
            matching_score = 0
            total_matches = question.answers.count()
            matching_data = {}

            print(f"  Обработка matching вопроса с {total_matches} элементами")

            # ВАЖНО: Используем forloop.counter0 как в HTML
            for i, answer in enumerate(question.answers.all()):
                # ИСПРАВЛЕНО: используем индекс, а не ID ответа
                user_selected_id = request.POST.get(f"match_{question.id}_{i}")
                print(f"    Элемент {i}: match_{question.id}_{i} = {user_selected_id}")

                if user_selected_id:
                    try:
                        user_answer = Answer.objects.get(id=int(user_selected_id))

                        # ИСПРАВЛЕНО: Правильная логика проверки
                        # Для matching каждый элемент имеет свое правильное сопоставление
                        # Правильный ответ для позиции i - это answer (текущий в цикле)
                        is_correct_match = (user_answer.matching_text == answer.matching_text)

                        matching_data[str(i)] = {
                            'selected_id': user_selected_id,
                            'selected_text': user_answer.matching_text,
                            'correct_id': answer.id,
                            'correct_text': answer.matching_text,
                            'is_correct': is_correct_match
                        }

                        if is_correct_match:
                            matching_score += 1
                            print(
                                f"    ✅ Правильное сопоставление: {user_answer.matching_text} = {answer.matching_text}")
                        else:
                            print(
                                f"    ❌ Неправильное сопоставление: {user_answer.matching_text} != {answer.matching_text}")

                    except (Answer.DoesNotExist, ValueError) as e:
                        print(f"    ❌ Ошибка сопоставления: {e}")
                        matching_data[str(i)] = {
                            'selected_id': None,
                            'selected_text': 'Не выбрано',
                            'correct_id': answer.id,
                            'correct_text': answer.matching_text,
                            'is_correct': False
                        }
                else:
                    print(f"    ❌ Нет выбора для элемента {i}")
                    matching_data[str(i)] = {
                        'selected_id': None,
                        'selected_text': 'Не выбрано',
                        'correct_id': answer.id,
                        'correct_text': answer.matching_text,
                        'is_correct': False
                    }

            # ИСПРАВЛЕНО: Вопрос считается правильным только если ВСЕ сопоставления верны
            is_correct = (matching_score == total_matches) if total_matches > 0 else False
            print(f"  Matching результат: {matching_score}/{total_matches}, правильный: {is_correct}")

        elif question.question_format == 'find_error':
            text_answer = request.POST.get(f"answer_{question.id}", "").strip()
            print(f"  Find error ответ: '{text_answer}'")

            correct_answer = question.answers.filter(is_correct=True).first()

            if correct_answer and text_answer:
                user_lower = text_answer.lower()
                correct_lower = correct_answer.text.lower()

                user_words = set(user_lower.split())
                correct_words = set(correct_lower.split())
                common_words = user_words.intersection(correct_words)

                similarity = len(common_words) / len(correct_words) if correct_words else 0
                is_correct = similarity > 0.3
                print(f"  Сходство: {similarity:.2f}, правильный: {is_correct}")

        # Создаем объект StudentAnswer
        student_answer = StudentAnswer(
            test=test,
            question=question,
            student_name=student_name,
            student_session=session_key,
            selected_answer=selected_answer,
            is_correct=is_correct,
            text_answer=text_answer,
            matching_data=matching_data,
            submitted_at=timezone.now()
        )

        # Сохраняем фото решения если есть
        if solution_photo:
            student_answer.solution_image = solution_photo
            print(f"  📸 Фото решения добавлено к ответу")

        student_answers.append(student_answer)

        if is_correct:
            correct += 1

        print(f"  Результат: {'✅ Правильно' if is_correct else '❌ Неправильно'}\n")

    # Массовое сохранение всех ответов
    # ВАЖНО: bulk_create не сохраняет FileField, поэтому нужно сохранять по отдельности
    for student_answer in student_answers:
        student_answer.save()

    # Создаем общий результат теста
    percentage = (correct / total * 100) if total > 0 else 0

    test_result = TestResult.objects.create(
        test=test,
        student_name=student_name,
        student_session=session_key,
        score=correct,
        total_questions=total,
        percentage=percentage,
        class_name=class_group,
        completed_at=timezone.now()
    )

    print(f"=== ИТОГ ===")
    print(f"Правильных ответов: {correct}/{total} ({percentage:.1f}%)")
    print(f"Создан TestResult ID: {test_result.id}")
    print(f"Создано StudentAnswer записей: {len(student_answers)}")

    return redirect('quiz:show_result', result_id=test_result.id)
def show_result(request, result_id):
    """Показ результата после прохождения теста"""
    try:
        print(f"=== ПОПЫТКА ЗАГРУЗКИ РЕЗУЛЬТАТА {result_id} ===")

        result = get_object_or_404(TestResult, id=result_id)

        print(f"✅ Результат найден: {result.student_name}")
        print(f"📊 Тест: {result.test.title}")

        # УПРОЩЕННАЯ ПРОВЕРКА ДОСТУПА
        has_access = (
                result.student_session == request.session.session_key or
                (request.user.is_authenticated and result.test.creator == request.user)
        )

        if not has_access:
            print("❌ Доступ запрещен")
            return HttpResponseForbidden("У вас нет доступа к этому результату")

        print("✅ Доступ разрешен")

        # Получаем детальные ответы студента
        student_answers = StudentAnswer.objects.filter(
            test=result.test,
            student_session=result.student_session
        ).select_related('question', 'selected_answer').order_by('question__order', 'id')

        print(f"📋 Найдено ответов: {student_answers.count()}")

        return render(request, 'quiz/show_results.html', {
            'result': result,
            'test': result.test,
            'student_answers': student_answers,
        })

    except TestResult.DoesNotExist:
        print(f"❌ Результат {result_id} не найден")
        return HttpResponseNotFound("Результат не найден")
    except Exception as e:
        print(f"💥 Критическая ошибка в show_result: {str(e)}")
        import traceback
        print(f"🔍 Детали ошибки:\n{traceback.format_exc()}")
        return HttpResponseServerError(f"Ошибка при загрузке результата: {str(e)}")
# УДАЛИТЕ ДУБЛИРУЮЩУЮ ФУНКЦИЮ - оставьте только process_test_results
# def process_unified_test_results(request, public_id):  # <-- УДАЛИТЕ ЭТУ ФУНКЦИЮ


@login_required
def create_math_test(request, test_id):
    """Создание математического теста"""
    test = get_object_or_404(Test, id=test_id, creator=request.user)

    if request.method == 'POST':
        # Обрабатываем динамические поля
        i = 0
        while f'question_text_{i}' in request.POST:
            question_text = request.POST.get(f'question_text_{i}', '')
            math_expression = request.POST.get(f'math_expression_{i}', '')
            question_format = request.POST.get(f'question_format_{i}', 'math_formula')

            # Получаем фото вопроса
            question_image = request.FILES.get(f'question_image_{i}')

            # Создаем вопрос
            question = Question.objects.create(
                test=test,
                text=question_text,
                math_expression=math_expression,
                question_type='math',
                question_format=question_format,
                order=i,
                image=question_image
            )

            # Обрабатываем ответы для этого вопроса
            j = 0
            while f'answer_text_{i}_{j}' in request.POST:
                answer_text = request.POST.get(f'answer_text_{i}_{j}', '')
                answer_formula = request.POST.get(f'answer_formula_{i}_{j}', '')
                answer_image = request.FILES.get(f'answer_image_{i}_{j}')

                # Определяем правильный ответ
                correct_answer_index = request.POST.get(f'correct_answer_{i}')
                is_correct = (str(j) == correct_answer_index)

                # Создаем ответ
                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    math_expression=answer_formula,
                    image=answer_image,
                    is_correct=is_correct,
                    order=j
                )
                j += 1

            i += 1

        return redirect('quiz:test_created', public_id=str(test.public_id))

    return render(request, 'quiz/create_math_test.html', {'test': test})

def _process_math_formula_answers(request, question):
    """Обработка математических формул - выбор правильной формулы с фото"""
    answer_formulas = request.POST.getlist('answer_formula[]')
    answer_images = request.FILES.getlist('answer_images[]')
    correct_answer_index = int(request.POST.get('correct_answer', 0))

    for i, formula in enumerate(answer_formulas):
        answer_image = answer_images[i] if i < len(answer_images) else None

        # ВАЖНО: Сохраняем формулу в math_expression, а не в text
        Answer.objects.create(
            question=question,
            text="",  # Оставляем text пустым для формул
            math_expression=formula,  # Сохраняем формулу здесь
            image=answer_image,
            is_correct=(i == correct_answer_index),
            order=i
        )

def _process_math_equation_answers(request, question):
    """Обработка математических уравнений - решение уравнений с фото"""
    answer_texts = request.POST.getlist('answer_text[]')
    answer_formulas = request.POST.getlist('answer_formula[]')  # Добавляем формулы
    answer_images = request.FILES.getlist('answer_images[]')
    correct_answer_index = int(request.POST.get('correct_answer', 0))

    for i, text in enumerate(answer_texts):
        if text.strip():
            answer_image = answer_images[i] if i < len(answer_images) else None
            answer_formula = answer_formulas[i] if i < len(answer_formulas) else ""

            Answer.objects.create(
                question=question,
                text=text,
                math_expression=answer_formula,  # Сохраняем формулу
                image=answer_image,
                is_correct=(i == correct_answer_index),
                order=i
            )

def _process_math_formula_answers(request, question):
    """Обработка математических формул - выбор правильной формулы с фото"""
    answer_formulas = request.POST.getlist('answer_formula[]')
    answer_images = request.FILES.getlist('answer_images[]')
    correct_answer_index = int(request.POST.get('correct_answer', 0))

    for i, formula in enumerate(answer_formulas):
        answer_image = answer_images[i] if i < len(answer_images) else None

        # Определяем текст ответа в зависимости от того что заполнено
        if formula.strip() and answer_image:
            answer_text = formula  # И формула и фото
        elif formula.strip():
            answer_text = formula  # Только формула
        elif answer_image:
            answer_text = "Ответ с изображением"  # Только фото
        else:
            answer_text = f"Ответ {i + 1}"  # Оба пустые - создаем базовый ответ

        Answer.objects.create(
            question=question,
            text=answer_text,
            image=answer_image,
            is_correct=(i == correct_answer_index),
            order=i
        )



def _process_math_proof_answers(request, question):
    """Обработка математических доказательств с фото"""
    proof_steps = request.POST.getlist('proof_step[]')
    proof_images = request.FILES.getlist('proof_images[]')  # Фото для шагов

    for i, step in enumerate(proof_steps):
        if step.strip():
            proof_image = proof_images[i] if i < len(proof_images) else None

            Answer.objects.create(
                question=question,
                text=step,
                image=proof_image,  # Сохраняем фото шага
                order=i,
                is_correct=True
            )


def _process_math_derivative_answers(request, question):
    """Обработка производных с фото"""
    correct_solution = request.POST.get('correct_solution', '')
    solution_image = request.FILES.get('solution_image')  # Фото решения

    if correct_solution.strip():
        Answer.objects.create(
            question=question,
            text=correct_solution,
            image=solution_image,  # Сохраняем фото решения
            is_correct=True
        )


def _process_math_integral_answers(request, question):
    """Обработка интегралов с фото"""
    correct_solution = request.POST.get('correct_solution', '')
    solution_image = request.FILES.get('solution_image')  # Фото решения

    if correct_solution.strip():
        Answer.objects.create(
            question=question,
            text=correct_solution,
            image=solution_image,  # Сохраняем фото решения
            is_correct=True
        )


def take_math_test(request, public_id):
    """Прохождение математического теста с фото решениями"""
    test = get_object_or_404(Test, public_id=public_id)

    # ВАЖНО: Предзагружаем ответы с изображениями и математическими выражениями
    questions = test.questions.filter(question_type='math').prefetch_related(
        Prefetch('answers', queryset=Answer.objects.all())
    ).order_by('order')

    # ДЕБАГ: Проверим что загружается
    print(f"=== ДЕБАГ: Математический тест {test.title} ===")
    print(f"Количество вопросов: {questions.count()}")

    for question in questions:
        print(f"Вопрос {question.id}:")
        print(f"  - Текст: {question.text}")
        print(f"  - Формат: {question.question_format}")
        print(f"  - Мат. выражение: {question.math_expression}")
        print(f"  - Изображение: {question.image}")
        print(f"  - Количество ответов: {question.answers.count()}")

        for answer in question.answers.all():
            print(f"    Ответ {answer.id}:")
            print(f"      - Текст: '{answer.text}'")
            print(f"      - Мат. выражение: '{answer.math_expression}'")
            print(f"      - Изображение: {answer.image}")
            print(f"      - Правильный: {answer.is_correct}")

    # Проверяем, проходил ли пользователь уже тест
    session_key = request.session.session_key
    existing_result = TestResult.objects.filter(
        test=test,
        student_session=session_key
    ).first()

    already_completed = existing_result is not None

    # ЕСЛИ УЖЕ ПРОХОДИЛ - показываем сообщение
    if already_completed:
        context = {
            'test': test,
            'questions': questions,
            'already_completed': already_completed,
            'existing_result': existing_result,
            'student_session': session_key,
        }
        return render(request, "quiz/take_math_test.html", context)

    # ЕСЛИ ЕЩЕ НЕ ПРОХОДИЛ - обрабатываем форму
    if request.method == "POST":
        print("=== ОБРАБОТКА POST ЗАПРОСА ДЛЯ MATH ТЕСТА ===")
        print(f"POST данные: {list(request.POST.keys())}")
        print(f"FILES данные: {list(request.FILES.keys())}")

        # Детальная отладка файлов
        for key, file in request.FILES.items():
            print(f"📁 Файл: {key} -> {file.name} ({file.size} bytes)")

        session_key = _ensure_session(request)
        student_name = request.POST.get("student_name") or "Аноним"
        class_group = request.POST.get("class_group", "")

        total = 0
        correct = 0
        student_answers = []  # Для массового сохранения

        for question in questions:
            total += 1
            is_correct = False
            selected_answer = None
            text_answer = None
            matching_data = None

            # ВАЖНО: ПОЛУЧАЕМ ФОТО РЕШЕНИЯ ДЛЯ КАЖДОГО ВОПРОСА
            solution_photo_key = f'solution_photo_{question.id}'
            solution_photo = request.FILES.get(solution_photo_key)

            print(f"🔍 Поиск фото решения для вопроса {question.id} по ключу: '{solution_photo_key}'")
            if solution_photo:
                print(f"✅ Фото найдено: {solution_photo.name}, размер: {solution_photo.size} bytes")
            else:
                print(f"❌ Фото решения для вопроса {question.id} не найдено")

            if question.question_format == 'math_formula':
                # Вопросы с выбором формулы
                selected_answer_id = request.POST.get(f"q_{question.id}")
                if selected_answer_id:
                    try:
                        selected_answer = Answer.objects.get(id=int(selected_answer_id))
                        is_correct = selected_answer.is_correct
                        print(f"✅ Выбран ответ: {selected_answer.text}, правильный: {is_correct}")
                    except (Answer.DoesNotExist, ValueError):
                        is_correct = False
                        print(f"❌ Ошибка при поиске ответа")

            elif question.question_format == 'math_equation':
                # Вопросы с решением уравнений
                user_solution = request.POST.get(f"solution_{question.id}", "").strip()
                text_answer = user_solution  # Сохраняем текстовый ответ

                if user_solution:
                    correct_answers = question.answers.filter(is_correct=True)
                    if correct_answers.exists():
                        user_normalized = _normalize_math_expression(user_solution)
                        for correct_answer in correct_answers:
                            correct_normalized = _normalize_math_expression(correct_answer.text)
                            if user_normalized == correct_normalized:
                                is_correct = True
                                break
                    print(f"🧮 Ответ уравнения: '{user_solution}', правильный: {is_correct}")

            elif question.question_format == 'math_geometry':
                # Геометрические задачи
                user_answer = request.POST.get(f"geometry_{question.id}", "").strip()
                text_answer = user_answer

                if user_answer:
                    correct_answers = question.answers.filter(is_correct=True)
                    if correct_answers.exists():
                        user_normalized = _normalize_math_expression(user_answer)
                        for correct_answer in correct_answers:
                            correct_normalized = _normalize_math_expression(correct_answer.text)
                            if user_normalized == correct_normalized:
                                is_correct = True
                                break
                    print(f"📐 Геометрический ответ: '{user_answer}', правильный: {is_correct}")

            # СОЗДАЕМ ОБЪЕКТ StudentAnswer С ФОТО РЕШЕНИЯ
            student_answer = StudentAnswer(
                test=test,
                question=question,
                student_name=student_name,
                student_session=session_key,
                selected_answer=selected_answer,
                is_correct=is_correct,
                text_answer=text_answer,
                matching_data=matching_data,
                submitted_at=timezone.now()
            )

            # ДОБАВЛЯЕМ ФОТО РЕШЕНИЯ ЕСЛИ ОНО ЕСТЬ
            if solution_photo:
                student_answer.solution_image = solution_photo
                print(f"📸 Фото решения добавлено к вопросу {question.id}")

            student_answers.append(student_answer)

            if is_correct:
                correct += 1

        # МАССОВОЕ СОХРАНЕНИЕ ВСЕХ ОТВЕТОВ
        StudentAnswer.objects.bulk_create(student_answers)
        print(f"💾 Сохранено {len(student_answers)} ответов")

        # СОЗДАЕМ ОБЩИЙ РЕЗУЛЬТАТ ТЕСТА
        percentage = (correct / total * 100) if total > 0 else 0

        test_result = TestResult.objects.create(
            test=test,
            student_name=student_name,
            student_session=session_key,
            score=correct,
            total_questions=total,
            percentage=percentage,
            class_name=class_group,
            completed_at=timezone.now()
        )

        print(f"🎯 Создан TestResult ID: {test_result.id}")
        print(f"📊 Результат: {correct}/{total} ({percentage:.1f}%)")

        # ПЕРЕНАПРАВЛЯЕМ НА СТРАНИЦУ РЕЗУЛЬТАТА
        return redirect(reverse("quiz:show_result", args=[str(test_result.id)]))

    # GET запрос - показываем форму
    context = {
        "test": test,
        "questions": questions,
        "already_completed": already_completed,
        "existing_result": existing_result,
        "student_session": session_key,
    }
    return render(request, "quiz/take_math_test.html", context)


def _normalize_math_expression(expression):
    """Нормализация математического выражения для сравнения"""
    if not expression:
        return ""

    # Приводим к нижнему регистру
    normalized = expression.lower().strip()

    # Убираем лишние пробелы
    normalized = ' '.join(normalized.split())

    # Заменяем синонимы и разные написания
    replacements = {
        '×': '*',
        '÷': '/',
        '^': '**',
        'pi': 'π',
        'sqrt': '√',
        ' ': '',  # Убираем все пробелы
    }

    for old, new in replacements.items():
        normalized = normalized.replace(old, new)

    # Убираем лишние скобки и знаки равенства
    normalized = normalized.replace('=', '').strip()

    return normalized


def take_math_thanks(request, public_id):
    """Страница благодарности после математического теста"""
    test = get_object_or_404(Test, public_id=public_id)
    last_score = request.session.get("last_score", {"correct": 0, "total": 0})

    return render(request, "quiz/take_math_thanks.html", {
        "test": test,
        "correct": last_score["correct"],
        "total": last_score["total"],
        "percentage": (last_score["correct"] / last_score["total"] * 100) if last_score["total"] > 0 else 0
    })




@login_required
def student_results(request):
    """Результаты всех учеников для всех тестов текущего пользователя"""
    # Получаем все тесты текущего пользователя
    user_tests = Test.objects.filter(creator=request.user)

    # Получаем все результаты для этих тестов
    all_results = TestResult.objects.filter(test__in=user_tests)

    # Группируем по тестам, убирая дубликаты учеников
    test_results = {}
    for test in user_tests:
        # Получаем ВСЕ результаты теста
        test_all_results = all_results.filter(test=test)

        # Убираем дубликаты учеников - берем только последние результаты
        from django.db.models import Max

        # Находим ID последних результатов для каждого ученика в этом тесте
        latest_ids = test_all_results.values('student_session').annotate(
            latest_id=Max('id')
        ).values_list('latest_id', flat=True)

        # Получаем только последние результаты (без дубликатов учеников)
        unique_results = TestResult.objects.filter(id__in=latest_ids)

        test_results[test] = unique_results

    # Считаем общую статистику БЕЗ дубликатов учеников
    from django.db.models import Max

    # Находим ID последних результатов для каждого ученика во всех тестах
    all_latest_ids = all_results.values('student_session').annotate(
        latest_id=Max('id')
    ).values_list('latest_id', flat=True)

    # Получаем только последние результаты (уникальные ученики)
    unique_students_results = TestResult.objects.filter(id__in=all_latest_ids)

    context = {
        'test_results': test_results,
        'total_students': unique_students_results.count(),  # Уникальные ученики
        'total_attempts': all_results.count(),  # Все попытки
    }
    return render(request, 'quiz/student_results.html', context)


@login_required
def test_student_results(request, public_id):
    """Результаты учеников для конкретного теста"""
    test = get_object_or_404(Test, public_id=public_id, creator=request.user)

    # Получаем ВСЕ результаты
    all_results = TestResult.objects.filter(test=test)

    # Собираем уникальные классы из ВСЕХ результатов
    class_set = set()
    for result in all_results:
        if result.class_name and result.class_name.strip():
            class_set.add(result.class_name.strip())

    class_list = sorted(list(class_set))

    # Статистика по классам из ВСЕХ результатов
    class_stats = {}
    for class_name in class_list:
        class_results = all_results.filter(class_name=class_name)
        if class_results.exists():
            avg_score = class_results.aggregate(Avg('percentage'))['percentage__avg'] or 0
            # Уникальные ученики в этом классе
            students_count = class_results.values('student_session').distinct().count()

            class_stats[class_name] = {
                'count': class_results.count(),  # Все попытки в классе
                'avg_score': avg_score,
                'students': students_count,  # Уникальные ученики
            }

    # Статистика для результатов без класса
    no_class_results = all_results.filter(class_name__isnull=True) | all_results.filter(class_name__exact='')
    if no_class_results.exists():
        avg_score = no_class_results.aggregate(Avg('percentage'))['percentage__avg'] or 0
        students_count = no_class_results.values('student_session').distinct().count()

        class_stats['Без класса'] = {
            'count': no_class_results.count(),
            'avg_score': avg_score,
            'students': students_count,
        }

    # УБИРАЕМ ДУБЛИКАТЫ: получаем только последние результаты каждого ученика
    latest_results = []
    seen_students = set()

    # Сортируем по дате (сначала новые)
    sorted_results = all_results.order_by('-completed_at')

    for result in sorted_results:
        student_key = result.student_name or result.student_session
        if student_key not in seen_students:
            latest_results.append(result)
            seen_students.add(student_key)

    context = {
        'test': test,
        'results': latest_results,  # Только последние результаты без дубликатов
        'total_students': len(latest_results),  # Количество уникальных учеников
        'total_attempts': all_results.count(),  # Общее количество попыток
        'average_score': sum(r.percentage for r in latest_results) / len(latest_results) if latest_results else 0,
        'class_list': class_list,
        'class_stats': class_stats,
    }
    return render(request, 'quiz/test_student_results.html', context)
# views.py


def test_json(request, result_id):
        """Простой тестовый endpoint"""
        return JsonResponse({
            'success': True,
            'message': '✅ Тестовый JSON работает!',
            'result_id': result_id,
            'test_data': 'Это тестовые данные'
        })

@require_http_methods(["GET"])
@login_required
def student_result_details(request, result_id):
    try:
        print(f"🎯 ===== ПОИСК ВОПРОСОВ ДЛЯ РЕЗУЛЬТАТА {result_id} =====")

        # Находим результат
        test_result = TestResult.objects.get(id=result_id)
        print(f"✅ Результат найден: {test_result.student_name}")
        print(f"📊 Тест: {test_result.test.title} (ID: {test_result.test.id})")

        # Ищем через StudentAnswer
        student_answers = StudentAnswer.objects.filter(
            test=test_result.test,
            student_session=test_result.student_session
        ).select_related('question', 'selected_answer')

        print(f"🔍 Найдено StudentAnswer: {student_answers.count()}")

        questions_data = []

        for answer in student_answers:
            print(f"📝 Обрабатываем ответ на вопрос: {answer.question.text}")

            # Получаем правильный ответ
            correct_answer_obj = answer.question.answers.filter(is_correct=True).first()

            # СОЗДАЕМ ДАННЫЕ ВОПРОСА С МАТЕМАТИЧЕСКИМИ ВЫРАЖЕНИЯМИ
            question_data = {
                'question_text': answer.question.text,
                'question_math_expression': answer.question.math_expression,  # ФОРМУЛА ВОПРОСА
                'question_format': answer.question.question_format,
                'is_correct': answer.is_correct,
                'explanation': getattr(answer.question, 'explanation', ''),
            }

            # ДОБАВЛЯЕМ ПРАВИЛЬНЫЙ ОТВЕТ (ТЕКСТ И ФОРМУЛУ)
            if correct_answer_obj:
                question_data['correct_answer'] = correct_answer_obj.text
                question_data[
                    'correct_answer_math_expression'] = correct_answer_obj.math_expression  # ФОРМУЛА ПРАВИЛЬНОГО ОТВЕТА
            else:
                question_data['correct_answer'] = "Не найден"
                question_data['correct_answer_math_expression'] = None

            # ДОБАВЛЯЕМ ОТВЕТ УЧЕНИКА (ТЕКСТ И ФОРМУЛУ)
            if answer.selected_answer:
                question_data['student_answer'] = answer.selected_answer.text
                question_data[
                    'student_answer_math_expression'] = answer.selected_answer.math_expression  # ФОРМУЛА ОТВЕТА УЧЕНИКА
            elif answer.text_answer:
                question_data['student_answer'] = answer.text_answer
                question_data['student_answer_math_expression'] = None
            else:
                question_data['student_answer'] = "Не ответил"
                question_data['student_answer_math_expression'] = None

            # ВАЖНОЕ ИСПРАВЛЕНИЕ: ДОБАВЛЯЕМ ФОТО РЕШЕНИЯ УЧЕНИКА
            if answer.solution_image:
                question_data['student_solution_image'] = request.build_absolute_uri(answer.solution_image.url)
                print(f"📸 Фото решения ученика: {question_data['student_solution_image']}")
            else:
                question_data['student_solution_image'] = None
                print(f"📸 Фото решения ученика: не загружено")

            # ДЕБАГ ИНФОРМАЦИЯ О ФОРМУЛАХ
            print(f"🧮 Формула вопроса: '{answer.question.math_expression}'")
            if correct_answer_obj:
                print(f"✅ Формула правильного ответа: '{correct_answer_obj.math_expression}'")
            if answer.selected_answer:
                print(f"👤 Формула ответа ученика: '{answer.selected_answer.math_expression}'")

            # ДОБАВЛЯЕМ ИЗОБРАЖЕНИЯ ВОПРОСА
            if answer.question.image:
                question_data['question_image'] = request.build_absolute_uri(answer.question.image.url)
                print(f"🖼️ Изображение вопроса: {question_data['question_image']}")

            # ДОБАВЛЯЕМ ИЗОБРАЖЕНИЕ ОТВЕТА УЧЕНИКА
            if answer.selected_answer and answer.selected_answer.image:
                question_data['student_answer_image'] = request.build_absolute_uri(answer.selected_answer.image.url)
                print(f"🖼️ Изображение ответа ученика: {question_data['student_answer_image']}")

            # ДОБАВЛЯЕМ ИЗОБРАЖЕНИЕ ПРАВИЛЬНОГО ОТВЕТА
            if correct_answer_obj and correct_answer_obj.image:
                question_data['correct_answer_image'] = request.build_absolute_uri(correct_answer_obj.image.url)
                print(f"🖼️ Изображение правильного ответа: {question_data['correct_answer_image']}")

            # ДОБАВЛЯЕМ ДАННЫЕ СОПОСТАВЛЕНИЯ ДЛЯ MATCHING ВОПРОСОВ
            if answer.question.question_format == 'matching' and answer.matching_data:
                question_data['matching_data'] = answer.matching_data
                print(f"🔄 Данные сопоставления: {answer.matching_data}")

            questions_data.append(question_data)

        print(f"📋 Собрано вопросов: {len(questions_data)}")

        # Если вопросы не найдены, пробуем альтернативные способы
        if not questions_data:
            print("⚠️ Вопросы не найдены через StudentAnswer, пробуем другие способы...")

            # Ищем вопросы теста
            test_questions = test_result.test.questions.all()
            print(f"🔍 Вопросов в тесте: {test_questions.count()}")

            for question in test_questions:
                # Получаем правильный ответ для вопроса
                correct_answer_obj = question.answers.filter(is_correct=True).first()

                question_data = {
                    'question_text': question.text,
                    'question_math_expression': question.math_expression,  # ФОРМУЛА ВОПРОСА
                    'question_format': question.question_format,
                    'is_correct': False,
                    'explanation': 'Данные ответа не найдены',
                }

                # ДОБАВЛЯЕМ ПРАВИЛЬНЫЙ ОТВЕТ
                if correct_answer_obj:
                    question_data['correct_answer'] = correct_answer_obj.text
                    question_data['correct_answer_math_expression'] = correct_answer_obj.math_expression
                else:
                    question_data['correct_answer'] = "Не найден"
                    question_data['correct_answer_math_expression'] = None

                question_data['student_answer'] = "Не найден"
                question_data['student_answer_math_expression'] = None
                question_data['student_solution_image'] = None  # Для вопросов без ответов фото решения нет

                # ДОБАВЛЯЕМ ИЗОБРАЖЕНИЯ ДЛЯ ВОПРОСОВ ТЕСТА
                if question.image:
                    question_data['question_image'] = request.build_absolute_uri(question.image.url)

                # ДОБАВЛЯЕМ ИЗОБРАЖЕНИЕ ПРАВИЛЬНОГО ОТВЕТА
                if correct_answer_obj and correct_answer_obj.image:
                    question_data['correct_answer_image'] = request.build_absolute_uri(correct_answer_obj.image.url)

                questions_data.append(question_data)

        response_data = {
            'success': True,
            'student_name': test_result.student_name,
            'class_name': getattr(test_result, 'class_name', ''),
            'score': test_result.score,
            'total_questions': test_result.total_questions,
            'percentage': test_result.percentage,
            'time_taken': getattr(test_result, 'time_taken', 0),
            'completed_at': test_result.completed_at.strftime("%d.%m.%Y %H:%M"),
            'questions': questions_data
        }

        print(f"📤 Отправляем {len(questions_data)} вопросов")
        print(f"🧮 Всего формул вопросов: {sum(1 for q in questions_data if q.get('question_math_expression'))}")
        print(
            f"✅ Всего формул правильных ответов: {sum(1 for q in questions_data if q.get('correct_answer_math_expression'))}")
        print(
            f"👤 Всего формул ответов учеников: {sum(1 for q in questions_data if q.get('student_answer_math_expression'))}")
        print(f"📸 Всего фото решений: {sum(1 for q in questions_data if q.get('student_solution_image'))}")
        return JsonResponse(response_data)

    except TestResult.DoesNotExist:
        print(f"❌ Результат {result_id} не найден")
        return JsonResponse({
            'success': False,
            'error': 'Результат не найден'
        }, status=404)
    except Exception as e:
        print(f"💥 Ошибка: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Ошибка сервера: {str(e)}'
        }, status=500)
@login_required
def class_groups(request):
    classes = ClassGroup.objects.fillter(teacher=request.user)
    return render(request, 'quiz/class_groups.html', {'classes': classes})


@login_required
def class_group_detail(request, class_id):
    class_group = get_object_or_404(ClassGroup, id=class_id, teacher=request.user)
    students = class_group.students.all()
    results = TestResult.objects.filter(class_group=class_group)

    test_stats = {}
    for test in Test.objects.filter(creator=request.user):
        test_results = results.filter(test=test)
        if test_results.exists():
            test_stats[test] = {
                'avg_score': test_results.aggregate(Avg('percentage'))['percentage__avg'] or 0,
                'attempts': test_results.count(),
                'best_score': test_results.aggregate(Max('percentage'))['percentage__max'] or 0,

            }

    context = {
        'class_group': class_group,
        'students': students,
        'results': results,
        'test_stats': test_stats,
    }
    return render(request, 'quiz/class_group_detail.html', context)














