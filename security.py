import os
import logging
from flask import flash

#  Protege a SECRET_KEY com variável de ambiente
def get_secret_key():
    return os.environ.get('SECRET_KEY', 'default_insegura')

#  Verifica se o upload é válido (extensão e tamanho)
def validar_upload_csv(csv_file, max_size_mb=5):
    if not csv_file.filename.endswith('.csv'):
        flash("Formato inválido. Apenas arquivos .csv são aceitos.", "danger")
        return False

    csv_file.seek(0, os.SEEK_END)
    size = csv_file.tell()
    csv_file.seek(0)

    if size > max_size_mb * 1024 * 1024:
        flash(f"Arquivo muito grande. Limite de {max_size_mb}MB.", "danger")
        return False

    return True

#  Bloqueia comandos SQL perigosos
def consulta_segura(query):
    comandos_bloqueados = ['DROP', 'DELETE', 'ALTER']
    upper_query = query.upper()

    for comando in comandos_bloqueados:
        if comando in upper_query:
            flash(f"⚠️ O comando {comando} não é permitido por segurança.", "danger")
            return False
    return True


def tratar_erro(e, contexto="Erro"):
    logging.error(f"[{contexto}] {str(e)}")
    flash(f"Erro: {str(e)}", "danger")
