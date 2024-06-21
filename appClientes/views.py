from .forms import CancionForm
from django.shortcuts import render, redirect, get_object_or_404
from .decorators import cliente_login_required
from .models import Cliente, Cancion, ListaCancion, Resenya, ImagenCliente
from django.contrib import messages
from .forms import ClienteForm, LoginForm, CancionForm, ResenyaForm, ImagenClienteForm, BuscarCancionForm
from django.core.paginator import Paginator
import cv2
import os
from django_ratelimit.decorators import ratelimit
from django.utils.timezone import now


# importar spotify para
# obtener las canciones de la api para agregar a la lista de canciones del cliente
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

# Reemplaza con tu Client ID de Spotify
SPOTIPY_CLIENT_ID = "fbf2eaabfd1947f698f3e8e75b32b53b"
# Reemplaza con tu Client Secret de Spotify
SPOTIPY_CLIENT_SECRET = "8e45d169e24547c7b88f8fc0c4e3284c"

sp = Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
))

# Create your views here.


@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
def registrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado con exito')
            return redirect('login',)

    else:
        form = ClienteForm()
    return render(request, 'registrar_cliente.html', {'form': form})


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
def agregar_cancion(request):
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.get(id_cliente=cliente_id)

    form = CancionForm()
    buscar_form = BuscarCancionForm()
    sugerencias = []

    if request.method == 'POST':
        if 'buscar' in request.POST:
            buscar_form = BuscarCancionForm(request.POST)
            if buscar_form.is_valid():
                query = buscar_form.cleaned_data['nombre']
                results = sp.search(q=query, type='track', limit=5)
                tracks = results.get('tracks', {}).get('items', [])

                for track in tracks:
                    artist_id = track['artists'][0]['id']
                    artist_info = sp.artist(artist_id)
                    genres = artist_info.get('genres', [])
                    # Usar el primer género de la lista si existe
                    genre = genres[0] if genres else 'Desconocido'
                    sugerencias.append({
                        'image': track['album']['images'][0]['url'] if track['album']['images'] else 'https://via.placeholder.com/150',
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'uri': track['uri'],
                        'genre': genre if genre else 'Desconocido'
                    })

        elif 'agregar' in request.POST:

            # obtener el nombre de la canción y el artista
            nombre_cancion = request.POST.get('nombre', '').strip()
            artista = request.POST.get('artista', '').strip()

            nombre_completo = f"{nombre_cancion} - {artista}".lower()

            form = CancionForm({'nombre': nombre_completo})
            if form.is_valid():
                cancion, created = Cancion.objects.get_or_create(
                    nombre=nombre_completo)

                if ListaCancion.objects.filter(cliente=cliente).count() >= 10:
                    messages.error(
                        request, "No puedes agregar más de 10 canciones.")
                elif ListaCancion.objects.filter(cliente=cliente, cancion=cancion).exists():
                    messages.error(
                        request, "Ya tienes esta canción en tu lista.")
                else:
                    ListaCancion.objects.create(
                        cliente=cliente, cancion=cancion)
                    messages.success(
                        request, "Canción agregada exitosamente a tu lista.")
                    return redirect('home')

    return render(request, 'agregar_canciones.html', {
        'form': form,
        'buscar_form': buscar_form,
        'sugerencias': sugerencias,
        'cliente': cliente
    })


@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
def login(request):
    # Login de cliente
    # Paginación de resenya en la página de inicio de sesión
    resenya = Resenya.objects.all()
    paginator = Paginator(resenya, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            login = form.cleaned_data['login']
            password = form.cleaned_data['password']
            try:
                cliente = Cliente.objects.get(login=login)
                if cliente.check_password(password):
                    request.session['cliente_id'] = cliente.id_cliente
                    return redirect('home')
                else:
                    form.add_error(None, 'Correo o contraseña incorrectos')
            except Cliente.DoesNotExist:
                form.add_error(None, 'Login o contraseña incorrectos')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'resenya': resenya, 'page_obj': page_obj})


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
# Página de inicio
def home(request):
    cliente_id = request.session.get('cliente_id')
    if not cliente_id:
        return redirect('login')

    cliente = Cliente.objects.get(id_cliente=cliente_id)
    canciones = ListaCancion.objects.filter(cliente=cliente)

    # Construir la URL de la imagen del rostro
    face_filename = f"{cliente_id}.jpg"
    face_path = os.path.join('faces', face_filename)
    face_url = None

    # Verificar si el archivo existe en la carpeta 'faces'
    if os.path.exists(face_path):
        timestamp = now().timestamp()
        face_url = f"/faces/{face_filename}?{timestamp}"

    return render(request, 'home.html', {'cliente': cliente, 'canciones': canciones, 'face_url': face_url})


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
# Tus reseñas
def resenya_cliente(request):
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.get(id_cliente=cliente_id)
    resenya = Resenya.objects.filter(cliente=cliente)
    return render(request, 'resenya_cliente.html', {'cliente': cliente, 'resenya': resenya})


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
# eliminar resenya del cliente
def eliminar_resenya(request, resenya_id):
    if request.method == 'POST':
        resenya = Resenya.objects.get(id=resenya_id)
        resenya.delete()
        messages.success(request, "Reseña eliminada exitosamente.")
    return redirect('resenyas')


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
# editar resenya del cliente
def editar_resenya(request, resenya_id):

    resenya = get_object_or_404(Resenya, pk=resenya_id)
    form = ResenyaForm(request.POST or None, instance=resenya)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Reseña editada con exito')
        return redirect('resenyas')
    else:
        form = ResenyaForm(instance=resenya)
    return render(request, 'editar_resenya.html', {'form': form, 'resenya': resenya})


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
# agregar resenya del cliente
def agregar_resenya(request):
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.get(id_cliente=cliente_id)

    # Validar si el cliente ya tiene una reseña
    if Resenya.objects.filter(cliente=cliente).exists():
        messages.error(request, "Ya tienes una reseña registrada.")
        return redirect('resenyas')

    if request.method == 'POST':
        form = ResenyaForm(request.POST)
        if form.is_valid():
            resenya = form.save(commit=False)
            resenya.cliente = cliente
            resenya.save()
            messages.success(request, 'Reseña agregada con exito')
            return redirect('resenyas')
    else:
        form = ResenyaForm()
    return render(request, 'agregar_resenya.html', {'form': form, 'cliente': cliente})


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
# Eliminar canción de la lista
def eliminar_cancion(request, lista_id):
    if request.method == 'POST':
        lista = ListaCancion.objects.get(
            id=lista_id, cliente=request.session.get('cliente_id'))
        lista.delete()
        messages.success(request, "Canción eliminada exitosamente.")
    return redirect('home')


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
def eliminar_cancion(request, lista_id):
    if request.method == 'POST':
        cliente_id = request.session.get('cliente_id')
        # Usa get_object_or_404 para manejar no encontrados
        lista = get_object_or_404(
            ListaCancion, id=lista_id, cliente=cliente_id)
        lista.delete()
        messages.success(request, "Canción eliminada exitosamente.")
    return redirect('home')


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
def logout(request):
    request.session.flush()
    return redirect('login')

#


@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
def extraer_rostro(request):
    if request.method == 'POST':
        form = ImagenClienteForm(request.POST, request.FILES)
        if form.is_valid():
            cliente_id = request.session.get('cliente_id')
            cliente = Cliente.objects.get(id_cliente=cliente_id)

            # Guardar la imagen subida temporalmente
            imagen_cliente = form.save(commit=False)
            imagen_cliente.cliente = cliente
            imagen_cliente.save()

            # Procesar la imagen
            image_path = imagen_cliente.imagen.path
            face_output_path = 'faces'

            if not os.path.exists(face_output_path):
                os.makedirs(face_output_path)

            # Cargar la imagen
            image = cv2.imread(image_path)
            if image is None:
                messages.error(request, 'Error al leer la imagen.')
                return redirect('subir_imagen')

            # Detectar rostros en la imagen
            face_classifier = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = face_classifier.detectMultiScale(image, 1.1, 5)

            if len(faces) == 0:
                messages.error(
                    request, 'No se detectaron rostros en la imagen.')
            elif len(faces) > 1:
                messages.error(
                    request, 'Se detectaron múltiples rostros en la imagen.')
            else:
                for (x, y, w, h) in faces:
                    face = image[y:y + h, x:x + w]
                    face = cv2.resize(face, (150, 150))

                    # Guardar la imagen del rostro con el ID del cliente
                    face_filename = os.path.join(
                        face_output_path, f"{cliente_id}.jpg")
                    cv2.imwrite(face_filename, face)
                    messages.success(
                        request, f'Rostro guardado')

            # Eliminar la imagen original una vez procesada
            os.remove(image_path)

            return redirect('home')
        else:
            messages.error(request, 'Error al procesar el formulario.')
    else:
        form = ImagenClienteForm()
    return render(request, 'subir_imagen.html', {'form': form})

# Eliminar la imagen del rostro del cliente


@ cliente_login_required
@ratelimit(key='ip', rate='40/m', method=ratelimit.ALL, block=True)
def eliminar_rostro(request):
    cliente_id = request.session.get('cliente_id')
    face_filename = os.path.join('faces', f"{cliente_id}.jpg")

    # Verificar si el archivo existe
    if os.path.exists(face_filename):
        os.remove(face_filename)
        messages.success(request, "Imagen del rostro eliminada exitosamente.")
    else:
        messages.error(
            request, "No se encontró ninguna imagen del rostro para eliminar.")

    return redirect('home')

# Eliminar cuenta del cliente y todas sus canciones y reseñas asociadas a él y
# su imagen del rostro si existe en la carpeta 'faces' del proyecto Django


@cliente_login_required
def eliminar_cuenta(request):
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.get(id_cliente=cliente_id)
    face_filename = os.path.join('faces', f"{cliente_id}.jpg")

    if os.path.exists(face_filename):
        os.remove(face_filename)

    cliente.delete()
    request.session.flush()
    messages.success(request, "Cuenta eliminada exitosamente.")
    return redirect('login')
