from odoo import fields, models

RECENT_LIMIT = 20


class IrRecentRecord(models.Model):
    _name = "ir.recent.record"
    _description = "Recently Viewed Record"
    _order = "access_date desc"

    user_id = fields.Many2one("res.users", required=True, ondelete="cascade", index=True)
    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    res_name = fields.Char()
    access_date = fields.Datetime(required=True, default=fields.Datetime.now)

    _unique_user_model_record = models.Constraint(
        "UNIQUE(user_id, res_model, res_id)",
        "Duplicate recently-viewed entry for this user and record.",
    )

    def _log(self, res_model, res_id, res_name):
        """Upsert a visit entry for the current user, then prune to RECENT_LIMIT."""
        uid = self.env.uid
        self.env.cr.execute(
            """
            INSERT INTO ir_recent_record
                (user_id, res_model, res_id, res_name, access_date,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, clock_timestamp(), %s, %s, clock_timestamp(), clock_timestamp())
            ON CONFLICT (user_id, res_model, res_id)
            DO UPDATE SET
                res_name    = EXCLUDED.res_name,
                access_date = clock_timestamp(),
                write_date  = clock_timestamp(),
                write_uid   = EXCLUDED.write_uid
            """,
            (uid, res_model, res_id, res_name, uid, uid),
        )
        self.env.cr.execute(
            """
            DELETE FROM ir_recent_record
            WHERE user_id = %s
              AND id NOT IN (
                  SELECT id FROM ir_recent_record
                  WHERE user_id = %s
                  ORDER BY access_date DESC
                  LIMIT %s
              )
            """,
            (uid, uid, RECENT_LIMIT),
        )

    def _get_recent(self):
        """Return the last RECENT_LIMIT visited records for the current user."""
        self.env.cr.execute(
            """
            SELECT res_model, res_id, res_name, access_date
            FROM ir_recent_record
            WHERE user_id = %s
            ORDER BY access_date DESC
            LIMIT %s
            """,
            (self.env.uid, RECENT_LIMIT),
        )
        rows = self.env.cr.dictfetchall()
        model_names = {r["res_model"] for r in rows}
        ir_models = self.env["ir.model"].search([("model", "in", list(model_names))])
        desc_map = {m.model: m.name for m in ir_models}
        for row in rows:
            if row.get("access_date"):
                row["access_date"] = row["access_date"].isoformat()
            row["model_description"] = desc_map.get(row["res_model"], row["res_model"])
        return rows

    def _clear(self):
        """Delete all recently-viewed records for the current user."""
        self.env.cr.execute(
            "DELETE FROM ir_recent_record WHERE user_id = %s",
            (self.env.uid,),
        )
