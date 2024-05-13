import psycopg2

try:
    conn = psycopg2.connect(host="localhost",dbname="salsia", user="postgres", password="nicolas_asdf1", port="5432")
    print("Conexión exitosa")
except Exception as ex:
    print(ex)
       
cur = conn.cursor()

#Stuff

cur.execute("""
    CREATE TABLE Cliente (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    apellidos VARCHAR(255) NOT NULL,
    edad INT NOT NULL
);           
    CREATE TABLE IF NOT EXISTS Cancion(
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);
CREATE TABLE Cliente_Cancion (
    id_cliente INT,
    id_cancion INT,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id),
    FOREIGN KEY (id_cancion) REFERENCES Cancion(id),
    PRIMARY KEY (id_cliente, id_cancion)
);
            """)



#End of stuff

conn.commit()
cur.close()
conn.close()
