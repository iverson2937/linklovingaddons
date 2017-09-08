// odoo.define('linkloving_sale_dashboard.Dashboard', function (require) {
//     "use strict";
//
//     var core = require('web.core');
//     var Model = require('web.Model');
//     var Widget = require('web.Widget');
//     var View = require('web.View');
//
//     var QWeb = core.qweb;
//     var _t = core._t;
//     var sales_team_dashboard = core.view_registry.get('list');
//     console.log(core.view_registry);
//     console.log(sales_team_dashboard);
//
//
//     sales_team_dashboard.include({
//         render: function () {
//             var super_render = this._super;
//             var self = this;
//             console.log(self)
//
//
//         }
//
//     });
// });

odoo.define('linkloving_sale_dashboard.dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var formats = require('web.formats');
    var Model = require('web.Model');
    var session = require('web.session');
    var KanbanView = require('web_kanban.KanbanView');

    var QWeb = core.qweb;

    var _t = core._t;
    var _lt = core._lt;

    var SalesTeamDashboardView = require('sales_team.dashboard');
    var Model = require('web.Model');

    SalesTeamDashboardView.include({

        render: function () {
            var super_render = this._super;
            var self = this;

            return this.fetch_data().then(function (result) {
                console.log(result)
                self.show_demo = result && result.nb_opportunities === 0;

                var sales_dashboard = QWeb.render('sales_team.SalesDashboard', {
                    widget: self,
                    show_demo: self.show_demo,
                    values: result,
                });
                super_render.call(self);
                $(sales_dashboard).prependTo(self.$el);
            });
        },
    });

});
