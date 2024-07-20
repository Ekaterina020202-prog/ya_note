from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()
URL_TO_DONE = reverse('notes:success')
URL_TO_ADD = reverse('notes:add')


class TestNoteCreation(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Текст заголовка'
    NOTE_SLUG = 'slug'

    @classmethod
    def setUpTestData(cls):
        cls.notes_counts = Note.objects.count()
        cls.user = User.objects.create(username='Фёдор Достоевский')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.NOTE_TEXT, 'title': cls.NOTE_TITLE,
                         'slug': cls.NOTE_SLUG, 'author': cls.auth_client}

    def test_user_can_create_note(self):
        response = self.auth_client.post(URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response, URL_TO_DONE)
        note_count = Note.objects.count()
        self.assertEqual(note_count, self.notes_counts + 1)
        note = Note.objects.last()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.user)

    def test_anonymous_user_cant_create_note(self):
        self.client.post(URL_TO_ADD, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, self.notes_counts)

    def test_empty_slug(self):
        self.form_data.pop('slug')
        response = self.auth_client.post(URL_TO_ADD, data=self.form_data)
        self.assertRedirects(response, URL_TO_DONE)
        self.assertEqual(Note.objects.count(), self.notes_counts + 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    NOTE_TITLE = 'Текст заголовка'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'slug'
    NEW_NOTE_TEXT = 'Обновлённая заметка'
    NEW_NOTE_TITLE = 'Обновлённый заголовок заметки'
    NEW_NOTE_SLUG = 'new_slug'

    @classmethod
    def setUpTestData(cls):
        cls.notes_counts = Note.objects.count()
        cls.author = User.objects.create(username='Автор заметки')
        cls.note = Note.objects.create(
            title='Заголовок',
            slug='Slug',
            author=cls.author,
            text=cls.NOTE_TEXT
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {'text': cls.NEW_NOTE_TEXT,
                         'title': cls.NEW_NOTE_TITLE,
                         'slug': cls.NEW_NOTE_SLUG}

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, URL_TO_DONE)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, URL_TO_DONE)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, self.notes_counts)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, self.notes_counts + 1)

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(URL_TO_ADD,
                                           data=self.form_data)
        self.assertFormError(response, 'form', 'slug',
                             errors=(self.note.slug + WARNING))
        self.assertEqual(Note.objects.count(), self.notes_counts + 1)
