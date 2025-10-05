web: export PYTHONPATH=$PYTHONPATH:./flask_app && python -m flask --app flask_app.App db upgrade && python -m flask --app flask_app.App seed-db && gunicorn flask_app.App:app
