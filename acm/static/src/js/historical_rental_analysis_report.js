odoo.define("acm_reports.historical_rental_analysis_report", function (require) {
    "use strict";

    var ListController = require("web.ListController");

    var includeDict = {
        renderButtons: function () {
            this._super.apply(this, arguments);
            if ((this.modelName === "historical.occupancy.analysis.report" || this.modelName === "historical.rental.rate.analysis.report") && this.$buttons) {
                var self = this;
                var data = this.model.get(this.handle);
                // Hide create and import button
                this.$buttons.find(".o_list_button_add").hide();
                this.$buttons.find(".o_button_import").hide()
                // Show lessee info
                this.$buttons
                    .find(".lessee_info")
                    .on("click", function () {
                        self._rpc({
                            model: "lessee.info.wizard",
                            method: "create",
                            args: [{}],
                            context: data.context,
                        }).then(function (res_id) {
                            self.do_action({
                                name: "Lessee Info",
                                type: "ir.actions.act_window",
                                res_model: "lessee.info.wizard",
                                res_id: res_id,
                                target: "current",
                                views: [[false, "form"]],
                                context: data.context,
                            });
                        })
                    });
            }
        },
    };

    ListController.include(includeDict);
});
