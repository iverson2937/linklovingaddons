from odoo import models, api


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def _get_tracked_fields(self, updated_fields):
        """ Return a structure of tracked fields for the current model.
            :param list updated_fields: modified field names
            :return dict: a dict mapping field name to description, containing
                always tracked fields and modified on_change fields
        """
        tracked_fields = []
        for name, field in self._fields.items():
            if getattr(field, 'track_visibility', False):
                tracked_fields.append(name)

        if tracked_fields:
            res = {}
            fields = self.fields_get(tracked_fields)
            for key, value in fields.iteritems():
                if not 'sel_groups_' in key and not 'in_group_' in key:
                    res.update({key: value})
            return res

        return {}
