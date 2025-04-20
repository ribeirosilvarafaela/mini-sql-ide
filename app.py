from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import pandas as pd
import sqlite3
import os
import re
import io
import uuid
import csv
import glob
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'depois_eu_vejo_isso'

# Banco de dados em memória
db_conn = sqlite3.connect(':memory:', check_same_thread=False)
db_cursor = db_conn.cursor()

# Home
@app.route('/')
def index():
    tabelas = buscar_tabelas()
    autocomplete_data = []
    return render_template('index.html', tabelas=tabelas, autocomplete_data=autocomplete_data)

# Cheatsheet
@app.route('/cheatsheet')
def cheatsheet():
    return render_template('cheatsheet.html')

# Upload CSV
@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    limpar_jsons_temp() # Limpa arquivos temporários
    csv_file = request.files['csv_file']
    if not csv_file:
        return redirect(url_for('index'))

    df = pd.read_csv(csv_file)
    table_name = limpar_nome_tabela(csv_file.filename)
    temp_id = str(uuid.uuid4())
    temp_json_path = f"temp_{temp_id}.json"
    df.to_json(temp_json_path)

    session['temp_json_path'] = temp_json_path
    session['temp_table_name'] = table_name

    # Sugestões e exemplos
    colunas = list(df.columns)
    sugestoes_tipos = {}
    exemplos = {}

    for coluna in colunas:
        exemplos[coluna] = df[coluna].dropna().astype(str).head(3).tolist()

        tipo_detectado = parece_data(df[coluna])
        if tipo_detectado:
            sugestoes_tipos[coluna] = tipo_detectado
        elif pd.api.types.is_integer_dtype(df[coluna]):
            sugestoes_tipos[coluna] = 'INTEGER'
        elif pd.api.types.is_float_dtype(df[coluna]):
            sugestoes_tipos[coluna] = 'REAL'
        else:
            sugestoes_tipos[coluna] = 'TEXT'

    return render_template('configurar_upload.html', colunas=colunas, sugestoes=sugestoes_tipos, exemplos=exemplos)

# Tela de configuração
@app.route('/configurar_upload')
def configurar_upload():
    temp_json_path = session.get('temp_json_path')
    table_name = session.get('temp_table_name')

    if not temp_json_path or not table_name:
        flash('Erro: Não encontramos um CSV carregado. Faça o upload novamente.')
        return redirect(url_for('index'))

    df = pd.read_json(temp_json_path)

    colunas = list(df.columns)
    sugestoes_tipos = {}
    exemplos = {}

    for coluna in colunas:
        exemplos[coluna] = df[coluna].dropna().astype(str).head(3).tolist()

        tipo_detectado = parece_data(df[coluna])
        if tipo_detectado:
            sugestoes_tipos[coluna] = tipo_detectado
        elif pd.api.types.is_integer_dtype(df[coluna]):
            sugestoes_tipos[coluna] = 'INTEGER'
        elif pd.api.types.is_float_dtype(df[coluna]):
            sugestoes_tipos[coluna] = 'REAL'
        else:
            sugestoes_tipos[coluna] = 'TEXT'

    return render_template('configurar_upload.html', colunas=colunas, sugestoes=sugestoes_tipos, exemplos=exemplos)

# Finalizar upload
@app.route('/finalizar_upload', methods=['POST'])
def finalizar_upload():
    tipos = request.form
    temp_json_path = session['temp_json_path']
    df = pd.read_json(temp_json_path)
    table_name = session['temp_table_name']

    # Validação de tipos
    for coluna in df.columns:
        tipo_escolhido = tipos[coluna]
        if not validar_coluna(df[coluna], tipo_escolhido):
            flash(f"Erro: A coluna '{coluna}' não pode ser convertida para {tipo_escolhido}. Corrija o tipo ou o CSV.")
            return redirect(url_for('configurar_upload'))

    campos = ", ".join([f'"{col}" {tipos[col]}' for col in df.columns])
    create_table_sql = f'CREATE TABLE "{table_name}" ({campos});'

    db_cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')
    db_cursor.execute(create_table_sql)

    for _, row in df.iterrows():
        placeholders = ", ".join(["?"] * len(row))
        insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
        db_cursor.execute(insert_sql, tuple(row))

    db_conn.commit()

    # Limpa sessão e deleta arquivo temporário
    if os.path.exists(temp_json_path):
        os.remove(temp_json_path)
    session.pop('temp_json_path', None)
    session.pop('temp_table_name', None)

    return redirect(url_for('index'))

# Executar consultas SQL
@app.route('/executar_query', methods=['POST'])
def executar_query():
    query = request.form.get('query')

    try:
        db_cursor.execute(query)
        if query.strip().lower().startswith("select"):
            resultado = db_cursor.fetchall()
            colunas = [description[0] for description in db_cursor.description]
        else:
            db_conn.commit()
            resultado = []
            colunas = []

        tabelas = buscar_tabelas()
        mensagem = "Consulta executada com sucesso!" if resultado else "Comando executado com sucesso."
        historico = session.get('historico', [])
        historico.insert(0, query)
        session['historico'] = historico[:3]

        autocomplete_data = [{"name": t, "meta": "tabela"} for t in tabelas]

        return render_template('index.html', tabelas=tabelas, resultado=resultado, colunas=colunas, mensagem=mensagem, historico=historico, autocomplete_data=autocomplete_data)

    except Exception as e:
        tabelas = buscar_tabelas()
        historico = session.get('historico', [])
        autocomplete_data = [{"name": t, "meta": "tabela"} for t in tabelas]
        return render_template('index.html', tabelas=tabelas, mensagem=f"Erro na consulta SQL: {str(e)}", historico=historico, autocomplete_data=autocomplete_data)

# Exportar resultado
@app.route('/exportar_csv')
def exportar_csv():
    historico = session.get('historico', [])
    if not historico:
        return redirect(url_for('index'))

    ultima_query = historico[0]

    try:
        db_cursor.execute(ultima_query)
        rows = db_cursor.fetchall()
        columns = [description[0] for description in db_cursor.description]

        temp_filename = "resultado_consulta.csv"
        with open(temp_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)

        return send_file(temp_filename, as_attachment=True)
    except Exception as e:
        flash(f"Erro ao exportar CSV: {str(e)}")
        return redirect(url_for('index'))

def limpar_jsons_temp():
    arquivos = glob.glob("temp_*.json")
    for arquivo in arquivos:
        try:
            os.remove(arquivo)
        except Exception as e:
            print(f"Erro ao tentar remover {arquivo}: {e}")
# Funções auxiliares
def buscar_tabelas():
    try:
        res = db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in res.fetchall()]
    except:
        return []

def limpar_nome_tabela(nome_arquivo):
    nome = os.path.splitext(nome_arquivo)[0]
    nome = re.sub(r'\W+', '_', nome)
    return nome.lower()

def parece_data(serie):
    formatos_timestamp = [
        '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y %H:%M:%S.%f', '%d/%m/%Y %H:%M:%S',
        '%Y/%m/%d %H:%M:%S.%f', '%Y/%m/%d %H:%M:%S'
    ]
    formatos_data = [
        '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'
    ]
    amostra = serie.dropna().astype(str).head(5)

    for valor in amostra:
        for formato in formatos_timestamp:
            try:
                datetime.strptime(valor.strip(), formato)
                return 'TIMESTAMP'
            except ValueError:
                continue

    for valor in amostra:
        for formato in formatos_data:
            try:
                datetime.strptime(valor.strip(), formato)
                return 'DATE'
            except ValueError:
                continue

    return None

def validar_coluna(serie, tipo):
    try:
        if tipo == 'INTEGER':
            pd.to_numeric(serie.dropna(), downcast='integer')
        elif tipo == 'REAL':
            pd.to_numeric(serie.dropna(), downcast='float')
        elif tipo == 'DATE':
            formatos = ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']
            for valor in serie.dropna():
                str_valor = str(valor).strip()
                if not any([tenta_data(str_valor, f) for f in formatos]):
                    return False
        elif tipo == 'TIMESTAMP':
            formatos = [
                '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y %H:%M:%S.%f', '%d/%m/%Y %H:%M:%S',
                '%Y/%m/%d %H:%M:%S.%f', '%Y/%m/%d %H:%M:%S'
            ]
            for valor in serie.dropna():
                str_valor = str(valor).strip()
                if not any([tenta_data(str_valor, f) for f in formatos]):
                    return False
        # TEXT aceita qualquer coisa
    except Exception:
        return False
    return True

def tenta_data(valor, formato):
    try:
        datetime.strptime(valor, formato)
        return True
    except:
        return False

@app.route('/cancelar_upload')
def cancelar_upload():
    temp_json_path = session.get('temp_json_path')

    if temp_json_path and os.path.exists(temp_json_path):
        os.remove(temp_json_path)

    session.pop('temp_json_path', None)
    session.pop('temp_table_name', None)

    flash('Upload cancelado com sucesso.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
