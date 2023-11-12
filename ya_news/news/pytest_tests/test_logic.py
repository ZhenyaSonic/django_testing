from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse
from django.test import Client
from news.forms import BAD_WORDS, WARNING
from news.models import Comment

pytestmark = pytest.mark.django_db


def test_anonymous_cant_create_comment(client, news, form_data):
    url = reverse('news:detail', args=(news.id,))
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


def test_user_can_create_comment(admin_client, admin_user, form_data, news):
    url = reverse('news:detail', args=(news.id,))
    response = admin_client.post(url, data=form_data)
    expected_url = url + '#comments'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 1
    new_comment = Comment.objects.get()
    assert new_comment.text == form_data['text']
    assert new_comment.news == news
    assert new_comment.author == admin_user


def test_user_cant_use_bad_words(author_client, news):
    bad_words_data = {'text': f'Какой-то text, {(BAD_WORDS)}, еще text'}
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    assert Comment.objects.count() == 0


def test_author_can_edit_comment(
        author_client, news, comment, form_data):
    url = reverse('news:edit', args=[comment.pk])
    response = author_client.post(url, data=form_data)
    expected_url = reverse('news:detail', args=(news.id,)) + '#comments'
    assertRedirects(response, expected_url)
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_author_can_delete_comment(
        author_client, news, comment, form_data):
    url = reverse('news:delete', args=[comment.pk])
    response = author_client.delete(url, data=form_data)
    expected_url = reverse('news:detail', args=(news.id,)) + '#comments'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


def test_other_user_cant_edit_comment(
        admin_client, comment, form_data):
    url = reverse('news:edit', args=[comment.pk])
    old_comment = comment.text
    response = admin_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == old_comment


def test_other_user_cant_delete_comment(
        admin_client, comment):
    url = reverse('news:delete', args=[comment.pk])
    expected_count = Comment.objects.count()
    response = admin_client.post(url)
    comments_count = Comment.objects.count()
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert comments_count == expected_count


def test_anonymous_cannot_edit_comment(
        comment, form_data):
    url = reverse('news:edit', args=[comment.pk])
    old_comment = comment.text

    client = Client()
    response = client.post(url, data=form_data)

    assert response.status_code == HTTPStatus.FOUND
    comment.refresh_from_db()
    assert comment.text == old_comment


def test_anonymous_cannot_delete_comment(
        comment):
    url = reverse('news:delete', args=[comment.pk])
    expected_count = Comment.objects.count()

    client = Client()
    response = client.post(url)

    comments_count = Comment.objects.count()
    assert response.status_code == HTTPStatus.FOUND
    assert comments_count == expected_count
