from odoo import http
from odoo.http import request


class RecentlyViewedController(http.Controller):

    @http.route("/web/recently_viewed/log", type="jsonrpc", auth="user", methods=["POST"])
    def log(self, res_model, res_id, res_name=""):
        if not res_model or not res_id:
            return {"ok": False}
        res_id = int(res_id)
        if not res_name:
            try:
                res_name = request.env[res_model].browse(res_id).display_name or ""
            except Exception:
                res_name = ""
        request.env["ir.recent.record"]._log(res_model, res_id, res_name)
        return {"ok": True}

    @http.route("/web/recently_viewed/get", type="jsonrpc", auth="user", methods=["POST"])
    def get(self):
        return request.env["ir.recent.record"]._get_recent()

    @http.route("/web/recently_viewed/clear", type="jsonrpc", auth="user", methods=["POST"])
    def clear(self):
        request.env["ir.recent.record"]._clear()
        return {"ok": True}
