frappe.listview_settings['Staff Productivity'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__('Sync'), function() {
            let d = new frappe.ui.Dialog({
                title: __('Sync Staff Productivity'),
                intro_title: __('Re-running the same date replaces the records of that date and report type. Data synced on any other date is kept as-is.'),
                fields: [
                    {
                        label: __('Report Type'),
                        fieldname: 'report_type',
                        fieldtype: 'Select',
                        options: 'BDE & BDO\nRD\nSMBG\nDD\nCASA',
                        reqd: 1
                    },
                    {
                        label: __('Date'),
                        fieldname: 'date',
                        fieldtype: 'Date',
                        reqd: 1,
                        default: frappe.datetime.add_days(frappe.datetime.get_today(), -1)
                    }
                ],
                primary_action_label: __('Start Sync'),
                primary_action(values) {
                    frappe.call({
                        method: 'custom_report.custom_report.doctype.staff_productivity.staff_productivity.sync_staff_productivity',
                        args: {
                            report_type: values.report_type,
                            date: values.date
                        },
                        freeze: true,
                        freeze_message: __('Connecting to DR Database & Syncing Data...'),
                        callback: function(r) {
                            if (!r.exc) {
                                let s = r.message || {};
                                frappe.msgprint({
                                    title: __('Sync Complete'),
                                    message: __('Report Type: {0}<br>Date: {1}<br>Processed: {2}<br>Inserted: {3}<br>Replaced: {4}<br>Failed: {5}', [
                                        values.report_type,
                                        values.date,
                                        s.processed || 0,
                                        s.inserted || 0,
                                        s.replaced || 0,
                                        s.failed || 0
                                    ]),
                                    indicator: (s.failed || 0) > 0 ? 'orange' : 'green'
                                });
                                listview.refresh();
                            }
                        }
                    });
                    
                    d.hide();
                }
            });
            d.show();
        });

        listview.page.add_inner_button(__('Delete All'), function() {
            frappe.call({
                method: 'custom_report.custom_report.doctype.staff_productivity.staff_productivity.clear_staff_productivity_data',
                callback: function(r) {
                    if (r.exc || !r.message) return;

                    let count = r.message.total || 0;
                    if (!count) {
                        frappe.msgprint(__('No records to delete.'));
                        return;
                    }

                    frappe.confirm(
                        __('This will permanently delete all {0} record(s) from {1}. This cannot be undone.', [count, __('Staff Productivity')]),
                        {
                            title: __('Delete All Records'),
                            'dangerouslyDisableConfirm': false
                        },
                        function() {
                            frappe.call({
                                method: 'custom_report.custom_report.doctype.staff_productivity.staff_productivity.clear_staff_productivity_data',
                                args: { confirm: 1 },
                                freeze: true,
                                freeze_message: __('Deleting all records...'),
                                callback: function(res) {
                                    if (res.exc) return;
                                    let s = res.message || {};
                                    frappe.msgprint({
                                        title: __('Delete Complete'),
                                        message: __('Deleted {0} of {1} record(s).<br>Remaining: {2}', [
                                            s.deleted || 0,
                                            s.total || 0,
                                            s.remaining || 0
                                        ]),
                                        indicator: (s.remaining || 0) > 0 ? 'orange' : 'green'
                                    });
                                    listview.refresh();
                                }
                            });
                        }
                    );
                }
            });
        }).addClass('btn-danger');
    }
};
