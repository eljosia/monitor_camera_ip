# Monitor de Cámaras IP

Este proyecto está diseñado para monitorear cámaras IP, proporcionando una forma eficiente de gestionar y visualizar las transmisiones de las cámaras.

## Características

- Monitoreo en tiempo real de cámaras IP.
- Configuración y puesta en marcha sencillas.
- Escalable para múltiples cámaras.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/eljosia/monitor_camera_ip.git
   ```
2. Navega al directorio del proyecto:
   ```bash
   cd monitor_camera_ip
3. Crea un ejecutable utilizando PyInstaller:
    ```bash
    pyinstaller --onefile --windowed main.py
    ```

4. Sigue las instrucciones de configuración en la documentación.

## Uso

1. Ejecuta el archivo generado en el paso anterior ubicado en `./dist/main.exe`.
### Agregar Cámaras IP por Transmisión RTSP

1. Asegúrate de que las cámaras IP sean compatibles con el protocolo RTSP.
2. Obtén la URL de transmisión RTSP de cada cámara. Por ejemplo:
    ```
    rtsp://usuario:contraseña@dirección_ip:puerto/ruta
    ```
3. Ingresa las URLs de las cámaras en la interfaz de configuración proporcionada por la aplicación.
4. Guarda los cambios y verifica que las transmisiones se muestren correctamente en la interfaz.


## Créditos

Este proyecto fue desarrollado con la asistencia de [GitHub Copilot](https://github.com/features/copilot). Un agradecimiento especial al usuario por su visión y guía en la creación de este proyecto.
