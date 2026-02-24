"""Tests unitaires des fonctions KPI de services.py."""


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


def test_calculate_utilization(app):
    with app.app_context():
        from app import services
        result = services.calculate_utilization()
        assert 'overall' in result
        assert 'by_machine' in result
        assert 'status' in result
        assert isinstance(result['by_machine'], list)


def test_calculate_throughput(app):
    with app.app_context():
        from app import services
        result = services.calculate_throughput()
        assert 'value' in result
        assert 'monthly' in result
        assert 'status' in result


def test_calculate_cycle_time(app):
    with app.app_context():
        from app import services
        result = services.calculate_cycle_time()
        assert 'value' in result
        assert 'status' in result
        assert isinstance(result['value'], (int, float))


def test_calculate_non_conformity(app):
    with app.app_context():
        from app import services
        result = services.calculate_non_conformity()
        assert 'value' in result
        assert 'rate_orders' in result
        assert 'rate_parts' in result
        assert 'by_machine' in result
        assert 'status' in result


def test_calculate_detection_time(app):
    with app.app_context():
        from app import services
        result = services.calculate_detection_time()
        assert 'value' in result
        assert 'by_event' in result
        assert 'count' in result
        assert 'status' in result


def test_calculate_lead_time(app):
    with app.app_context():
        from app import services
        result = services.calculate_lead_time()
        assert 'value' in result
        assert 'distribution' in result
        assert 'count' in result
        assert 'status' in result
        assert isinstance(result['distribution'], list)


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


def test_calculate_stock_variation(app):
    with app.app_context():
        from app import services
        result = services.calculate_stock_variation()
        assert 'variations' in result
        assert 'max_variation' in result
        assert 'status' in result
        assert isinstance(result['variations'], list)
