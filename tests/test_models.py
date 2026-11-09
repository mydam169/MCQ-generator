"""Unit tests for the economic models, checked against hand-computed values."""
import numpy as np
import pytest

import pecModules as mods
from exam import build_exam


# --- Supply and demand ------------------------------------------------------

def test_equilibrium_example_from_course():
    # P = 70 - 10.25Q, P = 2.5 + 9.15Q  ->  Q* = 67.5 / 19.4, P* = 70 - 10.25 Q*
    model = mods.LinearDSModel(70, -10.25, 2.5, 9.15)
    assert model.q_star == pytest.approx(3.4794, abs=1e-4)
    assert model.p_star == pytest.approx(34.3363, abs=1e-4)
    assert model.get_CS(model.q_star, model.p_star) == pytest.approx(62.04, abs=0.01)
    assert model.get_PS(model.q_star, model.p_star) == pytest.approx(55.39, abs=0.01)


@pytest.fixture
def simple_market():
    # P = 100 - 2Q, P = 10 + Q  ->  Q* = 30, P* = 40, CS = 900, PS = 450
    return mods.LinearDSModel(100, -2, 10, 1)


def test_simple_equilibrium_and_surplus(simple_market):
    m = simple_market
    assert m.q_star == pytest.approx(30)
    assert m.p_star == pytest.approx(40)
    assert m.get_CS(30, 40) == pytest.approx(900)
    assert m.get_PS(30, 40) == pytest.approx(450)
    assert m.TS_star == pytest.approx(1350)


def test_supply_intercept_validation_is_consistent():
    model = mods.LinearDSModel(100, -2, 0, 1)  # 0 allowed in the constructor
    model.supply_intercept = 0                 # ... and in the setter
    with pytest.raises(ValueError):
        model.supply_intercept = -1
    with pytest.raises(ValueError):
        mods.LinearDSModel(100, -2, -1, 1)
    with pytest.raises(ValueError):
        model.supply_intercept = 100
    with pytest.raises(ValueError):
        mods.LinearDSModel(100, -2, 100, 1)


# --- Taxation ---------------------------------------------------------------

def test_tax_incidence_revenue_and_deadweight_loss():
    # Tax of 6: Q_T = (90 - 6) / 3 = 28, P_d = 44, P_s = 38
    tax = mods.TaxModel(100, -2, 10, 1, tax_size=6)
    assert tax.q_T == pytest.approx(28)
    assert tax.P_d == pytest.approx(44)
    assert tax.P_s == pytest.approx(38)
    assert tax.tax_rev == pytest.approx(168)
    assert tax.DWL_T == pytest.approx(6)
    assert tax.CS_T == pytest.approx(784)
    assert tax.PS_T == pytest.approx(392)
    # Buyers bear |b| / (|b| + d) = 2/3 of the tax.
    assert (tax.P_d - tax.p_star) / 6 == pytest.approx(2 / 3)
    # Surplus is conserved: CS + PS + revenue + DWL = initial total surplus.
    assert tax.CS_T + tax.PS_T + tax.tax_rev + tax.DWL_T == pytest.approx(tax.TS_star)


def test_tax_is_capped_at_choke_level():
    tax = mods.TaxModel(100, -2, 10, 1, tax_size=500)
    assert tax.tax_size == 90
    assert tax.q_T == pytest.approx(0)


def test_elasticity_midpoint_formula():
    # P: 10 -> 12, Q: 20 -> 16  ->  (-4 / 18) / (2 / 11) = -1.22
    assert mods.computeElasticity(10, 12, 20, 16) == pytest.approx(-1.22)


# --- Price controls (market reduced by 30%: Q = 21) -------------------------

def test_price_ceiling():
    ceiling = mods.PriceCeiling(100, -2, 10, 1, ceiling=31 / 40)
    assert ceiling.price_ceiling == pytest.approx(31)
    assert ceiling.q_ceiling == pytest.approx(21)
    assert ceiling.q_shortage == pytest.approx(13.5)
    assert ceiling.DWL_ceiling == pytest.approx(121.5)
    assert ceiling.PS_ceiling == pytest.approx(220.5)
    assert ceiling.CS_ceiling == pytest.approx(1008)
    # The formulas used by the exam agree with the class.
    assert mods.computeCS(100, 2, 31, 21) == pytest.approx(1008)
    assert mods.computePS(10, 1, 31, 21) == pytest.approx(220.5)


def test_price_floor():
    floor = mods.PriceFloor(100, -2, 10, 1, floor=0.45)
    assert floor.price_floor == pytest.approx(58)
    assert floor.q_floor == pytest.approx(21)
    assert floor.q_excess == pytest.approx(27)
    assert floor.DWL_floor == pytest.approx(121.5)
    assert floor.CS_floor == pytest.approx(441)
    assert floor.PS_floor == pytest.approx(787.5)
    assert mods.computeCS(100, 2, 58, 21) == pytest.approx(441)
    assert mods.computePS(10, 1, 58, 21) == pytest.approx(787.5)


# --- Monopoly and Cournot duopoly -------------------------------------------

@pytest.fixture
def monopoly():
    # p = 100 - 2q, C(q) = 20q + 500; max profit before fixed costs = 80^2 / 8 = 800
    return mods.Monopole(100, 2, 20, 500)


def test_monopoly_outcomes(monopoly):
    assert monopoly.Q_mon == pytest.approx(20)
    assert monopoly.P_mon == pytest.approx(60)
    assert monopoly.MR(monopoly.Q_mon) == pytest.approx(monopoly.mc)
    assert monopoly.Profit_mon == pytest.approx(300)
    assert monopoly.PS_mon == pytest.approx(800)
    assert monopoly.CS_mon == pytest.approx(400)
    # DWL = 0.5 * (P_mon - MC) * (Q_efficient - Q_mon) = 0.5 * 40 * 20
    assert monopoly.DWL_mon == pytest.approx(400)


def test_cournot_duopoly(monopoly):
    # q_i = (a - c) / (3b) = 40 / 3, P = (a + 2c) / 3 = 140 / 3
    assert monopoly.q_duo == pytest.approx(40 / 3)
    assert monopoly.P_duo == pytest.approx(140 / 3)


def test_monopoly_fixed_cost_used_unchanged_or_rejected():
    assert mods.Monopole(100, 2, 20, 10).fc == 10
    assert mods.Monopole(100, 2, 20, 800).Profit_mon == pytest.approx(0)
    with pytest.raises(ValueError):
        mods.Monopole(100, 2, 20, 801)


# --- Answer options and exam versions ---------------------------------------

@pytest.mark.parametrize("value", [3.48, 0, 0.01, 0.05, 1234.5, -2.5])
def test_shuffle_answer_gives_six_distinct_options(value):
    options = mods.shuffleAnswer(value, np.random.default_rng(0))
    values = list(options.iloc[0])
    assert values[-1] == 'Autre'
    assert len(set(values[:6])) == 6
    assert round(value, 2) in values[:6]


def test_shuffle_answer_is_reproducible():
    a = mods.shuffleAnswer(3.48, np.random.default_rng(7))
    b = mods.shuffleAnswer(3.48, np.random.default_rng(7))
    assert a.equals(b)


def test_same_version_gives_same_exam():
    a, b = build_exam(1), build_exam(1)
    assert a.market == b.market and a.monopoly == b.monopoly
    for key in a.questions:
        assert a[key].options.equals(b[key].options)
    assert build_exam(1).market != build_exam(2).market


@pytest.mark.parametrize("sujet", range(1, 101))
def test_every_question_has_distinct_options_and_a_valid_letter(sujet):
    exam = build_exam(sujet)
    for question in exam.questions.values():
        values = list(question.options.iloc[0])[:6]
        assert len(set(values)) == 6
        assert question.options.iloc[0][question.letter] == question.value
