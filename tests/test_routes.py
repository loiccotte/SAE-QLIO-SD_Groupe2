"""Tests fonctionnels des routes."""


class TestProtectedRoutes:
    """Verifie que les routes protegees redirigent vers /login."""

    def test_dashboard_requires_login(self, client):
        resp = client.get('/dashboard')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_performance_requires_login(self, client):
        resp = client.get('/performance')
        assert resp.status_code == 302

    def test_qualite_requires_login(self, client):
        resp = client.get('/qualite')
        assert resp.status_code == 302

    def test_delai_requires_login(self, client):
        resp = client.get('/delai')
        assert resp.status_code == 302

    def test_energie_requires_login(self, client):
        resp = client.get('/energie')
        assert resp.status_code == 302

    def test_stock_requires_login(self, client):
        resp = client.get('/stock')
        assert resp.status_code == 302

    def test_api_kpis_requires_login(self, client):
        resp = client.get('/api/kpis')
        assert resp.status_code == 302


class TestAuthenticatedRoutes:
    """Verifie que les routes retournent 200 une fois connecte."""

    def test_dashboard_ok(self, auth_client):
        resp = auth_client.get('/dashboard')
        assert resp.status_code == 200

    def test_performance_ok(self, auth_client):
        resp = auth_client.get('/performance')
        assert resp.status_code == 200

    def test_qualite_ok(self, auth_client):
        resp = auth_client.get('/qualite')
        assert resp.status_code == 200

    def test_delai_ok(self, auth_client):
        resp = auth_client.get('/delai')
        assert resp.status_code == 200

    def test_energie_ok(self, auth_client):
        resp = auth_client.get('/energie')
        assert resp.status_code == 200

    def test_stock_ok(self, auth_client):
        resp = auth_client.get('/stock')
        assert resp.status_code == 200

    def test_api_kpis_ok(self, auth_client):
        resp = auth_client.get('/api/kpis')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'oee' in data


class TestExportRBAC:
    """Verifie que l'export est interdit pour le role employe."""

    def test_export_excel_forbidden_employe(self, employe_client):
        resp = employe_client.get('/export/excel')
        # Doit rediriger (acces refuse)
        assert resp.status_code == 302

    def test_export_pdf_forbidden_employe(self, employe_client):
        resp = employe_client.get('/export/pdf')
        assert resp.status_code == 302

    def test_export_excel_ok_admin(self, auth_client):
        resp = auth_client.get('/export/excel')
        assert resp.status_code == 200

    def test_export_pdf_ok_admin(self, auth_client):
        resp = auth_client.get('/export/pdf')
        assert resp.status_code == 200


class Test404:
    """Verifie la page 404 personnalisee."""

    def test_404_page(self, client):
        resp = client.get('/page-qui-nexiste-pas')
        assert resp.status_code == 404
        assert b'ERREUR 404' in resp.data
