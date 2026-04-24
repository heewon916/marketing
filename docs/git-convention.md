## 1. Branch Convention

### 기본 브랜치

| 브랜치 | 설명 |
| --- | --- |
| `master` | 배포 기준 브랜치 |
| `develop` | 개발 통합 브랜치 |
- `master`, `develop`에는 직접 push하지 않는다.
- 모든 작업은 `develop`에서 브랜치를 생성한다.
- 작업 완료 후 MR을 통해 `develop`에 병합한다.

---

## 2. Branch Naming Rule

### 브랜치명 형식

```
<type>/<part>/<domain>/<ticket_number>
```

### 예시

```markdown
feature/be/user/S14P31A401-2
fix/be/auth/S14P31A401-3
chore/fe/init/S14P31A401-4
refactor/ai/post/S14P31A401-5
docs/common/convention/S14P31A401-6
```

### Type

| type | 설명 |
| --- | --- |
| `feature` | 새로운 기능 개발 |
| `fix` | 버그 수정 |
| `refactor` | 리팩토링 |
| `chore` | 설정, 빌드, 패키지 등 기타 작업 |
| `docs` | 문서 작업 |
| `test` | 테스트 코드 작업 |

### Part

| part | 설명 |
| --- | --- |
| `fe` | Frontend |
| `be` | Backend |
| `ai` | AI |
| `db` | 필요시 생성 |
| `crawler` | 필요시 생성 |
| `common` | 필요시 생성 |

### Domain

작업 대상 도메인 또는 기능 단위를 작성한다.

```markdown
user
auth
home
post ; 발행 
generate ; 생성-> contents
alarm
analytics

```


---

## 3. Commit Convention

### 커밋 메시지 형식

```
<type>(<scope>): <commit message> (<ticket_number>)
```

### 예시

```
feat(user): 회원가입 API 구현 (S14P31A401-2)
fix(auth): 리프레시 토큰 만료 설정 수정 (S14P31A401-3)
docs(convention): Git 컨벤션 문서 작성 (S14P31A401-4)
```

### commit type

| type | 설명 |
| --- | --- |
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `refactor` | 리팩토링 |
| `chore` | 기타 변경 사항 |
| `docs` | 문서 수정 |
| `test` | 테스트 코드 추가/수정 |
| `style` | 코드 포맷팅 |
| `comment` | 주석 추가/변경 |
| `ci` | CI/CD 설정 |
| `build` | 빌드 관련 작업 |

### scope

브랜치의 `domain`과 동일하게 작성하는 것을 권장한다.

```
feat(user): 회원가입 API 구현 (S14P31A401-2)
fix(auth): 로그인 토큰 검증 오류 수정 (S14P31A401-3)
```

**공통 작업의 경우** 다음 scope를 사용할 수 있다.

```
chore(fe): 프론트엔드 초기 세팅 (S14P31A401-4)
chore(be): 백엔드 초기 세팅 (S14P31A401-5)
docs(convention): Git 컨벤션 문서 작성 (S14P31A401-6)
```

---

## 4. Merge Request Convention

### MR 제목 형식

```
[<Part>/<type>] <작업 내용>
```

### 예시

```
[Back/feat] 유저 회원가입 API 구현
[Back/fix] 리프레시 토큰 만료 오류 수정
[Front/chore] 프론트엔드 초기 프로젝트 설정
[AI/refactor] 추천 로직 서비스 계층 분리
[Docs/docs] Git 컨벤션 문서 작성
```

### Part 표기

| part | MR 표기 |
| --- | --- |
| `fe` | `Front` |
| `be` | `Back` |
| `ai` | `AI` |
| `db` | `DB` |
| `crawler` | `Crawler` |
| `common` | `Common` |
| `docs` | `Docs` |

### MR 템플릿 

```markdown
<!-- 기본 MR 템플릿 -->
## 💡 개요 (Overview)
> 이 코드가 '왜' 작성되었는지 한 줄로 파악하게 합니다.

## 📃 작업 내용 (Details)
- [ ] 작업 내용 1
- [ ] 작업 내용 2

## 🔗 Jira (Links)
- [티켓번호 - 숫자](해당 url)

## 📸 스크린샷 (Screenshots)

## 📚 테스트 (Test)
- [ ] 로컬 환경에서 기능 테스트 완료
- [ ] 기존 기능에 영향 없는지 확인 완료
```

---

## 5. Sync Merge Message Convention

작업 브랜치에서 최신 `develop`을 병합할 때 사용한다.

### 형식

```
Sync : 최신 develop 브랜치와 동기화
```

### 예시

```
git checkout feature/be/user/S14P31A401-2
git pull origin develop
```

또는

```
git checkout develop
git pull origin develop

git checkout feature/be/user/S14P31A401-2
git merge develop
```

이때 merge commit 메시지는 다음과 같이 작성한다.

```
Sync : 최신 develop 브랜치와 동기화
```

---

## 6. 작업 흐름

```
develop
  └── feature/be/user/S14P31A401-2
        └── MR → develop
```

1. Jira 티켓을 생성한다.
2. `develop`에서 해당 티켓의 작업 브랜치를 생성한다.

```
git checkout develop
git pull origin develop
git checkout-b feature/be/user/S14P31A401-2
```

1. 작업 후 커밋한다.

```
git commit-m"feat(user): 회원가입 API 구현 (S14P31A401-2)"
```

1. 원격 브랜치에 push한다.

```
git push origin feature/be/user/S14P31A401-2
```

1. MR을 생성한다.
2. 리뷰어를 지정한다.
3. 1명 이상의 리뷰 후 `develop`에 병합한다.
4. 병합 완료 후 작업 브랜치를 삭제한다.

```

Branch  : feature/be/user/S14P31A401-2
Commit  : feat(user): 회원가입 API 구현 (S14P31A401-2)
MR      : [Back/feat] 유저 회원가입 API 구현
Merge   : Merge : [Back/feat] 유저 회원가입 API 구현
Sync    : Sync : 최신 develop 브랜치와 동기화
```