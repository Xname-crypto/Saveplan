import { createApp } from "vue"

import App from "./App.vue"
import "./index.css"
import { router } from "./router"
import { initializeTheme } from "./services/theme"
import { startVideoPreloadQueue } from "./services/videoAssets"

initializeTheme()
createApp(App).use(router).mount("#app")
startVideoPreloadQueue()
