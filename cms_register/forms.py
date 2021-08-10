from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from django.utils.translation import gettext as _

from cms_register.models import Profile

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['country']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].widget.attrs.update(style='width: 100%;')
        self.fields['country'].label = _('Country')
        

class UserForm(UserCreationForm):
    username =  forms.CharField(label=_("username"), max_length=150, required=True, validators=[RegexValidator('^[A-Za-z0-9_-]+$')],
                                    widget=forms.TextInput(attrs={'autocomplete': 'username'})) 
    first_name = forms.CharField(label=_("first_name"), max_length=150, required=True, validators=[RegexValidator('^[a-zA-Z ]+$')]) 
    last_name = forms.CharField(label=_("last_name"), max_length=150, required=True, validators=[RegexValidator('^[a-zA-Z ]+$')]) 
    email = forms.EmailField(label=_("email"), max_length=254, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', )


class UserEditForm(UserForm):
    username =  forms.CharField(label=_("username"), disabled=True) 
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
        required=False,
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
        required=False,
    )

    def clean(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if (password1 or password2) and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return super().clean()
