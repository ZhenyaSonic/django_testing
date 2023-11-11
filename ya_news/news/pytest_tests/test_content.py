import pytest
from django.urls import reverse
from django.conf import settings
from news.forms import CommentForm
pytestmark = pytest.mark.django_db


def test_news_count(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    news_count = len(response.context['object_list'])
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(client):
    url = reverse('news:home')
    response = client.get(url)
    objects_list = response.context['object_list']
    sorted_list = sorted(objects_list,
                         key=lambda news:
                         news.date,
                         reverse=True)
    for i in range(len(objects_list)):
        assert objects_list[i].date == sorted_list[i].date


def test_comments_order(news, client):
    url = reverse('news:detail', args=[news.pk])
    response = client.get(url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()

    all_dates = [comment.created for comment in all_comments]
    sorted_dates = sorted(all_dates, key=lambda x: x)
    assert all_dates == sorted_dates


def test_anonymous_client_has_no_form(client, news):
    response = client.get(reverse('news:detail', args=(news.id,)))
    assert 'form' not in response.context


def test_authorized_client_has_form(client, news, author_client):
    response = author_client.get(reverse('news:detail', args=(news.id,)))
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
