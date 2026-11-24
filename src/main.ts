import '@fontsource-variable/source-sans-3'
import '@fontsource-variable/source-serif-4'
import './styles/base.css'

import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'

createApp(App).use(router).mount('#app')
