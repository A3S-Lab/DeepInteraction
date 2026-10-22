import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'defaultpage',
      redirect: '/homepage'
    },
    {
      path: '/homepage',
      name: 'homepage',
      component: () => import('@/views/homepage.vue')
    },
    {
      path: '/chatdetail',
      name: 'chatdetail',
      component: () => import('@/views/chatDetail.vue')
    }
  ]
})

export default router