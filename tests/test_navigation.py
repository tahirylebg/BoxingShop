import datetime

import pytest
from django.urls import reverse

from content.models import Guide
from core.templatetags.shop import markup_toc, simple_markup


def test_toc_anchors_match_rendered_headings():
    body = "Intro.\n\n## Règle n° 1 : l'usage\nTexte.\n\n## **Cuir** ou microfibre ?\nTexte."
    toc = markup_toc(body)
    html = str(simple_markup(body))
    assert [title for _, title in toc] == ["Règle n° 1 : l'usage", "Cuir ou microfibre ?"]
    for anchor, _ in toc:
        assert f'id="{anchor}"' in html


def test_toc_escapes_nothing_unsafe():
    html = str(simple_markup('## <script>alert(1)</script>\nx'))
    assert "<script>" not in html


@pytest.mark.django_db
def test_search_suggest_requires_two_characters(client):
    response = client.get(reverse("catalog:search_suggest"), {"q": "g"})
    assert response.status_code == 200
    assert response.json() == {"results": []}


@pytest.mark.django_db
def test_search_suggest_is_get_only(client):
    assert client.post(reverse("catalog:search_suggest"), {"q": "gant"}).status_code == 405


@pytest.mark.django_db
def test_guide_list_filters_by_topic(client):
    today = datetime.date.today()
    Guide.objects.create(title="Gants A", slug="gants-a", excerpt="x", body="x", topic="gants", published_at=today)
    Guide.objects.create(title="Tibias B", slug="tibias-b", excerpt="x", body="x", topic="protections",
                         published_at=today - datetime.timedelta(days=1))
    page = client.get(reverse("content:guides"), {"sujet": "protections"}).content.decode()
    assert "Tibias B" in page and "Gants A" not in page
    # Thème inconnu : ignoré, tous les guides sont listés.
    page = client.get(reverse("content:guides"), {"sujet": "<b>x</b>"}).content.decode()
    assert "Tibias B" in page and "Gants A" in page


@pytest.mark.django_db
def test_guide_detail_links_previous_and_next(client):
    today = datetime.date.today()
    for i, slug in enumerate(["recent", "milieu", "ancien"]):
        Guide.objects.create(title=slug.title(), slug=slug, excerpt="x", body="## Partie\ntexte", published_at=today - datetime.timedelta(days=i))
    page = client.get(reverse("content:guide", args=["milieu"])).content.decode()
    assert 'rel="prev"' in page and "/guides/recent/" in page
    assert 'rel="next"' in page and "/guides/ancien/" in page
    assert 'href="#s-partie"' in page
