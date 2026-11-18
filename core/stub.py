from django.http import HttpResponse


def coming_soon(request, *args, **kwargs):  # remplacé au fil des lots
    return HttpResponse("Bientôt disponible", status=501)
