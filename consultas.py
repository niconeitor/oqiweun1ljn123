import psycopg2
import random
try:
    conn = psycopg2.connect(host="localhost",dbname="salsia", user="postgres", password="nicolas_asdf1", port="5432")
    print("Conexión exitosa")
except Exception as ex:
    print(ex)
       
cur = conn.cursor()

#EL SIGUIENTE CÓDIGO ES SOLO LA LÓGICA DE COMO SERÍA, NO LO HE TESTEADO TODAVÍA


# Función para buscar cliente por ID en la base de datos
def buscar_cliente_por_id(id_cliente):
    # Realizar conexión a la base de datos
    conn = psycopg2.connect(
        dbname="nombre_base_de_datos",
        user="usuario",
        password="contraseña",
        host="localhost"
    )
    cursor = conn.cursor()

    # Ejecutar la consulta para obtener los datos del cliente por su ID
    cursor.execute("""
        SELECT Cliente.nombre, canciones.nombre 
        FROM Cliente 
        LEFT JOIN Cliente_Cancion ON Cliente.id = Cliente_Cancion.id_cliente 
        LEFT JOIN canciones ON Cliente_Cancion.id_cancion = canciones.id 
        WHERE Cliente.id = %s
    """, (id_cliente,))
    cliente = cursor.fetchall()

    # Cerrar la conexión y devolver los datos del cliente
    cursor.close()
    conn.close()
    return cliente

# Supongamos que tienes una función para reconocimiento facial que devuelve el ID del cliente
def reconocimiento_facial(imagen):
    # Aquí iría tu lógica para reconocimiento facial y devolver el ID del cliente
    # Por simplicidad, asumiré que devuelve un ID de cliente
    id_cliente = "123"
    return id_cliente

# Obtener el ID del cliente mediante reconocimiento facial
id_cliente = reconocimiento_facial("imagen.jpg")

# Buscar al cliente en la base de datos por su ID
cliente = buscar_cliente_por_id(id_cliente)

# Si se encontró al cliente
if cliente:
    nombre_cliente = cliente[0][0]  # Obtenemos el nombre del primer registro
    canciones_cliente = [c[1] for c in cliente if c[1] is not None]  # Ignoramos el nombre y obtenemos solo las canciones
    # Obtener una canción aleatoria del cliente si hay canciones registradas
    if canciones_cliente:
        cancion_aleatoria = random.choice(canciones_cliente)
        print("Cliente:", nombre_cliente)
        print("Canción Aleatoria:", cancion_aleatoria)
    else:
        print("El cliente no tiene canciones registradas.")
else:
    print("Cliente no encontrado en la base de datos.")