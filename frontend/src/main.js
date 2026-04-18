import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/theme.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

// Initialize auth store before mounting
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
authStore.initFromStorage()

app.use(router)
app.use(ElementPlus)
app.mount('#app')