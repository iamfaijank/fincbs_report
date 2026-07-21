import { createRouter, createWebHistory } from "vue-router"

const routes = [
	{
		path: "/",
		component: () => import("@/pages/Home.vue"),
		children: [
			{
				path: "",
				name: "Dashboard",
				component: () => import("@/pages/Dashboard.vue"),
			},
		],
	},
]

let router = createRouter({
	history: createWebHistory("/drishti"),
	routes,
})

export default router
