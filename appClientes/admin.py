from django.contrib import admin
from django import forms
import bcrypt
from .models import Cliente, Cancion, ListaCancion, Resenya

# Register your models here.


class ClienteAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    genero = forms.ChoiceField(choices=[('Masculino', 'Masculino'), ('Femenino', 'Femenino'), ('Otro', 'Otro')],
                               widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Cliente
        fields = '__all__'

    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Si la contraseña no empieza con '$2b$', significa que no está hasheada
        if password and not password.startswith('$2b$'):
            password = bcrypt.hashpw(password.encode(
                'utf-8'), bcrypt.gensalt()).decode('utf-8')
        return password


class ResenyaAdminForm(forms.ModelForm):
    resenya = forms.CharField(label="Reseña", widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder': 'Escribe tu reseña'}
    ))

    class Meta:
        model = Resenya
        fields = ['puntuacion', 'resenya']
        widgets = {
            'puntuacion': forms.Select(attrs={'class': 'form-control'}, choices=[
                (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')
            ])
        }


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    form = ClienteAdminForm
    list_display = ('id_cliente', 'nombre', 'apellido', 'login',
                    'fecha_nac', 'cuenta_vigente')
    list_filter = ('cuenta_vigente',)
    search_fields = ('nombre', 'apellido', 'login')
    ordering = ('nombre', 'apellido')


@admin.register(Cancion)
class CancionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(ListaCancion)
class ListaCancionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'cancion')
    search_fields = ('cliente', 'cancion')
    ordering = ('cliente', 'cancion')


@admin.register(Resenya)
class ResenyaAdmin(admin.ModelAdmin):
    form = ResenyaAdminForm
    list_display = ('puntuacion', 'resenya', 'cliente')
    search_fields = ('puntuacion', 'resenya', 'cliente')
    ordering = ('puntuacion', 'resenya', 'cliente')

# crear superusuario
# python manage.py createsuperuser
