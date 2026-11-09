"""Build one complete exam version from its version number.

All randomness for a version (model parameters, distractors and the order of
the answer options) comes from a single generator seeded with the version
number. Both Quarto templates (the student copy and the answer key) call
``build_exam`` and only *display* its results, so the two documents always
show identical options in identical order.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

import pecModules as mods


@dataclass(frozen=True)
class Question:
    """A multiple-choice question: its correct value and its option table."""

    value: float
    options: pd.DataFrame

    @property
    def letter(self) -> str:
        """Label of the option holding the correct value, e.g. ``'(D)'``."""
        for label, option in self.options.iloc[0].items():
            if option == self.value:
                return label
        raise ValueError(f"Correct value {self.value} not found among the options")

    @property
    def answer_text(self) -> str:
        """Answer-key line, e.g. ``'Bonne réponse : (D) 3.48'``."""
        return f"Bonne réponse : {self.letter} {self.value}"


@dataclass(frozen=True)
class MarketParams:
    """Linear market: inverse demand P = a - bQ, inverse supply P = c + dQ."""

    a: int
    b: float
    c: float
    d: float


@dataclass(frozen=True)
class MonopolyParams:
    """Monopoly: inverse demand p = a - bq, cost C(q) = cq + fc."""

    a: int
    b: float
    c: int
    fc: int


@dataclass(frozen=True)
class Exam:
    """All parameters and questions of one exam version."""

    sujet: int
    market: MarketParams
    monopoly: MonopolyParams
    questions: dict

    def __getitem__(self, key: str) -> Question:
        return self.questions[key]


def build_exam(sujet_number: int) -> Exam:
    """Draw the parameters and build every question of version ``sujet_number``.

    The same version number always yields the same exam.
    """
    rng = np.random.default_rng(sujet_number)
    questions = {}

    def ask(key: str, value: float) -> None:
        value = round(float(value), 2)
        questions[key] = Question(value, mods.shuffleAnswer(value, rng))

    # --- Supply and demand --------------------------------------------------
    a = int(round(rng.choice(np.arange(50.0, 200.0, 10.0))))
    b = round(float(rng.choice(np.arange(1.25, 15.0, 1.0))), 2)
    c = round(float(rng.choice(np.arange(0.5, 20.0, 1.0))), 2)
    d = round(float(rng.choice(np.arange(1.15, 20.0, 2.0))), 2)
    market = MarketParams(a, b, c, d)

    ds_model = mods.LinearDSModel(a, -b, c, d)
    qstar = round(ds_model.q_star, 2)
    pstar = round(ds_model.p_star, 2)
    ask("qstar", qstar)
    ask("pstar", pstar)
    ask("cs_star", ds_model.get_CS(qstar, pstar))
    ask("ps_star", ds_model.get_PS(qstar, pstar))

    # --- Taxation and price elasticity --------------------------------------
    # Tax levied on buyers, equal to 20% of the initial equilibrium price.
    tax = 0.2 * pstar
    tax_model = mods.TaxModel(a, -b, c, d, tax_size=tax)
    q_tax = round(tax_model.q_T, 2)
    p_sellers = round(tax_model.P_s, 2)
    p_buyers = round(tax_model.P_d, 2)
    ask("p_tax", p_sellers)
    ask("q_tax", q_tax)
    ask("dwl_tax", tax_model.DWL_T)
    ask("elasticity", np.abs(mods.computeElasticity(p_sellers, pstar, q_tax, qstar)))
    # Optional tax-incidence questions (disabled in the templates by default).
    burden_buyers = (p_buyers - pstar) / tax
    ask("incidence_buyers", burden_buyers)
    ask("incidence_buyers_if_sellers_taxed", burden_buyers)

    # --- Price ceiling and price floor (market shrinks by 30%) --------------
    q_new = 0.7 * qstar
    price_ceiling = round(c + d * q_new, 2)
    ask("price_ceiling", price_ceiling)
    ask("cs_ceiling", mods.computeCS(a, b, price_ceiling, q_new))
    ask("ps_ceiling", mods.computePS(c, d, price_ceiling, q_new))
    price_floor = round(a - b * q_new, 2)
    ask("price_floor", price_floor)
    ask("cs_floor", mods.computeCS(a, b, price_floor, q_new))
    ask("ps_floor", mods.computePS(c, d, price_floor, q_new))

    # --- Monopoly -----------------------------------------------------------
    ma = int(round(rng.choice(np.arange(250.0, 500.0, 10.0))))
    mb = round(float(rng.choice(np.arange(1.25, 15.0, 1.0))), 2)
    mc = int(round(rng.choice(np.arange(10.0, 200.0, 20.0))))
    max_fixed_cost = (ma - mc) ** 2 / (4 * mb)
    fc = int(round(rng.uniform(0.1, 0.95) * max_fixed_cost))
    monopoly = MonopolyParams(ma, mb, mc, fc)

    mon = mods.Monopole(ma, mb, mc, fc)
    q_mon = round(mon.Q_mon, 2)
    ask("q_mon", q_mon)
    ask("p_mon", mon.P_mon)
    ask("profit_mon", mon.Profit_mon)
    ask("q_efficient", q_mon * 2)
    ask("dwl_mon", mon.DWL_mon)

    # --- Cournot duopoly ----------------------------------------------------
    ask("q_duo", mon.q_duo)
    ask("p_duo", mon.P_duo)

    return Exam(sujet_number, market, monopoly, questions)
