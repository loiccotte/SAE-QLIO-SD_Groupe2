"""Tests unitaires des fonctions KPI de services.py."""

VALID_STATUSES = ('normal', 'warning', 'critical', 'error')


def test_calculate_oee(app):
    with app.app_context():
        from app import services
        result = services.calculate_oee()
        assert 'value' in result
        assert 'availability' in result
        assert 'performance' in result
        assert 'quality' in result
        assert 'status' in result
        assert isinstance(result['value'], (int, float))
        # Plages de valeurs
        assert 0 <= result['value'] <= 100
        assert 0 <= result['availability'] <= 100
        assert 0 <= result['performance'] <= 100
        assert 0 <= result['quality'] <= 100
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_utilization(app):
    with app.app_context():
        from app import services
        result = services.calculate_utilization()
        assert 'overall' in result
        assert 'by_machine' in result
        assert 'status' in result
        assert isinstance(result['by_machine'], list)
        # Plages de valeurs
        assert 0 <= result['overall'] <= 100
        # Données seed : MachineReport pour machine 1 → liste non vide
        assert len(result['by_machine']) > 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_throughput(app):
    with app.app_context():
        from app import services
        result = services.calculate_throughput()
        assert 'value' in result
        assert 'monthly' in result
        assert 'status' in result
        # Plages de valeurs
        assert result['value'] >= 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_cycle_time(app):
    with app.app_context():
        from app import services
        result = services.calculate_cycle_time()
        assert 'value' in result
        assert 'status' in result
        assert isinstance(result['value'], (int, float))
        # Plage de valeurs
        assert result['value'] >= 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_non_conformity(app):
    with app.app_context():
        from app import services
        result = services.calculate_non_conformity()
        assert 'value' in result
        assert 'rate_orders' in result
        assert 'rate_parts' in result
        assert 'by_machine' in result
        assert 'status' in result
        # Plages de valeurs
        assert 0 <= result['value'] <= 100
        assert 0 <= result['rate_orders'] <= 100
        assert 0 <= result['rate_parts'] <= 100
        # Données seed : PartsReport pour machine 1 → liste non vide
        assert len(result['by_machine']) > 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_detection_time(app):
    with app.app_context():
        from app import services
        result = services.calculate_detection_time()
        assert 'value' in result
        assert 'by_event' in result
        assert 'count' in result
        assert 'status' in result
        # Plage de valeurs
        assert result['value'] >= 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_lead_time(app):
    with app.app_context():
        from app import services
        result = services.calculate_lead_time()
        assert 'value' in result
        assert 'distribution' in result
        assert 'count' in result
        assert 'status' in result
        assert isinstance(result['distribution'], list)
        # Données seed : 5 ordres avec durée 2h → distribution non vide, lead time > 0
        assert result['value'] > 0
        assert len(result['distribution']) > 0
        assert result['count'] > 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_buffer_wait_time(app):
    with app.app_context():
        from app import services
        result = services.calculate_buffer_wait_time()
        assert 'value' in result
        assert 'by_event' in result
        assert 'count' in result
        assert 'status' in result
        # On a injecte des etapes buffer OpNo=212
        assert result['count'] > 0
        assert result['value'] > 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_energy_summary(app):
    with app.app_context():
        from app import services
        result = services.calculate_energy_summary()
        assert 'value' in result
        assert 'unit' in result
        assert 'air_value' in result
        assert 'timeline' in result
        assert 'status' in result
        assert isinstance(result['timeline'], list)
        # Plage de valeurs
        assert result['value'] >= 0
        assert result['air_value'] >= 0
        # Données seed : Steps + ResourceOperation → timeline non vide
        assert len(result['timeline']) > 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_buffer_occupancy(app):
    with app.app_context():
        from app import services
        result = services.calculate_buffer_occupancy()
        assert 'value' in result
        assert 'by_buffer' in result
        assert 'total_capacity' in result
        assert 'status' in result
        assert isinstance(result['by_buffer'], list)
        assert len(result['by_buffer']) > 0
        # Plage de valeurs
        assert 0 <= result['value'] <= 100
        # Statut valide
        assert result['status'] in VALID_STATUSES


def test_calculate_stock_variation(app):
    with app.app_context():
        from app import services
        result = services.calculate_stock_variation()
        assert 'variations' in result
        assert 'max_variation' in result
        assert 'status' in result
        assert isinstance(result['variations'], list)
        # Données seed : 2 buffers avec positions → variations non vide
        assert len(result['variations']) > 0
        assert result['max_variation'] >= 0
        # Statut valide
        assert result['status'] in VALID_STATUSES


class TestServicesEdgeCases:
    """Tests sur les cas limites et cohérence interne des KPIs."""

    def test_oee_components_sum(self, app):
        """availability * performance * quality doit être cohérent avec value (à l'arrondi près)."""
        with app.app_context():
            from app import services
            result = services.calculate_oee()
            if result['status'] != 'error':
                expected = (
                    result['availability'] / 100
                    * result['performance'] / 100
                    * result['quality'] / 100
                    * 100
                )
                assert abs(result['value'] - expected) < 1.0  # tolérance arrondi

    def test_non_conformity_rate_between_0_and_100(self, app):
        """rate_orders et rate_parts doivent être bornés entre 0 et 100."""
        with app.app_context():
            from app import services
            result = services.calculate_non_conformity()
            assert 0 <= result['rate_orders'] <= 100
            assert 0 <= result['rate_parts'] <= 100

    def test_buffer_occupancy_rate_bounded(self, app):
        """Le taux d'occupation des buffers doit être entre 0 et 100."""
        with app.app_context():
            from app import services
            result = services.calculate_buffer_occupancy()
            assert 0 <= result['value'] <= 100

    def test_lead_time_count_matches_distribution(self, app):
        """count doit être égal à len(distribution)."""
        with app.app_context():
            from app import services
            result = services.calculate_lead_time()
            assert result['count'] == len(result['distribution'])
