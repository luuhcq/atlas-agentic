"""Run from backend with: python3 -m unittest -v."""

from decimal import Decimal, ROUND_DOWN, localcontext
import unittest

from app.domain.positions import (
    InsufficientPositionError,
    Position,
    Transaction,
    TransactionType,
    calculate_position,
)


def buy(quantity: str, price: str) -> Transaction:
    return Transaction(TransactionType.BUY, Decimal(quantity), Decimal(price))


def sell(quantity: str, price: str) -> Transaction:
    return Transaction(TransactionType.SELL, Decimal(quantity), Decimal(price))


class PositionTests(unittest.TestCase):
    def test_empty_history(self):
        self.assertEqual(
            calculate_position([]), Position(Decimal(0), Decimal(0), Decimal(0))
        )

    def test_buys_weight_cost_by_quantity(self):
        self.assertEqual(
            calculate_position([buy("10", "10"), buy("30", "20")]),
            Position(Decimal("40"), Decimal("17.5"), Decimal("0")),
        )

    def test_sales_preserve_average_and_accumulate_gains_and_losses(self):
        history = [buy("10", "10"), buy("10", "20"), sell("5", "21")]
        self.assertEqual(
            calculate_position(history),
            Position(Decimal("15"), Decimal("15"), Decimal("30")),
        )
        history.extend([buy("5", "23"), sell("4", "12")])
        self.assertEqual(
            calculate_position(history),
            Position(Decimal("16"), Decimal("17"), Decimal("10")),
        )

    def test_oversell_raises_domain_exception(self):
        for history, held in [([], "0"), ([buy("2", "10")], "2")]:
            with self.subTest(held=held):
                with self.assertRaises(InsufficientPositionError) as error:
                    calculate_position(history + [sell("3", "20"), buy("10", "20")])
                self.assertEqual(error.exception.requested, Decimal("3"))
                self.assertEqual(error.exception.held, Decimal(held))

    def test_full_sale_and_reopening_with_fractional_quantity(self):
        history = [buy("0.5", "10"), sell("0.5", "12")]
        self.assertEqual(
            calculate_position(history),
            Position(Decimal("0"), Decimal("0"), Decimal("1")),
        )
        self.assertEqual(
            calculate_position(history + [buy("0.25", "20")]),
            Position(Decimal("0.25"), Decimal("20"), Decimal("1")),
        )

    def test_decimal_context_does_not_change_results(self):
        history = [buy("1", "1"), buy("2", "2")]
        with localcontext() as context:
            context.prec = 3
            context.rounding = ROUND_DOWN
            result = calculate_position(history)
            self.assertEqual(context.prec, 3)
            self.assertEqual(context.rounding, ROUND_DOWN)
        self.assertEqual(
            result.average_cost, Decimal("1.666666666666666666666666667")
        )

    def test_quantity_tracking_preserves_arbitrarily_small_increments(self):
        for places in (28, 60, 1200):
            with self.subTest(places=places):
                tiny = "0." + "0" * (places - 1) + "1"
                total = "1." + "0" * (places - 1) + "1"
                history = [buy("1", "10"), buy(tiny, "10")]
                self.assertEqual(calculate_position(history).quantity, Decimal(total))
                self.assertEqual(
                    calculate_position(history + [sell("1", "10")]).quantity,
                    Decimal(tiny),
                )
                result = calculate_position(history + [sell(total, "10")])
                self.assertEqual(result.quantity, Decimal(0))
                self.assertEqual(result.realized_pnl, Decimal(0))
                with self.assertRaises(InsufficientPositionError):
                    calculate_position(history + [sell(total + "1", "10")])

    def test_transaction_rejects_invalid_numbers(self):
        for value in ("0", "-1", "NaN", "Infinity"):
            for field in ("quantity", "unit_price"):
                with self.subTest(value=value, field=field):
                    values = {"quantity": Decimal("1"), "unit_price": Decimal("10")}
                    values[field] = Decimal(value)
                    with self.assertRaises(ValueError):
                        Transaction(TransactionType.BUY, **values)

    def test_transaction_rejects_float_and_unknown_type(self):
        with self.assertRaises(TypeError):
            Transaction(TransactionType.BUY, 1.0, Decimal("10"))
        with self.assertRaises(ValueError):
            Transaction("unknown", Decimal("1"), Decimal("10"))


if __name__ == "__main__":
    unittest.main()
