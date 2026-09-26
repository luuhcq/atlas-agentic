"""Moving weighted-average positions for one chronologically ordered asset.

Fees are intentionally excluded: no ADR or API_CONTRACT.md specifies their
cost-basis or P&L treatment; that decision is deferred rather than assumed.
"""

from dataclasses import dataclass
from decimal import Context, Decimal, Inexact, ROUND_HALF_EVEN, localcontext
from enum import Enum
from typing import Iterable


class TransactionType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class Transaction:
    type: TransactionType
    quantity: Decimal
    unit_price: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.type, TransactionType):
            raise ValueError("type must be a TransactionType")
        for name in ("quantity", "unit_price"):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{name} must be a Decimal")
            if not value.is_finite() or value <= 0:
                raise ValueError(f"{name} must be finite and positive")


@dataclass(frozen=True)
class Position:
    quantity: Decimal
    average_cost: Decimal
    realized_pnl: Decimal


class InsufficientPositionError(ValueError):
    """A sale would create a short position."""

    def __init__(self, requested: Decimal, held: Decimal) -> None:
        self.requested = requested
        self.held = held
        super().__init__(f"Cannot sell {requested} units: only {held} are held.")


def _add_exact(held: Decimal, amount: Decimal, *, subtract: bool = False) -> Decimal:
    """Size precision to retain every input digit, plus a possible carry."""
    exponent = min(held.as_tuple().exponent, amount.as_tuple().exponent)
    precision = max(held.adjusted(), amount.adjusted()) - exponent + 2
    with localcontext(Context(prec=precision, rounding=ROUND_HALF_EVEN)) as context:
        # Fail explicitly if exactness is ever violated instead of losing digits.
        context.traps[Inexact] = True
        return context.subtract(held, amount) if subtract else context.add(held, amount)


def _multiply_exact(left: Decimal, right: Decimal) -> Decimal:
    """A product needs at most the sum of its operands' coefficient lengths."""
    precision = len(left.as_tuple().digits) + len(right.as_tuple().digits)
    with localcontext(Context(prec=precision, rounding=ROUND_HALF_EVEN)) as context:
        context.traps[Inexact] = True
        return context.multiply(left, right)


def calculate_position(transactions: Iterable[Transaction]) -> Position:
    """Replay ordered transactions without modifying the inputs.

    Track quantities exactly with precision sized to each addition/subtraction.
    Buy cost totals are exact; average division and profit arithmetic use
    28 significant digits and half-even rounding,
    independent of the caller's context; no currency-scale rounding is applied.
    Empty histories return zeros. Sells retain average cost for nonzero
    holdings and reset it to zero when the position is fully closed.
    """
    quantity = Decimal(0)
    average_cost = Decimal(0)
    realized_pnl = Decimal(0)
    with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
        for transaction in transactions:
            if transaction.type is TransactionType.BUY:
                new_quantity = _add_exact(quantity, transaction.quantity)
                total_cost = _add_exact(
                    _multiply_exact(quantity, average_cost),
                    _multiply_exact(transaction.quantity, transaction.unit_price),
                )
                average_cost = total_cost / new_quantity
                quantity = new_quantity
            else:
                if transaction.quantity > quantity:
                    raise InsufficientPositionError(transaction.quantity, quantity)
                realized_pnl += transaction.quantity * (
                    transaction.unit_price - average_cost
                )
                quantity = _add_exact(quantity, transaction.quantity, subtract=True)
                if quantity == 0:
                    average_cost = Decimal(0)
    return Position(quantity, average_cost, realized_pnl)
