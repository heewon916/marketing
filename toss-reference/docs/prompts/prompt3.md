> [!NOTE] 토스 POS 플러그인 - Iframe 패키지 방식 개발 가이드
>
> ## 개요  
> Iframe 패키지 방식은 토스 POS 탭 화면에서 웹뷰 기반 iframe으로 UI를 렌더링하는 방식이다.  
> POS 내부 웹뷰에서 실행되며, DOM 기반 UI 개발이 가능하다.  
>
> ---
>
> ## 1. 시작하기  
> ### 1.1 설치  
> ```bash
> npm install
> npm install @tossplace/pos-plugin-sdk@latest
> ```
>
> ---
>
> ## 2. 프로젝트 구조  
> ```text
> project/
>  ├── src/
>  │   └── App.tsx
>  ├── public/
>  │   └── iframe-manifest.json
>  └── package.json
> ```
>
> ---
>
> ## 3. 주요 파일 설명  
> ### App.tsx  
> - UI 렌더링  
> - 이벤트 처리  
> - API 호출 및 상태 관리  
>
> ### iframe-manifest.json  
> ```json
> {
>   "tab": {
>     "title": "탭 이름",
>     "description": "탭 설명"
>   }
> }
> ```
> - POS에 표시되는 탭 정보 정의  
>
> ---
>
> ## 4. 실행 흐름  
> 1. POS에서 탭 클릭  
> 2. iframe 로드  
> 3. App 실행  
> 4. 사용자 입력  
> 5. SDK/API 호출  
> 6. UI 업데이트  
>
> ---
>
> ## 5. 개발 포인트  
> - iframe 내부에서 UI 동작  
> - SDK 기반 POS 연동  
> - 비동기 처리 필수  
> - 로딩/에러 상태 관리 필요  
>
> ---
>
> ## 6. 빌드 및 배포  
> ```bash
> npm run build
> ```
> 1. dist 생성  
> 2. zip 압축  
> 3. 개발자센터 업로드  
>
> ---
>
> ## 결론  
> iframe 방식은 UI 중심 플러그인 개발에 적합하며,  
> 사용자 인터랙션이 필요한 기능 구현 시 사용한다.