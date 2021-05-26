from django.forms import ModelForm

from cms_register.models import Profile


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['country']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].widget.attrs.update(style='width: 100%;')
