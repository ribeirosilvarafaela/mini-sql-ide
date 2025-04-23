import os
import re
import io
import uuid
import csv
import glob
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import pandas as pd
import sqlite3
from dotenv import load_dotenv
from security import get_secret_key, validar_upload_csv, consulta_segura, tratar_erro

# Configuração
load_dotenv()
app = Flask(__name__)
app.secret_key = get_secret_key()

# Banco em memória
db_conn = sqlite3.connect(':memory:', check_same_thread=False)
db_cursor = db_conn.cursor()

# Home
@app.route('/')
def index():
    tabelas = buscar_tabelas()
    autocomplete_data = [{"name": t, "meta": "tabela"} for t in tabelas]
    historico = session.get('historico', [])
    return render_template('index.html', tabelas=tabelas, autocomplete_data=autocomplete_data, historico=historico)

# Cheatsheet
@app.route('/cheatsheet')
def cheatsheet():
    return render_template('cheatsheet.html')

# Upload CSV
@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    limpar_jsons_temp()
    csv_file = request.files['csv_file']

    if not csv_file or not validar_upload_csv(csv_file):
        return redirect(url_for('index'))

    try:
        df = pd.read_csv(csv_file)
        table_name = limpar_nome_tabela(csv_file.filename)
        temp_id = str(uuid.uuid4())
        temp_json_path = f"temp_{temp_id}.json"
        df.to_json(temp_json_path)

        session['temp_json_path'] = temp_json_path
        session['temp_table_name'] = table_name

        colunas = list(df.columns)
        sugestoes_tipos, exemplos = detectar_tipos(df)

        return render_template('configurar_upload.html', colunas=colunas, sugestoes=sugestoes_tipos, exemplos=exemplos)
    except Exception as e:
        tratar_erro(e, "Erro no upload")
        return redirect(url_for('index'))

# Tela de configuração
@app.route('/configurar_upload')
def configurar_upload():
    try:
        temp_json_path = session['temp_json_path']
        df = pd.read_json(temp_json_path)

        colunas = list(df.columns)
        sugestoes_tipos, exemplos = detectar_tipos(df)

        return render_template('configurar_upload.html', colunas=colunas, sugestoes=sugestoes_tipos, exemplos=exemplos)
    except Exception as e:
        tratar_erro(e, "Erro ao configurar upload")
        return redirect(url_for('index'))

# Finalizar upload
@app.route('/finalizar_upload', methods=['POST'])
def finalizar_upload():
    try:
        tipos = request.form
        temp_json_path = session['temp_json_path']
        df = pd.read_json(temp_json_path)
        table_name = session['temp_table_name']

        for coluna in df.columns:
            tipo_escolhido = tipos[coluna]
            if not validar_coluna(df[coluna], tipo_escolhido):
                flash(f"Erro: A coluna '{coluna}' não pode ser convertida para {tipo_escolhido}.", "danger")
                return redirect(url_for('configurar_upload'))

        campos = ", ".join([f'"{col}" {tipos[col]}' for col in df.columns])
        db_cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')
        db_cursor.execute(f'CREATE TABLE "{table_name}" ({campos});')

        for _, row in df.iterrows():
            insert_sql = f'INSERT INTO "{table_name}" VALUES ({", ".join(["?"] * len(row))})'
            db_cursor.execute(insert_sql, tuple(row))

        db_conn.commit()
        os.remove(temp_json_path)
        session.pop('temp_json_path', None)
        session.pop('temp_table_name', None)

        flash('Tabela criada com sucesso!', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        tratar_erro(e, "Erro ao finalizar upload")
        return redirect(url_for('index'))

# Cancelar upload
@app.route('/cancelar_upload')
def cancelar_upload():
    path = session.get('temp_json_path')
    if path and os.path.exists(path):
        os.remove(path)
    session.pop('temp_json_path', None)
    session.pop('temp_table_name', None)
    flash('Upload cancelado com sucesso.')
    return redirect(url_for('index'))

# Executar SQL
@app.route('/executar_query', methods=['POST'])
def executar_query():
    query = request.form.get('query')

    if not consulta_segura(query):
        return redirect(url_for('index'))

    try:
        db_cursor.execute(query)
        if query.strip().lower().startswith("select"):
            resultado = db_cursor.fetchall()
            colunas = [desc[0] for desc in db_cursor.description]
            mensagem = "Consulta executada com sucesso!"
        else:
            db_conn.commit()
            resultado = []
            colunas = []
            mensagem = "Comando executado com sucesso."

        tabelas = buscar_tabelas()
        historico = session.get('historico', [])
        historico.insert(0, query)
        session['historico'] = historico[:3]
        autocomplete_data = [{"name": t, "meta": "tabela"} for t in tabelas]

        return render_template('index.html', tabelas=tabelas, resultado=resultado, colunas=colunas,
                               mensagem=mensagem, historico=historico, autocomplete_data=autocomplete_data)
    except Exception as e:
        tratar_erro(e, "Erro na execução SQL")
        return redirect(url_for('index'))

# Exportar CSV
@app.route('/exportar_csv')
def exportar_csv():
    historico = session.get('historico', [])
    if not historico:
        flash("Nenhuma consulta disponível para exportar.", "warning")
        return redirect(url_for('index'))

    try:
        db_cursor.execute(historico[0])
        rows = db_cursor.fetchall()
        columns = [desc[0] for desc in db_cursor.description]

        temp_filename = "resultado_consulta.csv"
        with open(temp_filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

        return send_file(temp_filename, as_attachment=True)
    except Exception as e:
        tratar_erro(e, "Erro ao exportar CSV")
        return redirect(url_for('index'))

# Utilitários
def buscar_tabelas():
    try:
        return [row[0] for row in db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    except:
        return []

def limpar_jsons_temp():
    for arq in glob.glob("temp_*.json"):
        try:
            os.remove(arq)
        except Exception as e:
            print(f"Erro ao remover {arq}: {e}")

def limpar_nome_tabela(nome_arquivo):
    return re.sub(r'\W+', '_', os.path.splitext(nome_arquivo)[0]).lower()

def detectar_tipos(df):
    sugestoes = {}
    exemplos = {}

    for col in df.columns:
        exemplos[col] = df[col].dropna().astype(str).head(3).tolist()
        tipo = detectar_tipo_coluna(df[col])
        sugestoes[col] = tipo or 'TEXT'

    return sugestoes, exemplos

def detectar_tipo_coluna(serie):
    formatos_ts = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']
    formatos_data = ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']
    amostra = serie.dropna().astype(str).head(5)

    for val in amostra:
        for f in formatos_ts:
            try: datetime.strptime(val.strip(), f); return 'TIMESTAMP'
            except: continue

    for val in amostra:
        for f in formatos_data:
            try: datetime.strptime(val.strip(), f); return 'DATE'
            except: continue

    if pd.api.types.is_integer_dtype(serie): return 'INTEGER'
    if pd.api.types.is_float_dtype(serie): return 'REAL'
    return None

def validar_coluna(serie, tipo):
    try:
        if tipo == 'INTEGER':
            pd.to_numeric(serie.dropna(), downcast='integer')
        elif tipo == 'REAL':
            pd.to_numeric(serie.dropna(), downcast='float')
        elif tipo == 'DATE':
            for v in serie.dropna(): 
                if not any(datetime.strptime(str(v).strip(), f) for f in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']):
                    return False
        elif tipo == 'TIMESTAMP':
            for v in serie.dropna(): 
                if not any(datetime.strptime(str(v).strip(), f) for f in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']):
                    return False
    except:
        return False
    return True

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)