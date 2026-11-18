def cart(request):
    """Nombre d'articles du panier, mémorisé en session pour éviter une requête SQL par page."""
    return {"cart_count": request.session.get("cart_count", 0) if hasattr(request, "session") else 0}
