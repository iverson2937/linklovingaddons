from odoo import models, fields, api, _


class project_issue(models.Model):
    _inherit = 'project.issue'

    version_id = fields.Many2one('project.issue.version', 'Version')

    @api.onchange("project_id")
    def on_change_project(self):
        if self.project_id and self.project_id.partner_id:
            return {
                'value': {'partner_id': self.project_id.partner_id.id, 'email_from': self.project_id.partner_id.email}}
        return {}
