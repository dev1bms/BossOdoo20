from odoo import api, fields, models

# 0 to 10, as Odoo 17 rated (x_entity_ratings.x_studio_rating, about 3 800 ratings): the same scale keeps them
# comparable when they are migrated.
RATINGS = [(str(value), str(value)) for value in range(11)]


class BossExpedienteRating(models.Model):
    """Rating of a party of a file when operations close (F0-C66; Odoo 17 required it to close since 01/03/2025): the
    customer and every supplier the file bought from. Cristina chooses suppliers by their average too."""

    _name = "boss.expediente.rating"
    _description = "Rating of a party of a shipment file"
    _order = "expediente_id desc, role, id"

    expediente_id = fields.Many2one("boss.expediente", "File", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="expediente_id.company_id", store=True)
    partner_id = fields.Many2one("res.partner", "Party", required=True, index=True, ondelete="cascade")
    role = fields.Selection([("customer", "Customer"), ("supplier", "Supplier")], required=True)
    rating = fields.Selection(RATINGS, "Rating (0-10)", help="0 very bad, 10 excellent.")
    note = fields.Char("Comment")
    user_id = fields.Many2one("res.users", "Rated by", readonly=True)

    _party_unique = models.Constraint("UNIQUE(expediente_id, partner_id, role)",
                                      "A party is rated once per file and role.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("rating"):
                vals["user_id"] = self.env.uid
        return super().create(vals_list)

    def write(self, vals):
        if "rating" in vals:
            vals = dict(vals, user_id=self.env.uid if vals["rating"] else False)
        return super().write(vals)
