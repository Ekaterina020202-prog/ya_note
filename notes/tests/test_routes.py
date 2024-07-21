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

        cls.urls_for_anonymous_access = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        cls.urls_for_author_access = (
            'notes:add',
            'notes:list',
            'notes:success',
        )
        cls.urls_for_author_only = (
            ('notes:detail', (cls.note.slug,)),
            ('notes:edit', (cls.note.slug,)),
            ('notes:delete', (cls.note.slug,)),
        )

    def test_pages_availability(self):
        """
        Проверяем доступность главной страницы анонимному пользователю
        и страниц регистрации, входа и выхода для всех пользователей.
        """
        for name in self.urls_for_anonymous_access:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_show_and_edit_and_delete(self):
        """
        Проверяем, что страницы отдельной заметки, удаления и редактирования
        заметки доступны только автору заметки.
        Если на эти страницы попытается зайти другой пользователь —
        вернётся ошибка 404.
        """
        users_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            for name, args in self.urls_for_author_only:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=args)
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)

    def test_availability_for_note_add_and_list(self):
        """
        Проверяем, что авторизованному пользователю
        доступна страница со списком заметок notes/,
        страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        for name in self.urls_for_author_access:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.author_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи, страницу добавления заметки,
        отдельной заметки, редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина.
        """
        login_url = reverse('users:login')
        urls = self.urls_for_author_only + [
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None),
        ]
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
