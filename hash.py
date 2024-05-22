import bcrypt

# Hash guardado en tu base de datos
hashed_password = '$2a$12$AHbIE2lol5Ga6V46HxFYxOE118XbD0SG0Wi8vNwa6YMIrkgDwtw/y'

# Contraseña ingresada por el usuario
password_entered = 'leica666'

# Verificar si la contraseña ingresada coincide con el hash
if bcrypt.checkpw(password_entered.encode('utf-8'), hashed_password.encode('utf-8')):
    print("La contraseña es correcta")
else:
    print("La contraseña es incorrecta")
