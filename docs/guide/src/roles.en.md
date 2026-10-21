Permissions are set in **Settings › Users** with the standard Sales groups and two BOSS groups.

| Role | Groups | Can |
|---|---|---|
| Salesperson | Sales: user | Opportunities, quotations, shipment data, sale price, see costs and their explanation |
| Salesperson who enters prices | + Supplier tariffs: user | Also create tariffs and prices **as drafts** and send them for approval |
| Tariff approver | Supplier tariffs: approver | Approve tariffs, change the priority of an approved tariff |
| Sales manager | Sales: administrator | Re-price accepted quotations (with a reason), Sales settings |

Rules enforced on the server (also for imports and integrations):

- A tariff is always created as a **draft**; only an approver approves it, with a click.
- Prices of a submitted or approved tariff **cannot change**; a change is a **new version**.
- Only draft tariffs can be deleted; approved ones are archived.
- A line of an accepted quotation only changes through [[Recotizar]].

> Who approves tariffs and who sees costs and margins are open decisions (P19, P20 in
> [Pending decisions](#/preguntas)). By default the administrator is an approver.
