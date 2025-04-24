#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template, abort
import requests
from dotenv import load_dotenv
from types import SimpleNamespace

# Carrega variáveis de ambiente
load_dotenv()
CHAVE_API = os.getenv("CHAVE_API_FUTEBOL")
URL_BASE  = "https://api.api-futebol.com.br/v1"
HEADERS   = {"Authorization": f"Bearer {CHAVE_API}"}

app = Flask(__name__)

def fetch(endpoint, params=None):
    """Faz GET na API e retorna JSON ou aborta em caso de erro."""
    resp = requests.get(f"{URL_BASE}{endpoint}", headers=HEADERS, params=params or {})
    if resp.status_code != 200:
        abort(resp.status_code)
    return resp.json()

def listar_itens(json_bruto, chave):
    """
    Se json_bruto for dict contendo a chave, retorna json_bruto[chave].
    Se for lista, retorna ela mesma.
    Caso contrário, retorna lista vazia.
    """
    if isinstance(json_bruto, dict):
        return json_bruto.get(chave, [])
    if isinstance(json_bruto, list):
        return json_bruto
    return []

@app.route("/")
def inicio():
    """Rota inicial: lista de campeonatos."""
    dados = fetch("/campeonatos")
    raw = listar_itens(dados, "campeonatos")

    campeonatos = []
    for c in raw:
        cid  = c.get("campeonato_id")
        nome = c.get("nome")
        slug = c.get("slug")
        if cid is not None:
            campeonatos.append(SimpleNamespace(id=cid, nome=nome, slug=slug))

    return render_template("campeonatos.html", campeonatos=campeonatos)

@app.route("/rodadas/<int:campeonato_id>")
def mostrar_rodadas(campeonato_id):
    """Exibe rodadas de um campeonato específico, com fallback por fases."""
    detalhe = fetch(f"/campeonatos/{campeonato_id}")
    nome_campeonato = detalhe.get("nome", "—")

    # Tenta buscar diretamente rodadas
    rod_data = fetch(f"/campeonatos/{campeonato_id}/rodadas")
    raw_rod  = listar_itens(rod_data, "rodadas")

    # Se não vier rodadas, obtém primeira fase e busca as rodadas dela
    if not raw_rod:
        fases_data = fetch(f"/campeonatos/{campeonato_id}/fases")
        raw_fases = listar_itens(fases_data, "fases")
        if raw_fases:
            primeira_fase_id = raw_fases[0].get("fase_id")
            fase_data = fetch(f"/campeonatos/{campeonato_id}/fases/{primeira_fase_id}")
            raw_rod = listar_itens(fase_data, "rodadas")

    rodadas = []
    for r in raw_rod:
        rid  = r.get("rodada_id")
        nome = r.get("nome") or f"Rodada {rid}"
        if rid is not None:
            rodadas.append(SimpleNamespace(id=rid, nome=nome))

    return render_template("rodadas.html", rodadas=rodadas, nome_campeonato=nome_campeonato)

@app.route("/partidas/<int:rodada_id>")
def mostrar_partidas(rodada_id):
    """Exibe as partidas de uma rodada específica."""
    part_data = fetch(f"/rodadas/{rodada_id}")
    raw_part  = listar_itens(part_data, "partidas")

    partidas = []
    for p in raw_part:
        mand = p.get("time_mandante", {})
        vis  = p.get("time_visitante", {})
        plac = p.get("placar", {})
        partidas.append(SimpleNamespace(
            mandante=mand.get("nome"),
            visitante=vis.get("nome"),
            gols_mandante=plac.get("mandante"),
            gols_visitante=plac.get("visitante"),
            status=p.get("status")
        ))

    return render_template("partidas.html", partidas=partidas)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
