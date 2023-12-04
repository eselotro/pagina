from flask import Flask
from flask import render_template, request, redirect, Response, url_for, session, send_from_directory
from flask_mysqldb import MySQL,MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os


app = Flask(__name__, template_folder='templates')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'login'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


CARPETA= os.path.join('uploads')  
app.config['CARPETA'] = CARPETA 

#esta funcion es cuando se entra a la pagina principal
@app.route('/')
def home():
    return render_template('alumnos/index.html', mostrar_sidebar=False)

#aca accedemos a la pagina para iniciar sesion
@app.route('/login')
def login():
    return render_template('/alumnos/login.html')

#SECCION DE LOGIN ALUMNOS
#esta seccion es para validar el usuario al ingresar con email y password
@app.route('/acceso-usuario', methods= ["GET", "POST"])
def usuario():

    if request.method == 'POST' and 'txtCorreo' in request.form and 'txtPassword' in request.form:
        _correo = request.form ['txtCorreo']
        _password = request.form ['txtPassword']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s and password = %s', (_correo, _password)) 
        account = cur.fetchone()
        cur.close()

        if account:
            session['ingresado'] = True
            session['id'] = account['id']
            session['id_rol'] = account['id_rol']
            session['n_usuario'] = account['nombre']

            if session['id_rol'] == 1:
                return render_template("/alumnos/admin.html", mostrar_sidebar=True)
            elif session['id_rol'] == 2:
                return render_template("/alumnos/userLog.html", mostrar_sidebar=True)
        else:
            return render_template('/alumnos/login.html', mensaje_error="Usuario o contraseña incorrectos!")
    

# SECCION DE BUSQUEDA
@app.route('/buscar')
def buscar():
    busqueda = request.args.get('search')
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 10
    if busqueda:
        cur = mysql.connection.cursor()

        # Consulta en busca de coincidencias en nombre, apellido o DNI
        search = "SELECT * FROM usuarios WHERE nombre LIKE %s OR apellido LIKE %s OR dni = %s"
        offset = (pagina - 1) * por_pagina
        cur.execute(search, ('%' + busqueda + '%', '%' + busqueda + '%', busqueda))

        resultados = cur.fetchall()
        # Consulta para contar el total de resultados(esto seria para la paginacion)
        #count_query = "SELECT COUNT(*) FROM usuarios WHERE nombre LIKE %s OR apellido LIKE %s OR dni = %s" 
        #cur.execute(count_query, ('%' + busqueda + '%', '%' + busqueda + '%', busqueda))
        #total_resultado = cur.fetchone()[0]
        cur.close()
        
        if not resultados:
            return render_template('/alumnos/resultados_busqueda.html', resultados=resultados, mensaje_resultado="No Hay conincidencias en la busqueda....revisa los datos ingresado!")

        return render_template('/alumnos/resultados_busqueda.html', resultados=resultados)
    
    return redirect(url_for('home'))

#SECCION DE REGISTRO DE ALUMNOS

@app.route('/registro')
def registo():
    return render_template('/alumnos/registro.html', mostrar_sidebar=True)

@app.route('/nuevo-registro', methods=["GET", "POST"])
def nuevo_registro():
    if request.method == 'POST':
        os.makedirs("uploads", exist_ok=True)
    
        dni=request.form['txtDni']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios where dni =%s", (dni,))
        if cur.fetchone():
            return render_template('alumnos/registro.html', error="Tu DNI ya se encuentra registrado, volve a intentarlo", mostrar_sidebar=True)
        nombre=request.form['txtNombre']
        apellido=request.form['txtApellido']
        correo=request.form['txtCorreo']
        password=request.form['txtPassword']
        foto = request.files['txtFoto']

        now= datetime.now()
        fecha = now.strftime('%Y%H%M%S')
        
        if foto.filename != '':
            filename = fecha + "_" + foto.filename  # Agrega un guion bajo para legibilidad
            filepath = os.path.join("uploads", filename)  # Construye la ruta del archivo correctamente
            foto.save(filepath)

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO usuarios (dni, nombre, apellido, correo, password, foto, id_rol) VALUES (%s, %s, %s, %s, %s, %s, '2')", (dni, nombre, apellido, correo, password, foto.filename))
    mysql.connection.commit()
    cur.close()

    return render_template('/alumnos/login.html', mensaje_registro="Registro Exitoso!")

#-----LISTAR ALUMNOS-------------
@app.route('/listar', methods= ["GET", "POST"])
def listar(): 
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM `login`.`usuarios`;")
    usuarios = cur.fetchall()
    cur.close()
    
    return render_template("alumnos/listado.html",usuarios=usuarios, mostrar_sidebar=True)

#----------EDITAR USUARIOS----------
@app.route('/editar/<int:id>')
def editar(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM `login`.`usuarios` WHERE id= %s", (id,))
    mysql.connection.commit()
    usuarios = cur.fetchall()
    cur.close()

    return render_template('alumnos/editar.html', usuarios=usuarios)


#---------ACTUALIZAR ALUMNOS-----------------
@app.route('/actualizar', methods=["GET", "POST"])
def actualizar():
    if request.method == 'POST':
        dni = request.form['txtDni']
        nombre = request.form['txtNombre']
        apellido = request.form['txtApellido']
        correo = request.form['txtCorreo']
        password = request.form['txtPassword']
        foto = request.files['txtFoto']
        id = request.form['txtID']

        cur = mysql.connection.cursor()

        # Actualizar foto si se sube una nueva
        if foto.filename != '':
            now = datetime.now()
            fecha = now.strftime('%Y%H%M%S')
            filename = fecha + "_" + foto.filename
            filepath = os.path.join(app.config['CARPETA'], filename)
            foto.save(filepath)

            cur.execute("SELECT foto FROM usuarios WHERE id=%s", (id,))
            fila = cur.fetchone()

            if fila and fila['foto']:
                old_file_path = os.path.join(app.config['CARPETA'], fila['foto'])
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            cur.execute("UPDATE usuarios SET foto=%s WHERE id=%s", (filename, id))
            mysql.connection.commit()

        # Hashear la contraseña antes de actualizar, en caso de que el usuario cambie el password
        #password_hashed = generate_password_hash(password, method='pbkdf2:sha256')

        # Actualizar otros datos del usuario
        cur.execute("UPDATE usuarios SET dni=%s, nombre=%s, apellido=%s, correo=%s, password=%s WHERE id=%s", (dni, nombre, apellido, correo, password, id))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('listar'))
    else:
        # Manejar otros métodos como GET si es necesario
        return redirect(url_for('actualizar'))

#llama la imagen de la carpeta uploads, para mostrarla en el formulario de actualizacion   
@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['CARPETA'], filename)

#----------BORRAR USUARIOS----------
@app.route('/borrar/<int:id>')
def borrar(id):
    try:
        cur = mysql.connection.cursor()

        # Obtener el nombre del archivo de la foto
        cur.execute("SELECT foto FROM usuarios WHERE id = %s", (id,))
        fila = cur.fetchone()

        # Si hay una foto, eliminarla del sistema de archivos
        if fila and fila['foto']:
            file_path = os.path.join(app.config['CARPETA'], fila['foto'])
            if os.path.exists(file_path):
                os.remove(file_path)

        # Eliminar el registro del usuario de la base de datos
        cur.execute("DELETE FROM usuarios WHERE id = %s", (id,))
        mysql.connection.commit()

    except Exception as e:
        print("Ocurrió un error al borrar el usuario:", e)
        

    finally:
        cur.close()

    return redirect(url_for('listar'))



#ESTE SERIA PARA EL LOGOUT  
@app.route('/logout')
def logout():
    session.pop('ingresado', None)
    session.pop('id', None)
    session.pop('id_rol', None)

    return redirect(url_for('home'))



    
    
    
if __name__ == '__main__':
    app.secret_key = "PatitaFelices"
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)