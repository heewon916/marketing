import { Outlet } from 'react-router-dom'

function App() {
  return (
    <div className="mx-auto w-full max-w-md bg-white">
      <Outlet />
    </div>
  )
}

export default App
