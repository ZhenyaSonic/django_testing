from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class SetUpTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )


class TestNoteList(SetUpTestCase):
    def test_list_context(self):
        user_notes = (
            (self.author, True),
            (self.reader, False),
        )
        url = reverse('notes:list')
        for user, value in user_notes:
            with self.subTest(user=user.username, value=value):
                response = self.client.get(url)
                note_objects_list = self.note in response.context[
                    'object_list']
                self.assertEqual(note_objects_list, value)

    def test_pages_contains_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for page, args in urls:
            with self.subTest(page=page):
                url = reverse(page, args=args)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertIn('form', response.context)
