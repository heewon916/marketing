import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import './styles/globals.css'
import { router } from './routes/Router.jsx'
import { initForegroundMessage } from './lib/firebase'
import './lib/PwaUpdate'
import AppUpdatingOverlay from './components/common/AppUpdatingOverlay'

void initForegroundMessage()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router} />
    <AppUpdatingOverlay />
  </StrictMode>,
)
