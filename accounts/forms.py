from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from .models import Address, Customer


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={"autocomplete": "email",
                                                                               "autofocus": True}))
    password = forms.CharField(label="Mot de passe", strip=False,
                               widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
                                help_text="10 caractères minimum, pas uniquement des chiffres.")
    password2 = forms.CharField(label="Confirmation du mot de passe", strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    accept_privacy = forms.BooleanField(
        label="J'accepte la politique de confidentialité", required=True,
        error_messages={"required": "Merci d'accepter la politique de confidentialité."},
    )

    class Meta:
        model = Customer
        fields = ["email", "first_name", "last_name"]
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Customer.objects.filter(email__iexact=email).exists():
            # Message neutre : ne révèle pas si un compte existe (énumération d'e-mails)
            raise forms.ValidationError("Impossible de créer un compte avec cette adresse. Essayez de vous connecter.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        if p1:
            user = Customer(email=cleaned.get("email", ""), first_name=cleaned.get("first_name", ""),
                            last_name=cleaned.get("last_name", ""))
            try:
                password_validation.validate_password(p1, user)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "phone"]


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["label", "first_name", "last_name", "line1", "line2", "postal_code", "city", "phone", "is_default"]
        widgets = {
            "line1": forms.TextInput(attrs={"autocomplete": "address-line1", "data-address-autocomplete": ""}),
            "postal_code": forms.TextInput(attrs={"inputmode": "numeric", "data-address-postcode": ""}),
            "city": forms.TextInput(attrs={"data-address-city": ""}),
        }


class ClubRequestForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["club_name", "club_siret", "club_message"]
        labels = {"club_message": "Présentez votre structure (discipline, nombre d'adhérents, besoins)"}
        widgets = {"club_message": forms.Textarea(attrs={"rows": 4, "maxlength": 1500})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["club_name"].required = True
        self.fields["club_siret"].required = True


class DeleteAccountForm(forms.Form):
    password = forms.CharField(label="Confirmez avec votre mot de passe", strip=False,
                               widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        if not self.user.check_password(self.cleaned_data["password"]):
            raise forms.ValidationError("Mot de passe incorrect.")
        return self.cleaned_data["password"]
