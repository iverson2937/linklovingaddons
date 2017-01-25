(function (a) {
    function d(b) {
        var c = b || window.event, d = [].slice.call(arguments, 1), e = 0, f = !0, g = 0, h = 0;
        return b = a.event.fix(c), b.type = "mousewheel", c.wheelDelta && (e = c.wheelDelta / 120), c.detail && (e = -c.detail / 3), h = e, c.axis !== undefined && c.axis === c.HORIZONTAL_AXIS && (h = 0, g = -1 * e), c.wheelDeltaY !== undefined && (h = c.wheelDeltaY / 120), c.wheelDeltaX !== undefined && (g = -1 * c.wheelDeltaX / 120), d.unshift(b, e, g, h), (a.event.dispatch || a.event.handle).apply(this, d)
    }

    var b = ["DOMMouseScroll", "mousewheel"];
    if (a.event.fixHooks)for (var c = b.length; c;)a.event.fixHooks[b[--c]] = a.event.mouseHooks;
    a.event.special.mousewheel = {
        setup: function () {
            if (this.addEventListener)for (var a = b.length; a;)this.addEventListener(b[--a], d, !1); else this.onmousewheel = d
        }, teardown: function () {
            if (this.removeEventListener)for (var a = b.length; a;)this.removeEventListener(b[--a], d, !1); else this.onmousewheel = null
        }
    }, a.fn.extend({
        mousewheel: function (a) {
            return a ? this.bind("mousewheel", a) : this.trigger("mousewheel")
        }, unmousewheel: function (a) {
            return this.unbind("mousewheel", a)
        }
    })
})(jQuery);


odoo.define('web.tree_image_preview', function (require) {
    "use strict";
    var core = require('web.core');
    var session = require('web.session');
    var ListView = require('web.ListView');
    var QWeb = core.qweb;
    var list_widget_registry = core.list_widget_registry;
    var WebTreeImagePreview = list_widget_registry.get('field.binary').extend({
        format: function (row_data, options) {
            if (!row_data[this.id] || !row_data[this.id].value) {
                return '';
            }
            var value = row_data[this.id].value, src;
            if (this.type === 'binary') {
                if (value && value.substr(0, 10).indexOf(' ') === -1) {
                    src = "data:image/png;base64," + value;
                } else {
                    var imageArgs = {
                        model: options.model,
                        field: this.id,
                        id: options.id
                    }
                    if (this.resize) {
                        imageArgs.resize = this.resize;
                    }
                    src = session.url('/web/binary/image', imageArgs);
                }
            } else {
                if (!/\//.test(row_data[this.id].value)) {
                    src = '/web/static/src/img/icons/' + row_data[this.id].value + '.png';
                } else {
                    src = row_data[this.id].value;
                }
            }
            return QWeb.render('ListView.row.image.preview', {widget: this, src: src});
        }
    });

    ListView.List.include({
        render: function () {
            var result = this._super(this, arguments)
            this.$current.delegate('img.web_tree_image_preview',
                'click', function () {
                    var image_href = $(this).attr('src');
                    var tree_image_preview_box = $('#web_image_preview_box')
                    if (tree_image_preview_box.length > 0) {
                        $('#content').html('<img id="myimage" src="' + image_href + '" /><script type="text/javascript">var myimage = document.getElementById("myimage");if (myimage.addEventListener) {myimage.addEventListener("mousewheel", MouseWheelHandler, false);myimage.addEventListener("DOMMouseScroll", MouseWheelHandler, false);}else myimage.attachEvent("onmousewheel", MouseWheelHandler);function MouseWheelHandler(e) {var e = window.event || e;delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));myimage.style.width = Math.max(50, Math.min(1920, myimage.width + (30 * delta))) + "px";return false;}</script>');
                        tree_image_preview_box.show();
                    }
                    else {
                        var preview_box =
                            '<div id="web_image_preview_box" onclick="this.style.display = \'none\';">' +
                            '<div id="content">' +
                            '<img id="myimage" src="' + image_href + '" />' +
                            '<script type="text/javascript">var myimage = document.getElementById("myimage");if (myimage.addEventListener) {myimage.addEventListener("mousewheel", MouseWheelHandler, false);myimage.addEventListener("DOMMouseScroll", MouseWheelHandler, false);}else myimage.attachEvent("onmousewheel", MouseWheelHandler);function MouseWheelHandler(e) {var e = window.event || e;delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));myimage.style.width = Math.max(50, Math.min(1920, myimage.width + (30 * delta))) + "px";return false;}</script>' +
                            '</div>' +
                            '</div>';
                        $('body').append(preview_box);
                    }
                    return false;
                });
            return result;
        },
    });

    list_widget_registry.add('field.tree-image-preview', WebTreeImagePreview)
});


odoo.define('w', function (require) {
    "use strict";
    var core = require('web.core');
    var session = require('web.session');
    var ListView = require('web.ListView');
    var QWeb = core.qweb;

    ListView.List.include({
        init: function (group, opts) {
            var self = this;
            this.group = group;
            this.view = group.view;
            this.session = this.view.session;

            this.options = opts.options;
            this.columns = opts.columns;
            this.dataset = opts.dataset;
            this.records = opts.records;

            this.record_callbacks = {
                'remove': function (event, record) {
                    var id = record.get('id');
                    self.dataset.remove_ids([id]);
                    var $row = self.$current.children('[data-id=' + id + ']');
                    var index = $row.data('index');
                    $row.remove();
                },
                'reset': function () {
                    return self.on_records_reset();
                },
                'change': function (event, record, attribute, value, old_value) {
                    var $row;
                    if (attribute === 'id') {
                        if (old_value) {
                            throw new Error(_.str.sprintf(_t("Setting 'id' attribute on existing record %s"),
                                JSON.stringify(record.attributes)));
                        }
                        self.dataset.add_ids([value], self.records.indexOf(record));
                        // Set id on new record
                        $row = self.$current.children('[data-id=false]');
                    } else {
                        $row = self.$current.children(
                            '[data-id=' + record.get('id') + ']');
                    }
                    var $newRow = $(self.render_record(record));
                    $newRow.find('.o_list_record_selector input').prop('checked', !!$row.find('.o_list_record_selector input').prop('checked'));
                    $row.replaceWith($newRow);
                },
                'add': function (ev, records, record, index) {
                    var $new_row = $(self.render_record(record));
                    var id = record.get('id');
                    if (id) {
                        self.dataset.add_ids([id], index);
                    }

                    if (index === 0) {
                        $new_row.prependTo(self.$current);
                    } else {
                        var previous_record = records.at(index - 1),
                            $previous_sibling = self.$current.children(
                                '[data-id=' + previous_record.get('id') + ']');
                        $new_row.insertAfter($previous_sibling);
                    }
                }
            };
            _(this.record_callbacks).each(function (callback, event) {
                this.records.bind(event, callback);
            }, this);

            this.$current = $('<tbody>')
                .delegate('input[readonly=readonly]', 'click', function (e) {
                    /*
                     Against all logic and sense, as of right now @readonly
                     apparently does nothing on checkbox and radio inputs, so
                     the trick of using @readonly to have, well, readonly
                     checkboxes (which still let clicks go through) does not
                     work out of the box. We *still* need to preventDefault()
                     on the event, otherwise the checkbox's state *will* toggle
                     on click
                     */
                    e.preventDefault();
                })
                .delegate('td.o_list_record_selector', 'click', function (e) {
                    e.stopPropagation();
                    var selection = self.get_selection();
                    var checked = $(e.currentTarget).find('input').prop('checked');
                    $(self).trigger(
                        'selected', [selection.ids, selection.records, !checked]);
                })
                .delegate('td.o_list_record_delete', 'click', function (e) {
                    e.stopPropagation();
                    var $row = $(e.target).closest('tr');
                    $(self).trigger('deleted', [[self.row_id($row)]]);
                    // IE Edge go crazy when we use confirm dialog and remove the focused element
                    if (document.hasFocus && !document.hasFocus()) {
                        $('<input />').appendTo('body').focus().remove();
                    }
                })
                .delegate('td button', 'click', function (e) {
                    e.stopPropagation();
                    var $target = $(e.currentTarget),
                        field = $target.closest('td').data('field'),
                        $row = $target.closest('tr'),
                        record_id = self.row_id($row);

                    if ($target.attr('disabled')) {
                        return;
                    }
                    $target.attr('disabled', 'disabled');

                    // note: $.data converts data to number if it's composed only
                    // of digits, nice when storing actual numbers, not nice when
                    // storing strings composed only of digits. Force the action
                    // name to be a string
                    $(self).trigger('action', [field.toString(), record_id, function (id) {
                        $target.removeAttr('disabled');
                        return self.reload_record(self.records.get(id));
                    }]);
                })
                .delegate('a', 'click', function (e) {
                    e.stopPropagation();
                })
                .delegate('tr', 'click', function (e) {
                    var row_id = self.row_id(e.currentTarget);
                    if (row_id) {
                        e.stopPropagation();
                        if (!self.dataset.select_id(row_id)) {
                            throw new Error(_t("Could not find id in dataset"));
                        }
                        self.row_clicked(e);
                    }
                });
        },
        render_record: function (record) {
            var self = this;
            var index = this.records.indexOf(record);
            return QWeb.render('ListView.row', {
                columns: this.columns,
                options: this.options,
                index: index,
                record: record,
                row_parity: (index % 2 === 0) ? 'even' : 'odd',
                view: this.view,
                render_cell: function () {
                    return self.render_cell.apply(self, arguments);
                }
            });
        },
        render: function () {
            var self = this;
            this.$current.html(
                QWeb.render('ListView.rows', _.extend({}, this, {
                    render_cell: function () {
                        return self.render_cell.apply(self, arguments);
                    }
                })));
            this.pad_table_to(4);
        },

        pad_table_to: function (count) {
            if (this.records.length >= count ||
                _(this.columns).any(function (column) {
                    return column.meta;
                })) {
                return;
            }
            var cells = [];
            if (this.options.selectable) {
                cells.push('<td class="o_list_record_selector"></td>');
            }else {
                 //add by allen to clear blank if the row less than 4
                 cells.push('<td></td>');
            }

            _(this.columns).each(function (column) {
                if (column.invisible === '1') {
                    return;
                }
                cells.push('<td title="' + column.string + '">&nbsp;</td>');
            });
            if (this.options.deletable) {
                cells.push('<td class="o_list_record_delete"></td>');
            }
            cells.unshift('<tr>');
            cells.push('</tr>');

            var row = cells.join('');
            this.$current
                .children('tr:not([data-id])').remove().end()
                .append(new Array(count - this.records.length + 1).join(row));
        },


    });
});