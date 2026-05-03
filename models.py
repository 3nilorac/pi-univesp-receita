from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class Receita(db.Model):
    __tablename__ = "receitas"

    id = db.Column(db.Integer, primary_key=True)
    data_emissao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    vet_nome = db.Column(db.String(200), nullable=False)
    vet_crmv = db.Column(db.String(50), nullable=False)
    vet_telefone = db.Column(db.String(30), default="")

    tutor_nome = db.Column(db.String(200), nullable=False)
    tutor_cpf = db.Column(db.String(20), default="")
    tutor_telefone = db.Column(db.String(30), default="")

    paciente_nome = db.Column(db.String(100), nullable=False)
    paciente_especie = db.Column(db.String(50), default="")
    paciente_raca = db.Column(db.String(100), default="")
    paciente_peso = db.Column(db.String(20), default="")

    medicamentos = db.relationship(
        "Medicamento", backref="receita", cascade="all, delete-orphan", lazy=True
    )

    @property
    def data_formatada(self):
        return self.data_emissao.strftime("%d/%m/%Y")


class Medicamento(db.Model):
    __tablename__ = "medicamentos"

    id = db.Column(db.Integer, primary_key=True)
    receita_id = db.Column(db.Integer, db.ForeignKey("receitas.id"), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    concentracao = db.Column(db.String(200), default="")
    posologia = db.Column(db.Text, nullable=False)
