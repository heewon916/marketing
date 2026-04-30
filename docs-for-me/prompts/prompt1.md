[팀 규칙]

1. 외부 접속 주소는 http://k14a401.p.ssafy.io 입니다.

2. 백엔드 API는 /api 경로로 호출합니다.
   예: http://k14a401.p.ssafy.io/api/...

3. Docker 내부에서 Spring은 FastAPI를 http://fastapi:8000 으로 호출합니다.

4. Spring에서 PostgreSQL은 postgres:5432 로 연결합니다.

5. Spring에서 Redis는 redis:6379 로 연결합니다.

6. .env는 GitLab에 올리지 않습니다.

7. 환경변수가 추가되면 Notion에 즉시 공유하고, 인프라 담당자에게 알려야 합니다.

8. 인프라 담당자가 Jenkins Credentials의 marketing-env 값을 수정합니다.

9. .env.example은 실제 실행용이 아니라 필요한 환경변수 목록을 알려주는 템플릿입니다.

10. develop에 merge되면 Jenkins가 자동으로 개발 서버를 재배포합니다.

11. develop을 master에 merge하면 Jenkins가 master 기준으로 최종 배포합니다.

[커밋 규칙]
## Commit Convention

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

**공통 작업의 경우** 다음 scope를 사용할 수 있다
