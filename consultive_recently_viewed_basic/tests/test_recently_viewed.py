from odoo.tests.common import TransactionCase


class TestIrRecentRecord(TransactionCase):

    def setUp(self):
        super().setUp()
        self.user_a = self.env.user.copy({
            "name": "Test RV User A",
            "login": "test_rv_user_a",
            "email": "test_rv_a@example.com",
        })
        self.user_b = self.env.user.copy({
            "name": "Test RV User B",
            "login": "test_rv_user_b",
            "email": "test_rv_b@example.com",
        })
        self.Model = self.env["ir.recent.record"]

    def _log(self, user, res_model, res_id, res_name="Test Record"):
        self.Model.with_user(user)._log(res_model, res_id, res_name)

    def _count_rows(self, user):
        self.env.cr.execute(
            "SELECT COUNT(*) FROM ir_recent_record WHERE user_id = %s",
            (user.id,),
        )
        return self.env.cr.fetchone()[0]

    def test_log_creates_row(self):
        self._log(self.user_a, "res.partner", 9901, "Partner One")
        self.env.cr.execute(
            "SELECT res_name FROM ir_recent_record "
            "WHERE user_id = %s AND res_model = %s AND res_id = %s",
            (self.user_a.id, "res.partner", 9901),
        )
        row = self.env.cr.fetchone()
        self.assertIsNotNone(row, "A recently-viewed row must be created on first visit")
        self.assertEqual(row[0], "Partner One")

    def test_upsert_no_duplicate_and_name_updated(self):
        self._log(self.user_a, "res.partner", 9902, "Old Name")
        self._log(self.user_a, "res.partner", 9902, "New Name")
        self.env.cr.execute(
            "SELECT COUNT(*), MAX(res_name) FROM ir_recent_record "
            "WHERE user_id = %s AND res_model = %s AND res_id = %s",
            (self.user_a.id, "res.partner", 9902),
        )
        count, name = self.env.cr.fetchone()
        self.assertEqual(count, 1, "Upsert must not produce duplicate rows")
        self.assertEqual(name, "New Name", "res_name must be refreshed on conflict")

    def test_prune_keeps_at_most_20_rows(self):
        for i in range(25):
            self._log(self.user_a, "sale.order", 10000 + i, f"Order {i}")
        count = self._count_rows(self.user_a)
        self.assertLessEqual(count, 20, "Prune must keep at most 20 rows per user")

    def test_prune_does_not_affect_other_users(self):
        for i in range(25):
            self._log(self.user_a, "sale.order", 10100 + i, f"Order A{i}")
        self._log(self.user_b, "res.partner", 9903, "Partner B")
        count_b = self._count_rows(self.user_b)
        self.assertEqual(count_b, 1, "User B's records must not be pruned by User A's inserts")

    def test_user_isolation_via_orm(self):
        self._log(self.user_a, "res.partner", 9904, "User A's Record")
        visible_to_b = self.Model.with_user(self.user_b).search(
            [("res_model", "=", "res.partner"), ("res_id", "=", 9904)]
        )
        self.assertFalse(
            visible_to_b,
            "User B must not see User A's recently-viewed records via ORM",
        )
