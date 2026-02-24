"""Tests fonctionnels des routes."""

import pytest


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


class TestRouteContent:
    """Verifie que chaque route authentifiee contient le contenu attendu."""

    def test_dashboard_contains_performance(self, auth_client):
        resp = auth_client.get('/dashboard')
        assert b'Performance' in resp.data

    def test_performance_contains_oee(self, auth_client):
        resp = auth_client.get('/performance')
        assert b'OEE' in resp.data

    def test_qualite_contains_conformit(self, auth_client):
        resp = auth_client.get('/qualite')
        # 'conformit' correspond au début de 'conformité' / 'non-conformité'
        assert b'conformit' in resp.data

    def test_delai_contains_lead(self, auth_client):
        resp = auth_client.get('/delai')
        assert b'Lead' in resp.data

    def test_energie_contains_nergie(self, auth_client):
        resp = auth_client.get('/energie')
        # 'nergie' est le suffixe ASCII de 'énergie' / 'Énergie' en UTF-8
        assert b'nergie' in resp.data

    def test_stock_contains_buffer(self, auth_client):
        resp = auth_client.get('/stock')
        assert b'Buffer' in resp.data

    def test_api_kpis_structure(self, auth_client):
        """Le JSON /api/kpis doit contenir les 5 clés avec chacune une clé 'value'."""
        resp = auth_client.get('/api/kpis')
        assert resp.status_code == 200
        data = resp.get_json()
        expected_keys = ('oee', 'non_conformity', 'lead_time', 'energy', 'buffer')
        for key in expected_keys:
            assert key in data, f"Clé '{key}' manquante dans /api/kpis"
            assert 'value' in data[key], f"Clé 'value' manquante dans data['{key}']"


@pytest.fixture
def responsable_client(client):
    """Client connecte en tant que responsable."""
    client.post('/login', data={
        'identifiant': 'responsable',
        'mot_de_passe': 'resp123',
    })
    return client


class TestResponsableRole:
    """Verifie les droits d'acces du role responsable."""

    def test_responsable_can_access_dashboard(self, responsable_client):
        resp = responsable_client.get('/dashboard')
        assert resp.status_code == 200

    def test_responsable_can_access_performance(self, responsable_client):
        resp = responsable_client.get('/performance')
        assert resp.status_code == 200

    def test_responsable_can_access_qualite(self, responsable_client):
        resp = responsable_client.get('/qualite')
        assert resp.status_code == 200

    def test_responsable_can_access_delai(self, responsable_client):
        resp = responsable_client.get('/delai')
        assert resp.status_code == 200

    def test_responsable_can_access_energie(self, responsable_client):
        resp = responsable_client.get('/energie')
        assert resp.status_code == 200

    def test_responsable_can_access_stock(self, responsable_client):
        resp = responsable_client.get('/stock')
        assert resp.status_code == 200

    def test_responsable_can_export_excel(self, responsable_client):
        resp = responsable_client.get('/export/excel')
        assert resp.status_code == 200

    def test_responsable_can_export_pdf(self, responsable_client):
        resp = responsable_client.get('/export/pdf')
        assert resp.status_code == 200
