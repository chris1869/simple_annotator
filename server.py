from app import APP
import app_backend
import app_frontend

APP.layout = app_frontend.get_layout()
APP.conf_server = app_backend.Annotator()

# Run the app
if __name__ == '__main__':
    APP.run_server(debug=True)
