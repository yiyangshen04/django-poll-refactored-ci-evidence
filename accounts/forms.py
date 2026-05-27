from django import forms
from django.contrib.auth import get_user_model

# ``get_user_model`` is resolved at import time, which keeps the form
# compatible with custom user models and makes the lookup point a single
# attribute that tests can patch (``accounts.forms.User.objects.filter``).
User = get_user_model()


class UserRegistrationForm(forms.Form):
    """
    Self-contained registration form.

    Validation (uniqueness, password match) used to live inline in
    ``accounts.views.create_user`` via three ``check1/2/3`` flags. Moving
    it into ``clean_*`` / ``clean`` and a small ``save()`` method makes:

    * the view trivial (only orchestrates is_valid -> save -> redirect),
    * the validation rules unit-testable without hitting the view layer,
      and easy to fake/mock the User lookup against.
    """

    username = forms.CharField(
        label="Username",
        max_length=100,
        min_length=5,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email",
        max_length=35,
        min_length=5,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password1 = forms.CharField(
        label="Password",
        max_length=50,
        min_length=5,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        max_length=50,
        min_length=5,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists!")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered!")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Password did not match!")
        return cleaned

    def save(self):
        """
        Create the user from cleaned data. Mirrors ModelForm.save() so the
        view can stay agnostic of the User model.
        """
        return User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password1"],
            email=self.cleaned_data["email"],
        )
