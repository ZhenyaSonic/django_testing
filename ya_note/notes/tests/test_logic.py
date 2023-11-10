from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.forms import WARNING
from notes.models import Note
from pytils.translit import slugify

User = get_user_model()

SLUG = 'slug'

EDIT_URL = reverse('notes:edit', args=(SLUG,))
ADD_URL = reverse('notes:add')
DELETE_URL = reverse('notes:delete', args=(SLUG,))
SUCCESS_URL = reverse('notes:success')


class TestNews(TestCase):
    TEST_SLUG = "Slug_text"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='testUser')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url = ADD_URL
        cls.form_data = {
            'title': 'Заголовок', 'text': 'Текст',
            'slug': cls.TEST_SLUG,
        }

    def test_user_can_create_note(self):
        self.client.force_login(self.user)
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, f'{self.url}#comments')
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_anonymous_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)
        note = Note.objects.get()
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_slug_unique(self):
        self.client.force_login(self.user)
        self.client.post(self.url, data=self.form_data)
        response = self.client.post(self.url, data=self.form_data)
        warn = self.form_data['slug'] + WARNING
        self.assertFormError(response, form='form', field='slug', errors=warn)

    def test_slug_repeat(self):
        note = Note.create_note(title="Заметка без slug",
                                content="Содержание без slug")
        expected_slug = slugify(note.title)
        self.assertEqual(note.slug, expected_slug)


class TestNotesEditDelete(TestCase):
    NOTE_TITLE = 'title'
    NEW_NOTE_TITLE = 'updated title'
    NOTE_TEXT = 'text'
    NEW_NOTE_TEXT = 'updated text'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель простой')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug='note-slug',
            author=cls.author,
        )
        cls.edit_note_url = reverse('notes:edit', args=[cls.note.slug])
        cls.delete_note_url = reverse('notes:delete', args=[cls.note.slug])
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT}

    def test_author_can_edit_note(self):
        self.author_client.post(self.edit_note_url, self.form_data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_other_user_cant_edit_note_of_another_user(self):
        res = self.reader_client.post(self.edit_note_url, self.form_data)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.filter(id=self.note.id).first()
        self.assertIsNotNone(note_from_db)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)

    def test_author_can_delete_note_(self):
        response = self.author_client.post(self.delete_note_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.post(self.delete_note_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
