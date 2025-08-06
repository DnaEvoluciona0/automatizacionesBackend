Hola programador de DNA, aqui te dejamos unas instrucciones claras de lo que hay que hacer una vez clones el repositorio desde GitHub


1.- Una vez clonado necesitas crear fuera del proyecto tu entorno virtual, es decir, automatizacionesBackend y tu env deben estar al mismo nivel de carpeta.
    Para ello una vez estes situado fuera del proyecto usaras el siguiente codigo en la consola
        python -m venv nombreENV

2.- Debes activar tu entorno virtual para ello colocaras lo siguiente en la consola, sabras que esta activado porque al lado de donde te dice la carpeta en la que te encuentras abra aparecido lo siugiente "(nombreENV)"
        cd nombreENV/Scripts
        Scripts

3.- Despues debe salir de tu entorno y entrar al proyecto, en el debes hacer las migraciones:
        cd automatizacionesBackend
        py manage.py makemigrations
        py manage.py migrate

4.- Finalmente para correr el proyecto de manera local usa:
        py manage.py runserver