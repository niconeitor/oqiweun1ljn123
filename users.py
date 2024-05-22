import psycopg2

try:
    conn = psycopg2.connect(host="localhost",dbname="salsia", user="postgres", password="nicolas_asdf1", port="5432")
    print("Conexión exitosa")
except Exception as ex:
    print(ex)
       
cur = conn.cursor()

#Stuff

cur.execute("""
    CREATE TABLE IF NOT EXISTS Cliente (
    id_cliente SERIAL PRIMARY KEY,
    login VARCHAR(64) NOT NULL,
    pass VARCHAR(32) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    apellidos VARCHAR(255) NOT NULL,
    fecha_nac DATE NOT NULL,
    genero VARCHAR(10) NOT NULL,
    cuenta_vigente BIT NOT NULL
);           
    CREATE TABLE IF NOT EXISTS Cancion(
    id_cancion SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS Lista_cancion (
    id_cliente INT,
    id_cancion INT,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente),
    FOREIGN KEY (id_cancion) REFERENCES Cancion(id_cancion),
    PRIMARY KEY (id_cliente, id_cancion)
);
            """)



#End of stuff

conn.commit()
cur.close()
conn.close()
