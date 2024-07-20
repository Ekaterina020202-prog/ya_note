from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Сергей Есенин')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст', author=cls.author)
        cls.reader = User.objects.create(username='Анон')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

    # 1. Проверяем доступность главной страницы анонимному пользователю.
    # 5. Проверяем, что страницы регистрации пользователей,
    # входа в учётную запись и выхода из неё доступны всем пользователям.
    def test_pages_availability(self):
        urls = (
            ('notes:home'),
            ('users:login'),
            ('users:logout'),
            ('users:signup'),
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # 3. Проверяем, что страницы отдельной заметки,
    # удаления и редактирования заметки доступны только автору заметки.
    # Если на эти страницы попытается зайти
    # другой пользователь — вернётся ошибка 404.
    def test_availability_for_note_show_and_edit_and_delete(self):
        users_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)

    # 2. Проверяем, что авторизованному пользователю
    # доступна страница со списком заметок notes/,
    # страница успешного добавления заметки done/,
    # страница добавления новой заметки add/.
    def test_availability_for_note_add_and_list(self):
        urls = (
            ('notes:add'),
            ('notes:list'),
            ('notes:success'),
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.author_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    # 4. При попытке перейти на страницу списка заметок,
    # страницу успешного добавления записи,
    # страницу добавления заметки, отдельной заметки,
    # редактирования или удаления,
    # заметки анонимный пользователь перенаправляется на страницу логина.
    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
