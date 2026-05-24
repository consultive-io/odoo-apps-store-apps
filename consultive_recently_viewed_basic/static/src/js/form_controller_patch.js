/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => this._logRecentlyViewed());
    },

    _logRecentlyViewed() {
        const root = this.model.root;
        const resId = root.resId;
        const resModel = root.resModel;
        if (!resId || !resModel) {
            return;
        }
        const resName =
            (root.data && (root.data.display_name || root.data.name)) || "";
        rpc("/web/recently_viewed/log", {
            res_model: resModel,
            res_id: resId,
            res_name: resName,
        }).catch(() => {});
    },
});
