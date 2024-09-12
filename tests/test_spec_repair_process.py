from httpx import AsyncClient
from infra_ai_service.core.app import get_app
from infra_ai_service.config.config import Settings
from infra_ai_service.api.ai_enhance.spec_repair_process import router
from infra_ai_service.api.common.utils import setup_qdrant_environment
from io import BytesIO
from unittest.mock import patch, MagicMock
import pytest

app = get_app()


class MockSettings(Settings):
    '''
    Mock settings for testing purpose
    '''
    def __init__(self):
        super().__init__(
            ENV='test',
            HOST='localhost',
            PORT=8000
        )


@pytest.mark.asyncio
@patch('infra_ai_service.config.config.Settings', new=MockSettings)
@patch('infra_ai_service.api.common.utils.setup_qdrant_environment')
async def test_spec_repair_process(mock_setup_qdrant_environment):
    mock_fastembed_model = MagicMock()
    mock_qdrant_client = MagicMock()
    mock_setup_qdrant_environment.return_value = (
        mock_fastembed_model,
        mock_qdrant_client,
        'test_simi'
    )

    settings = MockSettings()
    base_url = f'http://localhost:{settings.PORT}/'
    async with AsyncClient(app=app, base_url=base_url) as ac:
        err_spec_file = BytesIO(b'err spec file')
        err_log_file = BytesIO(b'err log file content')
        file = {
            'err_spec_file': ('to_repair.spec',
                              err_spec_file),
            'err_log_file': ('error.log',
                             err_log_file)
        }
        resp = await ac.post('/api/v1/spec-repair/', files=file)
        assert resp.status_code == 200
