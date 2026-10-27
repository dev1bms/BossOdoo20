import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";

// On a wide screen (>= XXL) Odoo puts the chatter beside the form, which halves the width left to the form.
// BOSS forms (quotation, shipment file, tariff) are wide by nature: the chatter goes below the form on every
// screen size (Belal, 27/10/2026). Attachment previews keep their standard place (beside, "COMBO" layouts).
const BELOW = {
    SIDE_CHATTER: "BOTTOM_CHATTER",
    EXTERNAL_COMBO_XXL: "EXTERNAL_COMBO",
};

patch(FormRenderer.prototype, {
    mailLayout(hasAttachmentContainer) {
        const layout = super.mailLayout(hasAttachmentContainer);
        return BELOW[layout] || layout;
    },
});
