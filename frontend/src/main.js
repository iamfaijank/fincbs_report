import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"

import {
	Button,
	Input,
	setConfig,
	frappeRequest,
	resourcesPlugin,
	FormControl,
} from "frappe-ui"

import "./index.css"
import "./theme.css"

const app = createApp(App)

setConfig("resourceFetcher", frappeRequest)
app.use(resourcesPlugin)

app.component("Button", Button)
app.component("Input", Input)
app.component("FormControl", FormControl)

app.use(router)

router.isReady().then(async () => {
	if (import.meta.env.DEV) {
		await frappeRequest({
			url: "/api/method/custom_report.www.drishti.get_context_for_dev",
		}).then(async (values) => {
			if (!window.frappe) window.frappe = {}
			window.frappe.boot = values
		})
	}

	app.mount("#app")
})
