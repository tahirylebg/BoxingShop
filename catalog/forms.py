from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label="Note", coerce=int, choices=[(i, f"{i} / 5") for i in range(5, 0, -1)], widget=forms.RadioSelect
    )

    class Meta:
        model = Review
        fields = ["rating", "title", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4, "maxlength": 2000})}
