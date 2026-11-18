import re

from django import forms


class CheckoutForm(forms.Form):
    email = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    first_name = forms.CharField(label="Prénom", max_length=80,
                                 widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    last_name = forms.CharField(label="Nom", max_length=80,
                                widget=forms.TextInput(attrs={"autocomplete": "family-name"}))
    line1 = forms.CharField(
        label="Adresse", max_length=200,
        widget=forms.TextInput(attrs={"autocomplete": "address-line1", "data-address-autocomplete": ""}),
        help_text="Commencez à taper : des suggestions d'adresses s'affichent.",
    )
    line2 = forms.CharField(label="Complément (bâtiment, étage…)", max_length=200, required=False,
                            widget=forms.TextInput(attrs={"autocomplete": "address-line2"}))
    postal_code = forms.CharField(label="Code postal", max_length=5,
                                  widget=forms.TextInput(attrs={"autocomplete": "postal-code", "inputmode": "numeric",
                                                                "data-address-postcode": ""}))
    city = forms.CharField(label="Ville", max_length=100,
                           widget=forms.TextInput(attrs={"autocomplete": "address-level2", "data-address-city": ""}))
    phone = forms.CharField(label="Téléphone (pour le transporteur)", max_length=30, required=False,
                            widget=forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}))
    save_address = forms.BooleanField(label="Enregistrer cette adresse dans mon carnet", required=False)
    accept_terms = forms.BooleanField(
        label="J'ai lu et j'accepte les conditions générales de vente", required=True,
        error_messages={"required": "Vous devez accepter les CGV pour commander."},
    )

    def clean_postal_code(self):
        value = self.cleaned_data["postal_code"].strip()
        if not re.fullmatch(r"\d{5}", value):
            raise forms.ValidationError("Code postal français à 5 chiffres (livraison en France métropolitaine).")
        if value.startswith(("97", "98")):
            raise forms.ValidationError("Les DOM-TOM ne sont pas encore desservis.")
        return value


class TrackOrderForm(forms.Form):
    number = forms.CharField(label="N° de commande", max_length=20,
                             widget=forms.TextInput(attrs={"placeholder": "BS-2611-A1B2C3"}))
    email = forms.EmailField(label="E-mail utilisé pour la commande")
