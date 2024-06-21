def agregar_cancion(request):
    cliente_id = request.session.get('cliente_id')
    # Obtenemos el cliente logueado
    cliente = Cliente.objects.get(id_cliente=cliente_id)

    if request.method == 'POST':
        form = CancionForm(request.POST)
        if form.is_valid():
            nombre_cancion = form.cleaned_data['nombre'].lower()
            cancion, created = Cancion.objects.get_or_create(
                nombre=nombre_cancion)

            # Verifica si el cliente ya ha alcanzado el límite de 10 canciones
            if ListaCancion.objects.filter(cliente=cliente).count() >= 10:
                messages.error(
                    request, "No puedes agregar más de 10 canciones.")
                return render(request, 'agregar_canciones.html', {'form': form, 'cliente': cliente})

            # Comprobar si la canción ya está en la lista del cliente
            if ListaCancion.objects.filter(cliente=cliente, cancion=cancion).exists():
                messages.error(request, "Ya tienes esta canción en tu lista.")
            else:
                ListaCancion.objects.create(cliente=cliente, cancion=cancion)
                messages.success(
                    request, "Canción agregada exitosamente a tu lista.")
                return redirect('home')
        else:
            messages.error(
                request, "Hay errores en el formulario, por favor corrígelos.")
    else:
        form = CancionForm()

    return render(request, 'agregar_canciones.html', {'form': form, 'cliente': cliente})


<form action = "" method = "post" >
            {% csrf_token % }
            {{form.as_p}}
            <button type = "submit" class = "btn btn-primary" > Agregar Cancion < /button >
            <a href = "{% url 'home' %}" class = "btn btn-danger" > Volver < /a >
          </form>