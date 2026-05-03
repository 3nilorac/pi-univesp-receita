import os
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Receita, Medicamento

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
    paciente_nome = request.form.get("paciente_nome", "").strip()

    med_nomes = request.form.getlist("med_nome[]")
    med_concentracoes = request.form.getlist("med_concentracao[]")
    med_posologias = request.form.getlist("med_posologia[]")

    if not vet_nome or not vet_crmv or not tutor_nome or not paciente_nome:
        flash("Preencha todos os campos obrigatórios (Veterinário, CRMV, Tutor e Paciente).", "error")
        return redirect(url_for("index"))

    meds_validos = [
        (n.strip(), c.strip(), p.strip())
        for n, c, p in zip(med_nomes, med_concentracoes, med_posologias)
        if n.strip() and p.strip()
    ]

    if not meds_validos:
        flash("Adicione pelo menos um medicamento com nome e posologia.", "error")
        return redirect(url_for("index"))

    receita = Receita(
        vet_nome=vet_nome,
        vet_crmv=vet_crmv,
        vet_telefone=request.form.get("vet_telefone", "").strip(),
        tutor_nome=tutor_nome,
        tutor_cpf=request.form.get("tutor_cpf", "").strip(),
        tutor_telefone=request.form.get("tutor_telefone", "").strip(),
        paciente_nome=paciente_nome,
        paciente_especie=request.form.get("paciente_especie", "").strip(),
        paciente_raca=request.form.get("paciente_raca", "").strip(),
        paciente_peso=request.form.get("paciente_peso", "").strip(),
    )

    for nome, concentracao, posologia in meds_validos:
        receita.medicamentos.append(
            Medicamento(nome=nome, concentracao=concentracao, posologia=posologia)
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
