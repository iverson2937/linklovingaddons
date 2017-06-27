odoo.define('linkloving_core.multi_selection', function (require) {
    "use strict";


    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var ListView = require('web.ListView');
    var ajax = require('web.ajax');
    var crash_manager = require('web.crash_manager');
    var data = require('web.data');
    var datepicker = require('web.datepicker');
    var dom_utils = require('web.dom_utils');
    var Priority = require('web.Priority');
    var ProgressBar = require('web.ProgressBar');
    var Dialog = require('web.Dialog');
    var common = require('web.form_common');
    var formats = require('web.formats');
    var framework = require('web.framework');
    var pyeval = require('web.pyeval');
    var session = require('web.session');
    var utils = require('web.utils');

    var QWeb = core.qweb;
    var _t = core._t;

    var FieldDates = common.fieldDate;
    var form_widget_registry = core.form_widget_registry;


});