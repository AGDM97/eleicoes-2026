"""
Testes para FastAPI API.

Executar com: pytest tests/

Requer: pip install pytest pytest-asyncio httpx
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.app.api.main import app


@pytest.fixture
def client():
    """Fixture para cliente de teste."""
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Testa endpoint /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "db_exists" in data
    assert data["status"] == "ok"


def test_candidates_empty_query(client: TestClient) -> None:
    """Testa /candidates com query vazia."""
    response = client.get("/candidates?q=&limit=10&offset=0")
    assert response.status_code in [200, 503]  # 503 se banco não existe
    
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "assets_enabled" in data
        assert "votes_enabled" in data
        assert "finance_enabled" in data
        assert isinstance(data["items"], list)


def test_candidates_with_query(client: TestClient) -> None:
    """Testa /candidates com termo de busca."""
    response = client.get("/candidates?q=silva&limit=10&offset=0")
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


def test_candidates_pagination(client: TestClient) -> None:
    """Testa paginação de candidatos."""
    response = client.get("/candidates?q=&limit=5&offset=0")
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert len(data["items"]) <= 5


def test_candidate_assets(client: TestClient) -> None:
    """Testa /candidates/{id}/assets."""
    # Usa um ID fictício (a resposta dependerá do estado do banco)
    response = client.get("/candidates/1/assets?limit=10&offset=0")
    assert response.status_code in [200, 404, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


def test_candidate_votes_municipio(client: TestClient) -> None:
    """Testa /candidates/{id}/votes_municipio."""
    response = client.get("/candidates/1/votes_municipio?limit=10")
    assert response.status_code in [200, 404, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


def test_candidate_finance(client: TestClient) -> None:
    """Testa /candidates/{id}/finance."""
    response = client.get("/candidates/1/finance?top=10")
    assert response.status_code in [200, 404, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "candidate_id" in data
        assert "summary" in data
        assert "top_doadores" in data
        assert "top_fornecedores" in data


def test_invalid_candidate_id(client: TestClient) -> None:
    """Testa acesso a candidato inválido."""
    response = client.get("/candidates/999999999/finance?top=10")
    assert response.status_code in [404, 503]


def test_limit_parameter(client: TestClient) -> None:
    """Testa limite de resultados."""
    response = client.get("/candidates?q=&limit=100&offset=0")
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert len(data["items"]) <= 100


def test_offset_parameter(client: TestClient) -> None:
    """Testa deslocamento de paginação."""
    response1 = client.get("/candidates?q=&limit=5&offset=0")
    response2 = client.get("/candidates?q=&limit=5&offset=5")
    
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        
        # IDs não devem se repetir (se houver dados)
        if data1["items"] and data2["items"]:
            ids1 = {item["id"] for item in data1["items"]}
            ids2 = {item["id"] for item in data2["items"]}
            assert len(ids1 & ids2) == 0  # intersecção vazia
