from django import forms
from .models import Cliente, Cancion, Resenya, ImagenCliente
import re
# Formulario para el registro de clientes


class ClienteForm(forms.ModelForm):

    # Campos del formulario de registro de clientes
    login = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Ingresa tu correo'}
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Repite tu contraseña'}))
    nombre = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Nombre'}
    ))
    apellido = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Apellido'}
    ))
    fecha_nac = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control datepicker', 'placeholder': 'YYYY-MM-DD'}
    ))
    genero = forms.ChoiceField(choices=[('Masculino', 'Masculino'), ('Femenino', 'Femenino'), ('Otro', 'Otro')],
                               widget=forms.Select(attrs={'class': 'form-control'}))

    # Meta: Define el modelo y los campos a utilizar en el formulario de registro de clientes
    class Meta:
        model = Cliente
        fields = ['login', 'password', 'nombre',
                  'apellido', 'fecha_nac', 'cuenta_vigente', 'genero']

    # Validar nombre y apellido solo con letras
    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]+$", nombre):
            raise forms.ValidationError(
                'El nombre solo puede contener letras y espacios')
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data['apellido']
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]+$", apellido):
            raise forms.ValidationError(
                'El apellido solo puede contener letras y espacios')
        return apellido

    # Validar email único
    def clean_login(self):
        login = self.cleaned_data['login']
        if Cliente.objects.filter(login=login).exists():
            raise forms.ValidationError('Correo ya registrado')
        return login

    # validar contraseña repetida
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        # Validar que la contraseña tenga al menos 8 caracteres
        if len(password) < 8:
            self.add_error(
                'password', 'La contraseña debe tener al menos 8 caracteres')

        # Validar que las contraseñas coincidan
        if password != password2:
            self.add_error('password2', 'Las contraseñas no coinciden')
        return cleaned_data

    # Encripta la contraseña
    def save(self, commit=True):
        cliente = super().save(commit=False)
        cliente.set_password(self.cleaned_data['password'])
        cliente.cuenta_vigente = True
        if commit:
            cliente.save()
        return cliente


# Formulario para la creación de resenya
class ResenyaForm(forms.ModelForm):
    # Define el campo 'resenya' con un widget personalizado aquí si es necesario
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


# Formulario para la creación de canciones


class CancionForm(forms.ModelForm):
    # Campos del formulario de registro de canciones
    nombre = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Nombre de la canción'}
    ))

    # Meta: Define el modelo y los campos a utilizar en el formulario de registro de canciones
    class Meta:
        model = Cancion
        fields = ['nombre']

    # Validar nombre de canción único
    """ def clean_nombre(self):
        # Deberías usar self.cleaned_data
        nombre = self.cleaned_data.get('nombre')
        if Cancion.objects.filter(nombre=nombre).exists():
            self.add_error('nombre', 'Canción ya registrada')
        return nombre """

    # Validar que el campo no esté vacío o solo contenga espacios
    def clean_nombre(self):

        nombre = self.cleaned_data.get('nombre', '').strip()
        # Validar que el campo no esté vacío o solo contenga espacios
        if not nombre:
            raise forms.ValidationError("Este campo es requerido.")
        return nombre

# Formulario para el inicio de sesión


class LoginForm(forms.ModelForm):
    login = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Ingresa tu correo'}
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Ingresa tu contraseña'}))

    class Meta:
        model = Cliente
        fields = ['login', 'password']

    def clean(self):
        cleaned_data = super().clean()
        login = cleaned_data.get('login')
        password = cleaned_data.get('password')

        try:
            cliente = Cliente.objects.get(login=login)
            if not cliente.check_password(password):
                self.add_error('password', 'Contraseña incorrecta')
            if not cliente.cuenta_vigente:
                self.add_error(
                    None, 'Cuenta no está vigente. Por favor, contacte con el soporte.')
        except Cliente.DoesNotExist:
            self.add_error('login', 'Usuario no registrado')

        return cleaned_data

        """  if not Cliente.objects.filter(login=login).exists():
            self.add_error('login', 'Usuario no registrado')
        else:
            cliente = Cliente.objects.get(login=login)
            if not cliente.check_password(password):
                self.add_error('password', 'Contraseña incorrecta')
        return cleaned_data """


class ImagenClienteForm(forms.ModelForm):
    imagen = forms.ImageField(widget=forms.FileInput(
        attrs={'class': 'form-control'}
    ))

    class Meta:
        model = ImagenCliente
        fields = ['imagen']

# Buscar canción en Spotify


class BuscarCancionForm(forms.Form):
    nombre = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control',
               'placeholder': 'Buscar canción en Spotify'}
    ))
