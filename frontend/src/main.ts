import { createApp } from "vue"

import App from "./App.vue"
import "./index.css"
import { router } from "./router"
import { startVideoPreloadQueue } from "./services/videoAssets"

createApp(App).use(router).mount("#app")
startVideoPreloadQueue()
