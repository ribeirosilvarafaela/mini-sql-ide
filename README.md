```markdown
# Mini IDE SQL Online com Flask

Este projeto é uma mini IDE SQL onde você pode:

- Fazer upload de múltiplos arquivos CSV
- Cada CSV vira uma tabela separada no banco SQLite (em memória)
- Escolher o tipo de dado de cada coluna (TEXT, INTEGER, REAL, DATE ou TIMESTAMP)
- Executar consultas SQL diretamente via navegador
- Exportar os resultados em CSV
- Cancelar uploads antes de finalizar
- Ambiente visual inspirado em IDEs modernas

---

## 🚀 Como usar localmente

### 1. Clone este repositório ou copie os arquivos

```bash
git clone https://github.com/ribeirosilvarafaela/mini-sql-ide.git
cd mini-ide-sql
```

### 2. Crie um ambiente virtual (recomendado)

No terminal:

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
pip install -r requirements.txt
```

### 4. Rode o servidor Flask

```bash
python app.py
```

### 5. Acesse pelo navegador

Abra [http://localhost:10000/](http://localhost:10000/) no seu navegador.

---

## 📄 Funcionalidades

- Upload de arquivos `.csv`
- Configuração personalizada dos tipos de colunas (TEXT, INTEGER, REAL, DATE, TIMESTAMP)
- Validação automática de tipos
- Execução de comandos SQL direto pela interface web
- Listagem automática das tabelas existentes
- Histórico das últimas consultas
- Exportação do resultado de consultas para CSV
- Limpeza automática de arquivos temporários
- Cheatsheet com comandos útei no SQLite 

---

## ⚙️ Tecnologias utilizadas

- [Flask](https://flask.palletsprojects.com/)
- [Pandas](https://pandas.pydata.org/)
- [Bootstrap 5](https://getbootstrap.com/)
- [Ace Editor (autocomplete SQL)](https://ace.c9.io/)
- [Particles.js](https://vincentgarreau.com/particles.js/)
- [Typed.js (efeito de digitação)](https://github.com/mattboldt/typed.js/)
- [SQLite (modo memória)](https://www.sqlite.org/inmemorydb.html)

---

## 📚 Exemplos de Consulta SQL

```sql
-- Listar tudo de uma tabela chamada clientes
SELECT * FROM clientes;

-- Buscar nome e idade de clientes com mais de 30 anos
SELECT nome, idade FROM clientes WHERE idade > 30;

-- Contar número de vendas por categoria
SELECT categoria, COUNT(*) FROM vendas GROUP BY categoria;

-- Buscar transações recentes
SELECT * FROM transacoes WHERE data_hora > '2024-01-01 00:00:00';
```

---

## 🛡️ Observações Importantes

- O banco de dados é **totalmente em memória** e será apagado se o servidor for reiniciado.
- Este projeto foi feito para **fins educacionais** e **prática de SQL**.
- Não é recomendado para uso em produção real sem as devidas adaptações de segurança.
- Os arquivos temporários são apagados automaticamente a cada novo upload para preservar espaço e organização.

---
