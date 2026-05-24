/** @odoo-module **/

import { Component, useState, useExternalListener } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class RecentlyViewedSystray extends Component {
    static template = "consultive_recently_viewed_basic.RecentlyViewedSystray";
    static props = {};

    setup() {
        this.actionService = useService("action");
        this.state = useState({ open: false, records: [] });
        useExternalListener(window, "click", () => {
            this.state.open = false;
        });
    }

    async toggle() {
        if (!this.state.open) {
            const records = await rpc("/web/recently_viewed/get", {});
            this.state.records = records || [];
        }
        this.state.open = !this.state.open;
    }

    async openRecord(record) {
        this.state.open = false;
        try {
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: record.res_model,
                res_id: record.res_id,
                views: [[false, "form"]],
                target: "current",
            });
        } catch {
            // Record may have been deleted — silently ignore
        }
    }

    async clearHistory() {
        await rpc("/web/recently_viewed/clear", {});
        this.state.records = [];
    }

    // Called via t-on-click.stop on the container to prevent the external
    // window listener from closing the dropdown when clicking inside it.
    onContainerClick() {}
}

registry.category("systray").add(
    "consultive_recently_viewed",
    { Component: RecentlyViewedSystray },
    { sequence: 1 }
);
