import hashlib
import sqlite3
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()


# =====================================================================
# FUNÇÕES AUXILIARES: CRIPTOGRAFIA (LGPD - Item 5.4) E BANCO DE DADOS
# =====================================================================
def criptografar(texto: str) -> str:
    """Criptografa CPF e Senha usando SHA-256 (Biblioteca padrão do Python)."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def get_db():
    """Conecta ao banco local SQLite (zero configuração) e ativa Foreign Keys."""
    conn = sqlite3.connect("oficina_db.sqlite")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_banco():
    """Cria as tabelas e insere os 3 registros iniciais caso o banco esteja vazio (Itens 2.1 e 2.2)."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cliente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            cpf TEXT NOT NULL,
            login TEXT NOT NULL,
            senha TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS veiculo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT NOT NULL,
            marca TEXT NOT NULL,
            cliente_id INTEGER NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES cliente(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS agendamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_agendamento TEXT NOT NULL,
            servico TEXT NOT NULL,
            veiculo_id INTEGER NOT NULL,
            FOREIGN KEY (veiculo_id) REFERENCES veiculo(id) ON DELETE CASCADE
        );
    """)
    if conn.execute("SELECT COUNT(*) FROM cliente").fetchone()[0] == 0:
        senha_padrao = criptografar("123")
        conn.executemany(
            "INSERT INTO cliente (nome, telefone, cpf, login, senha) VALUES (?, ?, ?, ?, ?)",
            [
                ("Ana Silva", "11999990001", criptografar("11111111111"), "ana", senha_padrao),
                ("Carlos Souza", "11999990002", criptografar("22222222222"), "carlos", senha_padrao),
                ("Mariana Costa", "11999990003", criptografar("33333333333"), "mariana", senha_padrao),
            ],
        )
        conn.executemany(
            "INSERT INTO veiculo (modelo, marca, cliente_id) VALUES (?, ?, ?)",
            [("Civic", "Honda", 1), ("Corolla", "Toyota", 2), ("Onix", "Chevrolet", 3)],
        )
        conn.executemany(
            "INSERT INTO agendamento (data_agendamento, servico, veiculo_id) VALUES (?, ?, ?)",
            [
                ("2026-05-20", "Troca de Óleo e Filtros", 1),
                ("2026-03-10", "Alinhamento e Balanceamento", 2),
                ("2025-11-05", "Revisão de Freios", 3),
            ],
        )
        conn.commit()
    conn.close()


inicializar_banco()


# =====================================================================
# ATIVIDADE 3: FUNCIONALIDADE DE LOGIN (Itens 3.1, 3.2 e 3.3)
# =====================================================================
@app.get("/", response_class=HTMLResponse)
def tela_login(erro: str = ""):
    msg_erro = f"<p style='color:red;'><b>{erro}</b></p>" if erro else ""
    return f"""
    <h2>Login - Oficina Mecânica</h2>
    {msg_erro}
    <form method="post" action="/login">
        Login: <input name="login" required> <br><br>
        Senha: <input type="password" name="senha" required> <br><br>
        <button type="submit">Entrar</button>
    </form>
    <p><small>Dica de teste: Login <b>ana</b> | Senha <b>123</b></small></p>
    """


@app.post("/login")
def fazer_login(login: str = Form(), senha: str = Form()):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM cliente WHERE login = ? AND senha = ?",
        (login, criptografar(senha)),
    ).fetchone()
    conn.close()

    # Item 3.3: Validação caso haja falha de autenticação
    if not user:
        return RedirectResponse("/?erro=Login+ou+senha+invalidos!", status_code=303)

    # Item 3.1 e 3.2: Redireciona para o módulo principal e cria sessão com tempo de expiração (1800s = 30 min)
    res = RedirectResponse("/principal", status_code=303)
    res.set_cookie(key="usuario_sessao", value=user["nome"], max_age=1800)
    return res


@app.get("/logout")
def logout():
    # Item 4.2: Meio para sair do sistema
    res = RedirectResponse("/", status_code=303)
    res.delete_cookie("usuario_sessao")
    return res


# =====================================================================
# ATIVIDADE 4: FUNCIONALIDADE PRINCIPAL DO SISTEMA (Itens 4.1, 4.2, 4.3)
# =====================================================================
@app.get("/principal", response_class=HTMLResponse)
def tela_principal(request: Request):
    usuario = request.cookies.get("usuario_sessao")
    if not usuario:
        return RedirectResponse("/?erro=Sessao+expirada.+Faca+login+novamente.", status_code=303)

    return f"""
    <h2>Sistema Oficina Mecânica - Tela Principal</h2>
    <p>Usuário logado: <b>{usuario}</b> | <a href="/logout">Sair do Sistema</a></p>
    <hr>
    <h3>Menu de Funcionalidades (Item 4.3):</h3>
    <ul>
        <li><a href="/clientes">Gerenciar Clientes</a></li>
        <li><a href="/veiculos">Gerenciar Veículos</a></li>
        <li><a href="/agendamentos">Gerenciar Agendamentos</a></li>
    </ul>
    """


# =====================================================================
# ATIVIDADE 5: GERENCIAMENTO DE CLIENTES (Itens 5.1, 5.2, 5.3, 5.4 e 5.5)
# =====================================================================
@app.get("/clientes", response_class=HTMLResponse)
def listar_clientes(busca: str = ""):
    conn = get_db()
    # Item 5.2: Busca com termo
    if busca:
        clientes = conn.execute("SELECT * FROM cliente WHERE nome LIKE ?", (f"%{busca}%",)).fetchall()
    else:
        clientes = conn.execute("SELECT * FROM cliente").fetchall()
    conn.close()

    linhas = ""
    for c in clientes:
        # Item 5.1 (Listar e Excluir) e Item 5.5 (Editar cliente já existente diretamente na linha)
        linhas += f"""
        <tr>
            <form method="post" action="/clientes/editar">
                <td>{c['id']}<input type="hidden" name="id" value="{c['id']}"></td>
                <td><input name="nome" value="{c['nome']}" required></td>
                <td><input name="telefone" value="{c['telefone']}" required></td>
                <td><input name="login" value="{c['login']}" required></td>
                <td><small>{c['cpf'][:12]}...</small></td>
                <td>
                    <button type="submit">Salvar Edição</button>
                    <a href="/clientes/excluir/{c['id']}">Excluir</a>
                </td>
            </form>
        </tr>
        """

    return f"""
    <p><a href="/principal">Voltar para Principal</a></p>
    <h2>Gerenciamento de Clientes</h2>

    <!-- Item 5.3 e 5.4: Inserir novo cliente (CPF e Senha serão criptografados) -->
    <h3>Novo Cliente</h3>
    <form method="post" action="/clientes/criar">
        Nome: <input name="nome" required>
        Telefone: <input name="telefone" required>
        CPF: <input name="cpf" required>
        Login: <input name="login" required>
        Senha: <input type="password" name="senha" required>
        <button type="submit">Cadastrar Cliente</button>
    </form>
    <hr>

    <!-- Item 5.2: Busca por termo -->
    <form method="get" action="/clientes">
        Buscar por nome: <input name="busca" value="{busca}">
        <button type="submit">Buscar</button>
        <a href="/clientes">Limpar</a>
    </form>
    <br>

    <!-- Item 5.1: Listagem -->
    <table border="1" cellpadding="5">
        <tr><th>ID</th><th>Nome</th><th>Telefone</th><th>Login</th><th>CPF (Hash LGPD)</th><th>Ações</th></tr>
        {linhas}
    </table>
    """


@app.post("/clientes/criar")
def criar_cliente(
    nome: str = Form(),
    telefone: str = Form(),
    cpf: str = Form(),
    login: str = Form(),
    senha: str = Form(),
):
    conn = get_db()
    # Item 5.4: Criptografa CPF e Senha antes de persistir no banco
    conn.execute(
        "INSERT INTO cliente (nome, telefone, cpf, login, senha) VALUES (?, ?, ?, ?, ?)",
        (nome, telefone, criptografar(cpf), login, criptografar(senha)),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/clientes", status_code=303)


@app.post("/clientes/editar")
def editar_cliente(
    id: int = Form(),
    nome: str = Form(),
    telefone: str = Form(),
    login: str = Form(),
):
    # Item 5.5: Atualiza dados do cliente existente
    conn = get_db()
    conn.execute(
        "UPDATE cliente SET nome = ?, telefone = ?, login = ? WHERE id = ?",
        (nome, telefone, login, id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/clientes", status_code=303)


@app.get("/clientes/excluir/{id}")
def excluir_cliente(id: int):
    # Item 5.1: Excluir registro de cliente
    conn = get_db()
    conn.execute("DELETE FROM cliente WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/clientes", status_code=303)


# =====================================================================
# ATIVIDADE 6: GERENCIAMENTO DE VEÍCULOS (Item 6.1)
# =====================================================================
@app.get("/veiculos", response_class=HTMLResponse)
def listar_veiculos():
    conn = get_db()
    clientes = conn.execute("SELECT id, nome FROM cliente").fetchall()
    veiculos = conn.execute("""
        SELECT v.id, v.modelo, v.marca, c.nome AS cliente_nome
        FROM veiculo v JOIN cliente c ON v.cliente_id = c.id
    """).fetchall()
    conn.close()

    opcoes_cliente = "".join([f"<option value='{c['id']}'>{c['nome']}</option>" for c in clientes])
    linhas = "".join([
        f"<tr><td>{v['id']}</td><td>{v['modelo']}</td><td>{v['marca']}</td><td>{v['cliente_nome']}</td></tr>"
        for v in veiculos
    ])

    return f"""
    <p><a href="/principal">Voltar para Principal</a></p>
    <h2>Gerenciamento de Veículos</h2>

    <!-- Item 6.1: Inserir novo veículo associando-o a um cliente no banco -->
    <h3>Novo Veículo</h3>
    <form method="post" action="/veiculos/criar">
        Modelo do Veículo: <input name="modelo" required>
        Marca: <input name="marca" required>
        Cliente: <select name="cliente_id" required>{opcoes_cliente}</select>
        <button type="submit">Cadastrar Veículo</button>
    </form>
    <hr>
    <table border="1" cellpadding="5">
        <tr><th>ID</th><th>Modelo do Veículo</th><th>Marca</th><th>Cliente Associado</th></tr>
        {linhas}
    </table>
    """


@app.post("/veiculos/criar")
def criar_veiculo(modelo: str = Form(), marca: str = Form(), cliente_id: int = Form()):
    conn = get_db()
    conn.execute(
        "INSERT INTO veiculo (modelo, marca, cliente_id) VALUES (?, ?, ?)",
        (modelo, marca, cliente_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/veiculos", status_code=303)


# =====================================================================
# ATIVIDADE 7: GERENCIAMENTO DE AGENDAMENTOS (Itens 7.1 e 7.2)
# =====================================================================
@app.get("/agendamentos", response_class=HTMLResponse)
def listar_agendamentos():
    conn = get_db()
    veiculos = conn.execute("SELECT id, modelo FROM veiculo").fetchall()

    # Item 7.1: Listar agendamentos ordenado por data, trazendo dados do cliente e do veículo
    agendamentos = conn.execute("""
        SELECT a.id, a.data_agendamento, a.servico,
               v.modelo AS veiculo_modelo, v.marca AS veiculo_marca,
               c.nome AS cliente_nome, c.telefone AS cliente_telefone
        FROM agendamento a
        JOIN veiculo v ON a.veiculo_id = v.id
        JOIN cliente c ON v.cliente_id = c.id
        ORDER BY a.data_agendamento ASC
    """).fetchall()
    conn.close()

    opcoes_veiculo = "".join([f"<option value='{v['id']}'>{v['modelo']}</option>" for v in veiculos])
    linhas = ""
    for a in agendamentos:
        # Item 7.2: Atualizar a data de um agendamento existente
        linhas += f"""
        <tr>
            <td>{a['id']}</td>
            <td>
                <form method="post" action="/agendamentos/atualizar" style="margin:0;">
                    <input type="hidden" name="id" value="{a['id']}">
                    <input type="date" name="data_agendamento" value="{a['data_agendamento']}" required>
                    <button type="submit">Atualizar Data</button>
                </form>
            </td>
            <td>{a['servico']}</td>
            <td>{a['veiculo_modelo']} ({a['veiculo_marca']})</td>
            <td>{a['cliente_nome']} - Tel: {a['cliente_telefone']}</td>
        </tr>
        """

    return f"""
    <p><a href="/principal">Voltar para Principal</a></p>
    <h2>Gerenciamento de Agendamentos</h2>

    <h3>Novo Agendamento</h3>
    <form method="post" action="/agendamentos/criar">
        Data: <input type="date" name="data_agendamento" required>
        Serviço: <input name="servico" required>
        Veículo: <select name="veiculo_id" required>{opcoes_veiculo}</select>
        <button type="submit">Agendar</button>
    </form>
    <hr>
    <table border="1" cellpadding="5">
        <tr><th>ID</th><th>Data (Ordenada)</th><th>Serviço</th><th>Dados do Veículo</th><th>Dados do Cliente</th></tr>
        {linhas}
    </table>
    """


@app.post("/agendamentos/criar")
def criar_agendamento(data_agendamento: str = Form(), servico: str = Form(), veiculo_id: int = Form()):
    conn = get_db()
    conn.execute(
        "INSERT INTO agendamento (data_agendamento, servico, veiculo_id) VALUES (?, ?, ?)",
        (data_agendamento, servico, veiculo_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/agendamentos", status_code=303)


@app.post("/agendamentos/atualizar")
def atualizar_data_agendamento(id: int = Form(), data_agendamento: str = Form()):
    # Item 7.2: Atualiza a data de um agendamento
    conn = get_db()
    conn.execute(
        "UPDATE agendamento SET data_agendamento = ? WHERE id = ?",
        (data_agendamento, id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/agendamentos", status_code=303)
