import { Outlet } from 'react-router-dom'
import ToastContainer from '@/components/common/ToastContainer'

function App() {
  return (
    <div className="mx-auto w-full max-w-md bg-white">
      <Outlet />
      <ToastContainer />
    </div>
  )
}

export default App
