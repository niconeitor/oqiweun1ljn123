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
id_cliente= 5
def buscar_cliente_por_id(id_cliente):
    # Ejecutar la consulta para obtener los datos del cliente por su ID
    cur.execute("""
        SELECT Cliente.nombre, Cancion.nombre 
        FROM Cliente 
        LEFT JOIN Lista_cancion ON Cliente.id_cliente = Lista_cancion.id_cliente 
        LEFT JOIN Cancion ON Lista_cancion.id_cancion = Cancion.id_cancion 
        WHERE Cliente.id_cliente = %s
    """, (id_cliente,))
    cliente = cur.fetchall()

    # Cerrar la conexión y devolver los datos del cliente
    cur.close()
    conn.close()
    return cliente

# Buscar al cliente en la base de datos por su ID
cliente = buscar_cliente_por_id(id_cliente)

# Si se encontró al cliente
def cancion_aleatoria(cliente):
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
print(cancion_aleatoria(cliente))