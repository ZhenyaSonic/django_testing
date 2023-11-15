import pytest
from django.urls import reverse
from django.conf import settings
from news.forms import CommentForm
from http import HTTPStatus

pytestmark = pytest.mark.django_db


def test_news_count(
    client,
    news_list
):
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    news_count = len(response.context['object_list'])
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(client):
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    object_list = list(response.context['object_list'])
    sorted_list = sorted(object_list, key=lambda news: news.date, reverse=True)
    assert object_list == sorted_list


def test_comments_order(
    news,
    client
):
    url = reverse('news:detail', args=[news.pk])
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'news' in response.context
    news = response.context['news']
    all_comments = list(news.comment_set.all())

    sorted_comments = sorted(all_comments, key=lambda comment: comment.created)
    assert all_comments == sorted_comments


def test_anonymous_client_has_no_form(
    client,
    news
):
    response = client.get(reverse('news:detail', args=(news.id,)))
    assert response.status_code == HTTPStatus.OK
    assert 'form' not in response.context


def test_authorized_client_has_form(
    client,
    news,
    author_client
):
    response = author_client.get(reverse('news:detail', args=(news.id,)))
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
