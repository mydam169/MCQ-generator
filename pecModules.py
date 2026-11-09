"""Economic models and multiple-choice helpers for the exam templates.

Models
------
- ``LinearDSModel``: linear supply and demand, equilibrium and surpluses.
- ``TaxModel``: per-unit tax, new equilibrium, tax revenue, deadweight loss.
- ``PriceFloor`` / ``PriceCeiling``: binding price controls.
- ``Monopole``: monopoly with linear demand and constant marginal cost, plus
  the symmetric Cournot duopoly outcome.

Helpers
-------
- ``shuffleAnswer``: build six distinct, shuffled answer options.
- ``printAnswer``: print the answer-key line of a question.
- ``computeElasticity``, ``computeCS``, ``computePS``.
"""
from typing import Optional

import numpy as np
import pandas as pd


class LinearDSModel:
    """Linear supply and demand model.

    Inverse demand: P = a + bQ (b < 0). Inverse supply: P = c + dQ (d > 0).
    Equilibrium: Q* = (a - c) / (d - b), P* = a + bQ*.
    """

    def __init__(self, demand_intercept: float, demand_slope: float,
                 supply_intercept: float, supply_slope: float):
        # Assign through the setters so the constructor and the setters
        # apply exactly the same validation.
        self.demand_intercept = demand_intercept
        self.demand_slope = demand_slope
        self.supply_intercept = supply_intercept
        self.supply_slope = supply_slope

    @property
    def q_star(self) -> float:
        """Equilibrium quantity."""
        return (self._a - self._c) / (self._d - self._b)

    @property
    def p_star(self) -> float:
        """Equilibrium price."""
        return self._a + self._b * self.q_star

    @property
    def TS_star(self) -> float:
        """Total surplus at the competitive equilibrium."""
        return (self._a - self._c) * self.q_star * 0.5

    @property
    def demand_intercept(self) -> float:
        return self._a

    @demand_intercept.setter
    def demand_intercept(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Demand intercept must be positive")
        self._a = value

    @property
    def demand_slope(self) -> float:
        return self._b

    @demand_slope.setter
    def demand_slope(self, value: float) -> None:
        if value >= 0:
            raise ValueError("Demand slope must be negative")
        self._b = value

    @property
    def supply_intercept(self) -> float:
        return self._c

    @supply_intercept.setter
    def supply_intercept(self, value: float) -> None:
        if value < 0:
            raise ValueError("Supply intercept must be non-negative")
        if value >= self._a:
            raise ValueError("Supply intercept must be less than demand intercept")
        self._c = value

    @property
    def supply_slope(self) -> float:
        return self._d

    @supply_slope.setter
    def supply_slope(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Supply slope must be positive")
        self._d = value

    def get_P_demand(self, quantity: float) -> float:
        """Price buyers are willing to pay for ``quantity``."""
        return self._a + self._b * quantity

    def get_P_supply(self, quantity: float) -> float:
        """Price sellers require to supply ``quantity``."""
        return self._c + self._d * quantity

    def get_Q_demand(self, price: float) -> float:
        """Quantity demanded at ``price``."""
        return (price - self._a) / self._b

    def get_Q_supply(self, price: float) -> float:
        """Quantity supplied at ``price``."""
        return (price - self._c) / self._d

    def get_CS(self, quantity_bought: float, price_paid: float) -> float:
        """Consumer surplus when buyers pay the demand price for ``quantity_bought``."""
        return 0.5 * (self._a - price_paid) * quantity_bought

    def get_PS(self, quantity_sold: float, price_received: float) -> float:
        """Producer surplus when sellers receive the supply price for ``quantity_sold``."""
        return 0.5 * (price_received - self._c) * quantity_sold


class TaxModel(LinearDSModel):
    """Linear market with a per-unit tax that drives a wedge between P_d and P_s."""

    def __init__(self, demand_intercept: float, demand_slope: float,
                 supply_intercept: float, supply_slope: float,
                 tax_size: Optional[float] = None):
        super().__init__(demand_intercept, demand_slope, supply_intercept, supply_slope)
        self.tax = None
        if tax_size is not None:
            self.tax_size = tax_size

    @property
    def tax_size(self) -> float:
        return self.tax

    @tax_size.setter
    def tax_size(self, value: float) -> None:
        # A tax larger than a - c would shut the market down entirely.
        self.tax = min(value, self._a - self._c)

    @property
    def q_T(self) -> float:
        """Quantity traded with the tax."""
        return (self._a - self._c - self.tax) / (self._d - self._b)

    @property
    def P_d(self) -> float:
        """Price paid by buyers (tax included)."""
        return self.get_P_demand(self.q_T)

    @property
    def P_s(self) -> float:
        """Price received by sellers."""
        return self.get_P_supply(self.q_T)

    @property
    def DWL_T(self) -> float:
        """Deadweight loss of the tax."""
        return 0.5 * (self.q_star - self.q_T) * self.tax

    @property
    def tax_rev(self) -> float:
        """Tax revenue."""
        return self.q_T * self.tax

    @property
    def CS_T(self) -> float:
        """Consumer surplus with the tax."""
        return (self._a - self.P_d) * self.q_T * 0.5

    @property
    def PS_T(self) -> float:
        """Producer surplus with the tax."""
        return self.get_PS(self.q_T, self.P_s)


class PriceFloor(LinearDSModel):
    """Linear market with a minimum price set above the equilibrium price."""

    def __init__(self, demand_intercept: float, demand_slope: float,
                 supply_intercept: float, supply_slope: float,
                 floor: Optional[float] = None):
        """``floor`` is the markup over P*: the floor is (1 + floor) * P*."""
        super().__init__(demand_intercept, demand_slope, supply_intercept, supply_slope)
        if floor is not None:
            self.price_floor = floor

    @property
    def price_floor(self) -> float:
        return self.p_min

    @price_floor.setter
    def price_floor(self, markup: float) -> None:
        self.p_min = (1 + markup) * self.p_star

    @property
    def q_floor(self) -> float:
        """Quantity traded (set by demand at the floor price)."""
        return max(self.get_Q_demand(self.p_min), 0)

    @property
    def q_excess(self) -> float:
        """Excess supply at the floor price."""
        return self.get_Q_supply(self.p_min) - self.q_floor

    @property
    def DWL_floor(self) -> float:
        """Deadweight loss of the price floor."""
        return min(0.5 * (self.p_min - self.get_P_supply(self.q_floor)) * (self.q_star - self.q_floor),
                   self.TS_star)

    @property
    def CS_floor(self) -> float:
        """Consumer surplus with the price floor."""
        return self.get_CS(self.q_floor, self.p_min)

    @property
    def PS_floor(self) -> float:
        """Producer surplus with the price floor."""
        return self.TS_star - self.CS_floor - self.DWL_floor


class PriceCeiling(LinearDSModel):
    """Linear market with a maximum price set below the equilibrium price."""

    def __init__(self, demand_intercept: float, demand_slope: float,
                 supply_intercept: float, supply_slope: float,
                 ceiling: Optional[float] = None):
        """``ceiling`` is a fraction of P* in (0, 1]: the ceiling is ceiling * P*."""
        super().__init__(demand_intercept, demand_slope, supply_intercept, supply_slope)
        if ceiling is not None:
            self.price_ceiling = ceiling

    @property
    def price_ceiling(self) -> float:
        return self.p_max

    @price_ceiling.setter
    def price_ceiling(self, ceiling_percent: float) -> None:
        if ceiling_percent > 1:
            raise ValueError("Must be a value between zero and one")
        self.p_max = self.p_star * ceiling_percent

    @property
    def q_ceiling(self) -> float:
        """Quantity traded (set by supply at the ceiling price)."""
        return max(self.get_Q_supply(self.p_max), 0)

    @property
    def q_shortage(self) -> float:
        """Excess demand at the ceiling price."""
        return self.get_Q_demand(self.p_max) - self.q_ceiling

    @property
    def DWL_ceiling(self) -> float:
        """Deadweight loss of the price ceiling."""
        return min(0.5 * (self.get_P_demand(self.q_ceiling) - self.p_max) * (self.q_star - self.q_ceiling),
                   self.TS_star)

    @property
    def PS_ceiling(self) -> float:
        """Producer surplus with the price ceiling."""
        return self.get_PS(self.q_ceiling, self.p_max)

    @property
    def CS_ceiling(self) -> float:
        """Consumer surplus with the price ceiling."""
        return self.TS_star - self.PS_ceiling - self.DWL_ceiling


# Distractors are these multiples of the correct answer (1.0 is not included).
DISTRACTOR_MULTIPLES = np.arange(0.5, 2.0, 0.15)
OPTION_LABELS = ['(A)', '(B)', '(C)', '(D)', '(E)', '(F)']


def shuffleAnswer(correctAnswer: float, rng: np.random.Generator) -> pd.DataFrame:
    """Return six distinct, shuffled answer options plus "(G) Autre".

    The five distractors are distinct multiples (0.5x to 1.85x) of the correct
    answer, rounded to two decimals. If rounding or a zero answer makes some of
    them coincide, they are replaced by offsets from the correct answer, so the
    six options are always distinct. All randomness comes from ``rng``.
    """
    correct = round(float(correctAnswer), 2)
    n_wrong = len(OPTION_LABELS) - 1
    candidates = np.round(rng.choice(DISTRACTOR_MULTIPLES, size=n_wrong, replace=False) * correct, 2)

    wrong = []
    for value in candidates:
        value = float(value)
        if value != correct and value not in wrong:
            wrong.append(value)

    # Degenerate cases only (zero or very small answers): deterministic offsets.
    step = max(round(abs(correct) * 0.15, 2), 0.01) if correct != 0 else 1.0
    sign = 1 if correct >= 0 else -1
    k = 1
    while len(wrong) < n_wrong:
        value = round(correct + sign * k * step, 2)
        if value != correct and value not in wrong:
            wrong.append(value)
        k += 1

    all_answers = np.array(wrong + [correct])
    rng.shuffle(all_answers)
    choices = {label: [value] for label, value in zip(OPTION_LABELS, all_answers)}
    choices['(G)'] = ['Autre']
    return pd.DataFrame(choices, index=[''])


def printAnswer(question) -> None:
    """Print the answer-key line of a question, e.g. "Bonne réponse : (D) 3.48"."""
    print(question.answer_text)


def computeElasticity(initP: float, finalP: float, initQ: float, finalQ: float) -> float:
    """Price elasticity between two points, using the midpoint (arc) formula."""
    midP = (initP + finalP) / 2
    midQ = (initQ + finalQ) / 2
    deltaP = finalP - initP
    deltaQ = finalQ - initQ
    eps = (deltaQ / midQ) / (deltaP / midP)
    return round(eps, 2)


def computeCS(demand_intercept: float, demand_slope: float,
              price_paid: float, qty_bought: float) -> float:
    """Consumer surplus for inverse demand P = a - bQ (``demand_slope`` = b > 0).

    Area between the demand curve and ``price_paid`` from 0 to ``qty_bought``.
    """
    cs = (demand_intercept - price_paid) * qty_bought - 0.5 * demand_slope * (qty_bought ** 2)
    return round(cs, 2)


def computePS(supply_intercept: float, supply_slope: float,
              price_received: float, qty_sold: float) -> float:
    """Producer surplus for inverse supply P = c + dQ.

    Area between ``price_received`` and the supply curve from 0 to ``qty_sold``.
    """
    ps = (price_received - supply_intercept) * qty_sold - 0.5 * supply_slope * (qty_sold ** 2)
    return round(ps, 2)


class Monopole:
    """Monopoly with inverse demand p = a - bq and cost C(q) = cq + F.

    Also gives the symmetric Cournot duopoly outcome for two identical firms.
    """

    def __init__(self, demand_int: float, demand_slope: float, marginal_cost: float,
                 fixed_cost: float):
        """``demand_slope`` is b > 0 in p = a - bq.

        Raises ``ValueError`` if the fixed cost exceeds the maximum profit
        before fixed costs, (a - c)^2 / (4b).
        """
        if marginal_cost < 0:
            raise ValueError('Marginal cost must be non-negative')
        if demand_slope <= 0:
            raise ValueError('Demand slope in absolute value must be positive')
        if demand_int <= marginal_cost:
            raise ValueError('Demand intercept must be greater than marginal cost')
        self.demand_int = demand_int
        self.demand_sl = demand_slope
        self.mc = marginal_cost
        # Maximum profit before fixed costs: (a - c)^2 / (4b).
        max_profit = (demand_int - marginal_cost) ** 2 / (4 * demand_slope)
        if fixed_cost > max_profit:
            raise ValueError(
                f"Fixed cost {fixed_cost} exceeds the maximum operating profit "
                f"{max_profit:.2f}; profit after fixed costs would be negative"
            )
        self.fc = fixed_cost

    def MR(self, quantity: float) -> float:
        """Marginal revenue at ``quantity``."""
        return self.demand_int - 2 * self.demand_sl * quantity

    @property
    def Q_mon(self) -> float:
        """Monopoly quantity (MR = MC)."""
        return (self.demand_int - self.mc) / (2 * self.demand_sl)

    @property
    def P_mon(self) -> float:
        """Monopoly price."""
        return self.demand_int - self.demand_sl * self.Q_mon

    @property
    def Profit_mon(self) -> float:
        """Monopoly profit after fixed costs."""
        profit = self.P_mon * self.Q_mon - self.Q_mon * self.mc - self.fc
        return max(profit, 0)

    @property
    def PS_mon(self) -> float:
        """Producer surplus (operating profit before fixed costs)."""
        return (self.P_mon - self.mc) * self.Q_mon

    @property
    def DWL_mon(self) -> float:
        """Deadweight loss of monopoly relative to the efficient quantity."""
        return self.PS_mon / 2

    @property
    def CS_mon(self) -> float:
        """Consumer surplus under monopoly."""
        return (self.demand_int - self.P_mon) * self.Q_mon / 2

    @property
    def q_duo(self) -> float:
        """Quantity produced by each firm in a symmetric Cournot duopoly."""
        return (2 / 3) * self.Q_mon

    @property
    def P_duo(self) -> float:
        """Market price in the Cournot duopoly (total output 2 * q_duo)."""
        return self.demand_int - 2 * self.demand_sl * self.q_duo
