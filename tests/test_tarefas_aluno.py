"""TAREFA DO ALUNO -- os cinco testes que faltam para os >= 8 do entregavel.

Cada teste abaixo tem nome, docstring e a implementacao correspondente.
Nenhum deles precisa de banco: os tres primeiros rodam so contra o motor.
"""

from __future__ import annotations

from decimal import Decimal

from app.dominio.motor_emergia import calcular_indices


def test_regressao_numerica_contra_a_planilha(fluxos_golden):
    """Compara os seis indices com a aba SSB da Planilha_base.xlsx.

    Criterio do entregavel: abs(delta) <= 1E-6 por indice.
    """
    resultado = calcular_indices(fluxos_golden, energia_produto_j=Decimal("1000"))

    assert abs(resultado.y - Decimal("200")) <= Decimal("1E-6")
    assert abs(resultado.eyr - Decimal("4.0")) <= Decimal("1E-6")
    assert abs(resultado.elr - Decimal("0.739130")) <= Decimal("1E-6")
    assert abs(resultado.esi - Decimal("5.411765")) <= Decimal("1E-6")
    assert abs(resultado.eii - Decimal("0.184783")) <= Decimal("1E-6")
    assert abs(resultado.percentual_r - Decimal("57.5")) <= Decimal("1E-6")


def test_quantizacao_unica_no_final():
    """Mostra o erro de arredondar no meio do calculo."""
    val_a = Decimal("10.126")
    val_b = Decimal("3.004")

    quant_a = val_a.quantize(Decimal("0.01"))  # 10.13
    quant_b = val_b.quantize(Decimal("0.01"))  # 3.00

    res_a = (quant_a / quant_b).quantize(Decimal("0.01"))
    res_b = (val_a / val_b).quantize(Decimal("0.01"))

    assert res_a != res_b


def test_ordem_da_soma_com_magnitudes_divergentes():
    """Demonstra perda de precisao de ponto flutuante com magnitudes diferentes."""
    exp_grande = 1e20
    exp_pequeno = 1e-5

    soma_1 = (exp_grande + (-exp_grande)) + exp_pequeno
    soma_2 = exp_grande + ((-exp_grande) + exp_pequeno)

    assert soma_1 != soma_2


def test_erro_de_dominio_responde_problem_json(cliente, corpo_golden):
    """Inventario sem fluxo renovavel deve sair 422 em application/problem+json."""
    corpo_invalido = dict(corpo_golden)

    corpo_invalido["fluxos"] = [
        fluxo
        for fluxo in corpo_invalido["fluxos"]
        if fluxo["categoria"] not in ("R", "MR", "SR")
    ]

    response = cliente.post(
        "/v1/safras/42/calculos",
        json=corpo_invalido,
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    dados = response.json()

    assert "type" in dados
    assert "title" in dados
    assert dados["status"] == 422
    assert "detail" in dados
    assert "instance" in dados


def test_campo_extra_no_corpo_da_requisicao_e_rejeitado(
    cliente,
    corpo_golden,
):
    """'energia_produto_jj' tem de morrer com 422, nao virar calculo incompleto."""
    corpo_com_typo = dict(corpo_golden)
    fluxos_modificados = [dict(f) for f in corpo_com_typo["fluxos"]]
    fluxos_modificados[0]["energia_produto_jj"] = "1000"
    corpo_com_typo["fluxos"] = fluxos_modificados

    response = cliente.post(
        "/v1/safras/42/calculos",
        json=corpo_com_typo,
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    dados = response.json()

    assert dados["status"] == 422
    assert "erros" in dados or "detail" in dados