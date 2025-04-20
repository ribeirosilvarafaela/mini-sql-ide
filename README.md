
```markdown
# Mini IDE SQL Online com Flask

Este projeto é uma mini IDE SQL onde você pode:

- Fazer upload de múltiplos arquivos CSV
- Cada CSV vira uma tabela separada no banco SQLite (em memória)
- Executar consultas SQL diretamente via navegador
- Ver o resultado das consultas na tela

---

## 🚀 Como usar

### 1. Clone este repositório ou copie os arquivos

```bash
git clone https://github.com/seuusuario/mini-ide-sql.git
cd mini-ide-sql
```

### 2. Crie um ambiente virtual (recomendado)

No terminal, digite:

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# Windows
venv\Scripts\activate

# MacOS/Linux
source venv/bin/activate
```

### 3. Instale as dependências

Com o ambiente virtual ativado:

```bash
pip install flask pandas
```

### 4. Rode o servidor Flask

```bash
python app.py
```

### 5. Acesse pelo navegador

Abra [http://localhost:5000/](http://localhost:5000/) no seu navegador.

---

## 📄 Funcionalidades

- Upload de arquivos `.csv`
- Cada arquivo gera uma nova tabela no SQLite em memória
- Execução de comandos SQL diretamente pela interface web
- Listagem automática das tabelas existentes
- Resultado das consultas exibido em formato de tabela

---

## ⚙️ Tecnologias utilizadas

- [Flask](https://flask.palletsprojects.com/)
- [Pandas](https://pandas.pydata.org/)
- [Bootstrap 5](https://getbootstrap.com/)
- [SQLite (modo memória)](https://www.sqlite.org/inmemorydb.html)

---

## 📚 Exemplos de Consulta SQL

```sql
-- Listar tudo de uma tabela chamada vendas_janeiro
SELECT * FROM vendas_janeiro;

-- Buscar apenas nome e idade de clientes com mais de 30 anos
SELECT nome, idade FROM clientes WHERE idade > 30;
```

---

## 🛡️ Observações
Este projeto é apenas para fins de estudo e prática de SQL em ambiente local.  
Não foi projetado para uso em produção.

---
```
