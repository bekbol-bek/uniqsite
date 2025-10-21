from django.contrib.auth.forms import User
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import UserRegisterForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm




def auth_view(request):
    """Объединенный view для входа и регистрации"""
    login_form = AuthenticationForm()
    register_form = UserRegisterForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'login':
            login_form = AuthenticationForm(data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect('quiz:profile')
            else:
                messages.error(request, 'Ошибка входа. Проверьте данные.')

        elif form_type == 'register':
            register_form = UserRegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                messages.success(request, f'Аккаунт создан! Добро пожаловать, {user.username}!')
                return redirect('quiz:profile')
            else:
                messages.error(request, 'Ошибка регистрации. Проверьте данные.')

    context = {
        'login_form': login_form,
        'register_form': register_form,
    }
    return render(request, 'account/auth.html', context)


def user_logout(request):
    logout(request)
    return redirect('quiz:main')
