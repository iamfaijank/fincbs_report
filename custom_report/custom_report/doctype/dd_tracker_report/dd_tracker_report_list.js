frappe.listview_settings['DD Tracker Report'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__("Sync Data"), function() {
            let d = new frappe.ui.Dialog({
                title: 'Sync DD Tracker Report',
                fields: [
                    {
                        label: 'Sync Date',
                        fieldname: 'sync_date',
                        fieldtype: 'Date',
                        reqd: 1,
                        default: frappe.datetime.add_days(frappe.datetime.get_today(), -1)
                    }
                ],
                primary_action_label: 'Sync',
                primary_action(values) {
                    frappe.call({
                        method: "custom_report.custom_report.doctype.dd_tracker_report.dd_tracker_report.sync_dd_tracker_data",
                        args: {
                            sync_date: values.sync_date
                        },
                        freeze: true,
                        freeze_message: "Syncing data from DR. This may take a while...",
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint("Data synced successfully for " + values.sync_date);
                                listview.refresh();
                            }
                            d.hide();
                        }
                    });
                }
            });
            d.show();
        });
    }
};
