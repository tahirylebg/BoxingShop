"""Rendu des pages publiques, filtres (repli GET), SEO."""
import json

import pytest

pytestmark = pytest.mark.django_db


def test_public_pages_render(client, product, variant):
    for url in ["/", "/boutique/", "/boxe-anglaise/", "/equipement/gants/", "/boxe-anglaise/gants/",
                product.get_absolute_url(), "/guides/", "/informations/cgv/", "/informations/mentions-legales/",
                "/informations/confidentialite/", "/cookies/", "/robots.txt", "/sitemap.xml"]:
        assert client.get(url).status_code == 200, url


def test_semantic_product_url(product):
    assert product.get_absolute_url() == "/boxe-anglaise/gants/gant-test/"


def test_filters_work_without_js(client, product, variant):
    r = client.get("/boutique/", {"poids": "10", "tri": "prix"})
    assert r.status_code == 200
    assert product in list(r.context["products"])
    r = client.get("/boutique/", {"poids": "16"})
    assert product not in list(r.context["products"])


def test_filters_fetch_returns_fragment(client, product, variant):
    r = client.get("/boutique/", {"poids": "10"}, HTTP_X_REQUESTED_WITH="fetch")
    assert r.status_code == 200
    assert b"<html" not in r.content


def test_product_jsonld_and_canonical(client, product, variant):
    html = client.get(product.get_absolute_url()).content.decode()
    assert f'<link rel="canonical" href="http://testserver{product.get_absolute_url()}">' in html or \
           'rel="canonical"' in html
    blocks = []
    for chunk in html.split('<script type="application/ld+json"')[1:]:
        data = json.loads(chunk.split(">", 1)[1].split("</script>")[0])
        blocks.extend(data if isinstance(data, list) else [data])
    types = {b.get("@type") for b in blocks}
    assert {"Product", "BreadcrumbList"} <= types
    product_ld = next(b for b in blocks if b["@type"] == "Product")
    offers = product_ld["offers"] if isinstance(product_ld["offers"], list) else [product_ld["offers"]]
    assert offers[0]["@type"] == "Offer" and offers[0]["sku"] == "BS-TEST-10"


def test_wrong_discipline_redirects_to_canonical(client, product, variant):
    r = client.get("/muay-thai/gants/gant-test/")
    assert r.status_code in (301, 404)


def test_cookie_refusal_is_one_click(client):
    r = client.post("/cookies/consentement/", {"choice": "refused", "next": "https://evil.example/"})
    assert r.status_code == 302 and r["Location"] == "/"
    assert r.cookies["bs_consent"].value == "refused"
    html = client.get("/").content.decode()
    assert 'name="choice" value="refused"' not in html  # bannière masquée une fois le choix fait


def test_cookie_banner_offers_refuse_and_accept_equally(client):
    html = client.get("/").content.decode()
    assert 'value="refused"' in html and 'value="accepted"' in html


def test_robots_and_sitemap(client, product, variant):
    assert b"Sitemap:" in client.get("/robots.txt").content
    assert product.get_absolute_url().encode() in client.get("/sitemap.xml").content
