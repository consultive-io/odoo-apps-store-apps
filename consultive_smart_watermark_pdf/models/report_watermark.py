import logging
from markupsafe import escape, Markup
from odoo import models

_logger = logging.getLogger(__name__)

# Injected into <head>: override overflow:hidden on web.minimal_layout body.
_OVERFLOW_CSS = (
    '<style>'
    'html,body,.o_body_pdf,.overflow-hidden,.overflow-x-hidden'
    '{overflow:visible!important;overflow-x:visible!important}'
    '</style>'
)

# Position: center of A4 content viewport (717×1046px at 96dpi with 10mm margins),
# empirically tuned. translate(-50%,-50%) is element-relative in WebKit, so the
# visual center of the text is always at (395, 400) regardless of text length.
_WM_DIV_BASE = (
    'position:fixed;left:395px;top:400px;'
    '-webkit-transform:translate(-50%,-50%) rotate(-45deg);'
    'transform:translate(-50%,-50%) rotate(-45deg);'
    'white-space:nowrap;font-weight:900;'
    'font-family:Arial,Helvetica,sans-serif;'
    'color:rgba(220,38,38,0.40);z-index:99999;'
    'pointer-events:none;'
    '-webkit-print-color-adjust:exact;print-color-adjust:exact;'
)

# Dynamic font sizing: scale so text width ≈ 700px regardless of text length.
# Derivation: target_px=700, char_ratio=0.72 (Arial Bold uppercase), pt_per_px=72/96
#   → font_pt = 700 / (n_chars × 0.72) × (72/96) = 729 / n_chars
# Capped at 80pt (short texts like "DRAFT") and floored at 20pt.
_WM_MAX_FONT_PT = 80
_WM_FONT_SCALE = 729  # = 700 × (72/96) / 0.72


def _wm_font_pt(text):
    return min(_WM_MAX_FONT_PT, max(20, round(_WM_FONT_SCALE / max(len(text), 1))))


def _wm_div_style(text):
    return _WM_DIV_BASE + f'font-size:{_wm_font_pt(text)}pt;'


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _prepare_html(self, html, report_model=False):
        """Inject watermark into each wkhtmltopdf body after _prepare_html runs.

        web.report_layout injection (report_layout.xml) is discarded by Odoo's
        _prepare_html — it only keeps <div class="article"> nodes and re-wraps
        them in web.minimal_layout. We inject here, after that re-wrap, so our
        div actually reaches wkhtmltopdf.
        """
        result = super()._prepare_html(html, report_model=report_model)
        if not result or not isinstance(result, tuple) or not report_model:
            return result

        wm_model = self.env.get('consultive.watermark.config')
        if wm_model is None:
            return result

        bodies = list(result[0])
        res_ids = result[1]

        for i, (body, res_id) in enumerate(zip(bodies, res_ids)):
            if not res_id:
                continue
            try:
                record = self.env[report_model].browse(res_id)
                wm_text = wm_model.get_watermark_text(record)
            except Exception:
                _logger.exception(
                    'consultive_smart_watermark_pdf: error getting watermark '
                    'text for %s(%s)', report_model, res_id
                )
                continue

            if not wm_text:
                continue

            body_str = str(body)

            if '</head>' in body_str:
                body_str = body_str.replace('</head>', _OVERFLOW_CSS + '</head>', 1)

            wm_html = str(
                Markup('<div style="') + Markup(_wm_div_style(wm_text)) + Markup('">')
                + escape(wm_text)
                + Markup('</div>')
            )
            if '</body>' in body_str:
                body_str = body_str.replace('</body>', wm_html + '</body>', 1)
            else:
                body_str += wm_html

            bodies[i] = Markup(body_str)

        return (bodies,) + result[1:]
