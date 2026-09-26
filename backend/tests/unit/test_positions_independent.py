"""Independent ADR-0004 and ADR-0008 checks; expected values do not use production helpers."""
from decimal import Decimal, localcontext, ROUND_DOWN
import unittest

from app.domain.positions import (
    Transaction, TransactionType, InsufficientPositionError, calculate_position,
)


def tx(side, quantity, price):
    return Transaction(TransactionType[side], Decimal(quantity), Decimal(price))


class IndependentPositionTests(unittest.TestCase):
    def check(self, rows, quantity, average, pnl):
        history = [tx(*row) for row in rows]
        before = list(history)
        result = calculate_position(history)
        self.assertEqual(result.quantity, Decimal(quantity))
        self.assertEqual(result.average_cost, Decimal(average))
        self.assertEqual(result.realized_pnl, Decimal(pnl))
        self.assertEqual(history, before)
        return result

    def test_empty_history_has_no_holdings_or_profit(self):
        self.check([], '0', '0', '0')

    def test_three_unequal_buys(self):
        # Total acquisition cost 24 + 80 + 56 = 160 over 10 units.
        self.check([('BUY','3','8'), ('BUY','5','16'), ('BUY','2','28')],
                   '10', '16', '0')

    def test_sale_uses_presale_average_and_leaves_it_unchanged(self):
        self.check([('BUY','3','8'), ('BUY','5','16'), ('BUY','2','28'),
                    ('SELL','4','21')], '6', '16', '20')

    def test_loss_and_break_even_sales(self):
        self.check([('BUY','8','12.5'), ('SELL','2','10'), ('SELL','3','12.5')],
                   '3', '12.5', '-5')

    def test_long_history_every_prefix_against_manual_ledger(self):
        rows = [
            ('BUY','8','10'), ('BUY','2','20'), ('SELL','4','15'),
            ('BUY','6','18'), ('SELL','3','11'), ('BUY','3','7'),
            ('SELL','5','17'), ('BUY','7','19'), ('SELL','4','14'),
            ('SELL','10','20'), ('BUY','0.25','8'), ('SELL','0.125','12'),
        ]
        # (remaining units, average cost, cumulative realized P&L).
        expected = [
            ('8','10','0'), ('10','12','0'), ('6','12','12'),
            ('12','15','12'), ('9','15','0'), ('12','13','0'),
            ('7','13','20'), ('14','16','20'), ('10','16','12'),
            ('0','0','52'), ('0.25','8','52'), ('0.125','8','52.5'),
        ]
        for count, state in enumerate(expected, 1):
            with self.subTest(prefix=count):
                self.check(rows[:count], *state)

    def test_exact_full_sale_succeeds(self):
        self.check([('BUY','0.1','10'), ('BUY','0.2','25'), ('SELL','0.3','30')],
                   '0', '0', '3')

    def test_close_resets_average_and_reopening_uses_only_new_buy(self):
        # Cost = 2*9 + 6*17 = 120; average = 15 across 8 units.
        rows = [('BUY','2','9'), ('BUY','6','17'), ('SELL','3','19')]
        self.check(rows, '5', '15', '12')
        # Closing at a loss realizes 5*(11-15) = -20 before resetting.
        rows.append(('SELL','5','11'))
        self.check(rows, '0', '0', '-8')
        # Reopening has no old held cost to blend in; realized P&L persists.
        rows.append(('BUY','0.4','37.5'))
        self.check(rows, '0.4', '37.5', '-8')
        rows.append(('SELL','0.1','42.5'))
        self.check(rows, '0.3', '37.5', '-7.5')

    def test_oversell_rejected_at_each_boundary(self):
        cases = [
            ([], '0', '0.00000001'),
            ([('BUY','0.3','10')], '0.3', '0.30000001'),
            ([('BUY','2','10'), ('SELL','1.75','12')], '0.25', '0.25000001'),
            ([('BUY','2','10'), ('SELL','2','12')], '0', '0.00000001'),
        ]
        for rows, held, requested in cases:
            with self.subTest(held=held, requested=requested):
                with self.assertRaises(InsufficientPositionError) as caught:
                    calculate_position([tx(*r) for r in rows] + [tx('SELL', requested, '10')])
                self.assertEqual(caught.exception.held, Decimal(held))
                self.assertEqual(caught.exception.requested, Decimal(requested))
                self.assertEqual(type(caught.exception).__module__, 'app.domain.positions')

    def test_later_buy_cannot_fund_earlier_sale(self):
        with self.assertRaises(InsufficientPositionError):
            calculate_position([tx('SELL','1','10'), tx('BUY','2','10')])

    def test_order_changes_realized_profit(self):
        self.check([('BUY','2','10'), ('SELL','1','30'), ('BUY','1','40')],
                   '2', '25', '20')
        self.check([('BUY','2','10'), ('BUY','1','40'), ('SELL','1','30')],
                   '2', '20', '10')

    def test_tiny_fractional_units_and_prices(self):
        self.check([('BUY','0.00000001','0.00000002'),
                    ('BUY','0.00000003','0.00000006'),
                    ('SELL','0.00000002','0.00000008')],
                   '0.00000002', '0.00000005', '0.0000000000000006')

    def test_repeating_average_with_explicit_error_bound(self):
        # Exact average 5/3; exact realized P&L 4/3. No approved rounding policy.
        result = calculate_position([tx('BUY','1','1'), tx('BUY','2','2'), tx('SELL','1','3')])
        with localcontext() as ctx:
            ctx.prec = 60
            self.assertLess(abs(result.average_cost - Decimal(5)/3), Decimal('1e-26'))
            self.assertLess(abs(result.realized_pnl - Decimal(4)/3), Decimal('1e-26'))
        self.assertEqual(result.quantity, Decimal('2'))

    def test_caller_context_and_iterator_do_not_change_results(self):
        rows = [tx('BUY','3','8'), tx('BUY','5','16'), tx('SELL','2','20')]
        with localcontext() as ctx:
            ctx.prec = 3
            ctx.rounding = ROUND_DOWN
            result = calculate_position(iter(rows))
            self.assertEqual(ctx.prec, 3)
            self.assertEqual(ctx.rounding, ROUND_DOWN)
        self.assertEqual((result.quantity, result.average_cost, result.realized_pnl),
                         (Decimal('6'), Decimal('13'), Decimal('14')))

    def test_valid_small_buy_must_not_disappear(self):
        self.check([('BUY','1','10'), ('BUY','0.0000000000000000000000000001','10')],
                   '1.0000000000000000000000000001', '10', '0')

    def test_exact_full_sale_after_small_buy_must_succeed(self):
        self.check([('BUY','1','10'), ('BUY','0.0000000000000000000000000001','10'),
                    ('SELL','1.0000000000000000000000000001','10')],
                   '0', '0', '0')


if __name__ == '__main__':
    unittest.main()
