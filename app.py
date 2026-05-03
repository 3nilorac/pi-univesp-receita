import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Receita, Medicamento


UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for i in range(9, 11):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if int(cpf[i]) != digito:
            return False

    return True


def validar_telefone(telefone: str) -> bool:
    if not telefone:
        return True
    digits = re.sub(r"\D", "", telefone)
    if len(digits) == 10:
        return digits[0:2] >= "11"
    if len(digits) == 11:
        return digits[0:2] >= "11" and digits[2] == "9"
    return False


def validar_crmv(crmv: str) -> bool:
    crmv = crmv.strip()
    match = re.match(r"^(\d{3,6})\s*/\s*([A-Za-z]{2})$", crmv)
    if not match:
        return False
    return match.group(2).upper() in UFS_VALIDAS

app = Flask(__name__)
app.secret_key = os.urandom(24)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "receitas.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/receitas", methods=["POST"])
def criar_receita():
    vet_nome = request.form.get("vet_nome", "").strip()
    vet_crmv = request.form.get("vet_crmv", "").strip()
    tutor_nome = request.form.get("tutor_nome", "").strip()
    tutor_cpf = request.form.get("tutor_cpf", "").strip()
    paciente_nome = request.form.get("paciente_nome", "").strip()

    med_nomes = request.form.getlist("med_nome[]")
    med_concentracoes = request.form.getlist("med_concentracao[]")
    med_modos_uso = request.form.getlist("med_modo_uso[]")
    med_posologias = request.form.getlist("med_posologia[]")

    if not vet_nome or not vet_crmv or not tutor_nome or not tutor_cpf or not paciente_nome:
        flash("Preencha todos os campos obrigatórios (Veterinário, CRMV, Tutor, CPF e Paciente).", "error")
        return redirect(url_for("index"))

    if not validar_crmv(vet_crmv):
        flash("CRMV inválido. Use o formato número/UF (ex: 12345/SP).", "error")
        return redirect(url_for("index"))

    if not validar_cpf(tutor_cpf):
        flash("CPF inválido. Verifique os dígitos informados.", "error")
        return redirect(url_for("index"))

    vet_telefone = request.form.get("vet_telefone", "").strip()
    tutor_telefone = request.form.get("tutor_telefone", "").strip()

    if not validar_telefone(vet_telefone):
        flash("Telefone do veterinário inválido. Use (DD) XXXX-XXXX ou (DD) 9XXXX-XXXX.", "error")
        return redirect(url_for("index"))

    if not validar_telefone(tutor_telefone):
        flash("Telefone do tutor inválido. Use (DD) XXXX-XXXX ou (DD) 9XXXX-XXXX.", "error")
        return redirect(url_for("index"))

    meds_validos = [
        (n.strip(), c.strip(), m.strip(), p.strip())
        for n, c, m, p in zip(med_nomes, med_concentracoes, med_modos_uso, med_posologias)
        if n.strip() and p.strip()
    ]

    if not meds_validos:
        flash("Adicione pelo menos um medicamento com nome e posologia.", "error")
        return redirect(url_for("index"))

    receita = Receita(
        vet_nome=vet_nome,
        vet_crmv=vet_crmv,
        vet_telefone=vet_telefone,
        tutor_nome=tutor_nome,
        tutor_cpf=tutor_cpf,
        tutor_telefone=tutor_telefone,
        paciente_nome=paciente_nome,
        paciente_especie=request.form.get("paciente_especie", "").strip(),
        paciente_raca=request.form.get("paciente_raca", "").strip(),
        paciente_peso=request.form.get("paciente_peso", "").strip(),
    )

    for nome, concentracao, modo_uso, posologia in meds_validos:
        receita.medicamentos.append(
            Medicamento(nome=nome, concentracao=concentracao, modo_uso=modo_uso, posologia=posologia)
        )

    db.session.add(receita)
    db.session.commit()

    flash("Receita salva com sucesso!", "success")
    return redirect(url_for("ver_receita", id=receita.id))


@app.route("/receitas")
def listar_receitas():
    receitas = Receita.query.order_by(Receita.data_emissao.desc()).all()
    return render_template("receitas.html", receitas=receitas)


@app.route("/receitas/<int:id>")
def ver_receita(id):
    receita = db.get_or_404(Receita, id)
    return render_template("receita.html", receita=receita)


@app.route("/receitas/<int:id>/excluir", methods=["POST"])
def excluir_receita(id):
    receita = db.get_or_404(Receita, id)
    db.session.delete(receita)
    db.session.commit()
    flash("Receita excluída com sucesso.", "success")
    return redirect(url_for("listar_receitas"))


if __name__ == "__main__":
    app.run(debug=True)
