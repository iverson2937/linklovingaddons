odoo.define('linkloving_core.date_format', function (require) {
    "use strict";


    //var core = require('web.core');
    //var Model = require('web.Model');
    //var Widget = require('web.Widget');
    //var ListView = require('web.ListView');
    //var ajax = require('web.ajax');
    //var crash_manager = require('web.crash_manager');
    //var data = require('web.data');
    //var datepicker = require('web.datepicker');
    //var dom_utils = require('web.dom_utils');
    //var Priority = require('web.Priority');
    //var ProgressBar = require('web.ProgressBar');
    //var Dialog = require('web.Dialog');
    //var common = require('web.form_common');
    //var formats = require('web.formats');
    //var framework = require('web.framework');
    //var pyeval = require('web.pyeval');
    //var session = require('web.session');
    //var utils = require('web.utils');
    //
    //var QWeb = core.qweb;
    //var _t = core._t;
    //
    //var FieldDates = common.fieldDate;
    //var form_widget_registry = core.form_widget_registry;

    Date.prototype.Format = function (fmt) { //author: meizz
        var o = {
            "M+": this.getMonth() + 1,                 //月份
            "d+": this.getDate(),                    //日
            "h+": this.getHours(),                   //小时
            "m+": this.getMinutes(),                 //分
            "s+": this.getSeconds(),                 //秒
            "q+": Math.floor((this.getMonth() + 3) / 3), //季度
            "S": this.getMilliseconds()             //毫秒
        };
        if (/(y+)/.test(fmt))
            fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
        for (var k in o)
            if (new RegExp("(" + k + ")").test(fmt))
                fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
        return fmt;
    }

});