"""Tests d'authentification et RBAC."""


class TestLogin:
    """Tests du systeme de connexion."""

    def test_login_page_renders(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200
        assert b'ELEFAN' in resp.data

    def test_login_valid_admin(self, client):
        resp = client.post('/login', data={
            'identifiant': 'admin',
            'mot_de_passe': 'admin123'
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert '/dashboard' in resp.headers['Location']

    def test_login_valid_responsable(self, client):
        resp = client.post('/login', data={
            'identifiant': 'responsable',
            'mot_de_passe': 'resp123'
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_login_valid_operateur(self, client):
        resp = client.post('/login', data={
            'identifiant': 'operateur',
            'mot_de_passe': 'oper123'
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_login_invalid_password(self, client):
        resp = client.post('/login', data={
            'identifiant': 'admin',
            'mot_de_passe': 'wrong'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'incorrect' in resp.data

    def test_login_invalid_user(self, client):
        resp = client.post('/login', data={
            'identifiant': 'inconnu',
            'mot_de_passe': 'test'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'incorrect' in resp.data

    def test_login_redirects_if_already_logged(self, auth_client):
        resp = auth_client.get('/login')
        assert resp.status_code == 302
        assert '/dashboard' in resp.headers['Location']


class TestLogout:
    """Tests de la deconnexion."""

    def test_logout_clears_session(self, auth_client):
        resp = auth_client.get('/logout')
        assert resp.status_code == 302
        # Apres logout, le dashboard doit rediriger vers login
        resp2 = auth_client.get('/dashboard')
        assert resp2.status_code == 302
        assert '/login' in resp2.headers['Location']


class TestRoleHierarchy:
    """Tests du decorateur role_required."""

    def test_admin_can_export(self, auth_client):
        resp = auth_client.get('/export/excel')
        assert resp.status_code == 200

    def test_employe_cannot_export(self, employe_client):
        resp = employe_client.get('/export/excel', follow_redirects=False)
        assert resp.status_code == 302

    def test_employe_can_view_dashboard(self, employe_client):
        resp = employe_client.get('/dashboard')
        assert resp.status_code == 200

    def test_employe_can_view_detail_pages(self, employe_client):
        for route in ['/performance', '/qualite', '/delai', '/energie', '/stock']:
            resp = employe_client.get(route)
            assert resp.status_code == 200, f"Route {route} devrait etre accessible"
