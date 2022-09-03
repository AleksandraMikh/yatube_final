from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.forms import CharField


User = get_user_model()


class CreationForm(UserCreationForm):
    first_name = CharField(max_length=150, required=True, label="Имя")
    last_name = CharField(max_length=150, required=True, label="Фамилия")

    class Meta(UserCreationForm.Meta):
        # укажем модель, с которой связана создаваемая форма
        model = User
        # укажем, какие поля должны быть видны в форме и в каком порядке
        fields = ('first_name', 'last_name', 'username', 'email')
