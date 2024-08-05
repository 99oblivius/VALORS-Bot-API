from flask import request
from ..services import auth_service, update_service, data_service

def init_routes(app):
    @app.route('/update', methods=['POST'])
    def update():
        return update_service.handle_update(app, request)

    @app.route('/auth/<platform>/<token>')
    def auth(platform, token):
        return auth_service.handle_auth(app, platform, token)

    @app.route('/verify')
    def verify():
        return auth_service.handle_verify(app, request)

    @app.route('/verified')
    def verified():
        return auth_service.handle_verified(request)

    @app.route('/data')
    def data():
        return data_service.handle_data(request)