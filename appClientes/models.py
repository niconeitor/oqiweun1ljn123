import bcrypt
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, DecimalValidator

# Create your models here.


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    login = models.CharField(max_length=64)
    password = models.CharField(max_length=90)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    fecha_nac = models.DateField()
    genero = models.CharField(max_length=10)
    cuenta_vigente = models.BooleanField()

    class Meta:
        db_table = 'cliente'

    # Encripta la contraseña
    def set_password(self, password):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.password = hashed.decode('utf-8')

    # Verifica si la contraseña ingresada es correcta
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    # Retorna el nombre completo del cliente
    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Cancion(models.Model):
    id_cancion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)

    class Meta:
        db_table = 'cancion'

    def __str__(self):
        return f"{self.nombre}"


class ListaCancion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cancion = models.ForeignKey(Cancion, on_delete=models.CASCADE)

    # Un cliente no puede tener la misma canción en su lista de canciones
    class Meta:
        unique_together = ('cliente', 'cancion'),
        db_table = 'lista_cancion'

    def __str__(self):
        return f"{self.cliente} - {self.cancion}"

# Modelo para resenyas


class Resenya(models.Model):
    puntuacion = models.DecimalField(
        max_digits=2, decimal_places=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)], help_text='Puntuación entre 1 y 5')
    resenya = models.TextField(max_length=1000)
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    class Meta:
        db_table = 'resenya'
        # cliente solo puede agregar una reseña
        unique_together = ('cliente', 'resenya')

    def __str__(self):
        return f'Cliente {self.cliente} - Reseña {self.resenya}'


# Modelo Imagen Cliente para almacenar las imágenes de los clientes en una carpeta
class ImagenCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='temp_images/')

    class Meta:
        db_table = 'imagen_cliente'

    def __str__(self):
        return f'Cliente {self.cliente} - Imagen {self.imagen}'
