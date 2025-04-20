from flask import Flask, render_template, request, send_file
import pandas as pd
import sqlite3
import os
import re
import io

app = Flask(__name__)

# Banco de dados em memória
db_conn = sqlite3.connect(':memory:', check_same_thread=False)
db_cursor = db_conn.cursor()

# Último resultado e histórico
last_result_df = None
historico_consultas = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global db_conn, db_cursor, last_result_df, historico_consultas
    mensagem = ''
    resultado = None
    colunas = []
    tabelas = []

    if request.method == 'POST':
        if 'csv_file' in request.files and request.files['csv_file'].filename != '':
            csv_file = request.files['csv_file']
            df = pd.read_csv(csv_file)
            table_name = limpar_nome_tabela(csv_file.filename)
            try:
                df.to_sql(table_name, db_conn, if_exists='replace', index=False)
                mensagem = f'CSV \"{csv_file.filename}\" carregado como tabela \"{table_name}\" com {len(df)} linhas.'
            except Exception as e:
                mensagem = f"Erro ao carregar CSV: {str(e)}"

        elif 'query' in request.form:
            query = request.form['query']
            try:
                res = db_cursor.execute(query)
                if res.description:
                    resultado = res.fetchall()
                    colunas = [description[0] for description in res.description]
                    last_result_df = pd.DataFrame(resultado, columns=colunas)
                else:
                    mensagem = "Comando SQL executado com sucesso (sem resultados)."
                    resultado = []
                    last_result_df = pd.DataFrame()

                # Salva no histórico
                if query.strip():
                    historico_consultas.insert(0, query.strip())
                    historico_consultas = historico_consultas[:5]  # Mantém os últimos 5
            except Exception as e:
                mensagem = f"Erro na consulta SQL: {str(e)}"

    tabelas = buscar_tabelas()
    autocomplete_data = get_autocomplete_data(tabelas)
    return render_template('index.html', mensagem=mensagem, resultado=resultado, colunas=colunas, tabelas=tabelas, autocomplete_data=autocomplete_data, historico=historico_consultas)

@app.route('/exportar_csv')
def exportar_csv():
    global last_result_df
    if last_result_df is not None and not last_result_df.empty:
        output = io.StringIO()
        last_result_df.to_csv(output, index=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='resultado_consulta.csv')
    else:
        return "Nenhum resultado para exportar."

def limpar_nome_tabela(nome_arquivo):
    nome = os.path.splitext(nome_arquivo)[0]
    nome = re.sub(r'\W+', '_', nome)
    return nome.lower()

def buscar_tabelas():
    try:
        res = db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = [row[0] for row in res.fetchall()]
        return tabelas
    except Exception:
        return []

def get_autocomplete_data(tabelas):
    data = []
    for tabela in tabelas:
        try:
            res = db_cursor.execute(f"PRAGMA table_info({tabela});")
            colunas = [row[1] for row in res.fetchall()]
            data.append({"name": tabela, "meta": "tabela"})
            for coluna in colunas:
                data.append({"name": coluna, "meta": f"coluna de {tabela}"})
        except:
            continue
    return data 

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
