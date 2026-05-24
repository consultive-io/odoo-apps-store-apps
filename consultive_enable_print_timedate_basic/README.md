# Consultive – Enable Print Time Date Basic

Appends a **"Printed on: Month DD, YYYY HH:MM AM/PM (GMT)"** line at the
bottom of every PDF / printed report in Odoo 19 (Community & Enterprise).

## Installation

1. Copy the `consultive_enable_print_timedate_basic` folder into your Odoo
   `addons` path.
2. Restart the Odoo server.
3. In the backend, go to **Apps**, remove the *Apps* filter, search for
   **Consultive Enable Print Time Date Basic**, and click **Install**.

## Notes

- The timestamp is rendered in **UTC / GMT** by the server at print time.
- Applies automatically to all four built-in report layouts (Standard, Striped,
  Boxed, Bold) with no further configuration.
- No per-model toggle is included in this version.
