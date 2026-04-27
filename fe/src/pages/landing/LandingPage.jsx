import Button from '@/components/common/Button.jsx';

function LandingPage() {


  return (
    <main className="min-h-screen bg-surface-base text-primary-500">
      <Button size="lg" variant="white">
        인스타로 확인하기
      </Button>
      <Button size="lg" variant="primary">
        인스타로 확인하기
      </Button>
      <Button size="sm" variant="white">
        아니오
      </Button>
      <Button size="sm" variant="primary">
        예
      </Button>
      <Button size="sm" variant="navy">
        예
      </Button>
    </main>
  )
}

export default LandingPage
