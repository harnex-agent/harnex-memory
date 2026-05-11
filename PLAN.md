# harnex-memory PLAN

## 목표

`harnex-memory`는 harnex의 다른 모듈들이 쉽게 호출할 수 있도록 가장 하위 의존성에 위치하는 memory 기반 모듈이다. skill/rule/hook 문서를 관리하고, 추후 반복 프롬프트를 감지해 관련 내용을 문서에 반영할 수 있도록 Python API와 Typer CLI를 함께 제공한다.

상위 harnex 구조에서 `harnex-memory`는 다음 책임을 가진다.

- `harnex-clarify`, `harnex-verify`, GUI, 에이전트 어댑터가 공통으로 호출할 수 있는 memory API를 제공한다.
- 프로젝트의 skill/rule/hook 문서를 조회, 생성, 수정, 미리보기, 적용한다.
- 다른 모듈이 전달한 프롬프트와 memory event를 기록할 수 있는 최소 계약을 제공한다.
- 반복 프롬프트가 누적되면 skill/rule/hook 문서 반영 후보를 만들 수 있도록 확장 지점을 둔다.
- 문서 변경안을 diff 또는 preview 형태로 보여준다.
- 사용자의 승인 이후에만 프로젝트 파일 시스템에 변경을 적용한다.
- 다른 모듈, CLI, GUI, 테스트가 같은 core 로직을 재사용할 수 있도록 공개 API와 Typer entrypoint를 업무 로직에서 분리한다.

## 초기 범위

1. 프로젝트 및 API 골격 구성
   - `uv` 기반 Python 프로젝트로 구성한다.
   - CLI 프레임워크는 Typer를 사용한다.
   - 테스트는 pytest, 린트/포맷은 Ruff를 사용한다.
   - Typer command는 얇게 유지하고 실제 로직은 `harnex_memory.core` 아래에 둔다.
   - 다른 harnex 모듈이 subprocess 없이 호출할 수 있는 Python API를 `harnex_memory.api`에서 제공한다.

2. skill/rule/hook 문서 관리
   - 프로젝트 루트 아래의 skill/rule/hook 문서 위치를 찾고 목록화한다.
   - 문서가 없을 때 생성 가능한 기본 경로와 템플릿을 제공한다.
   - 문서 내용을 구조화된 모델로 읽고, 변경 요청을 안전한 patch 후보로 만든다.

3. Prompt memory 계약 정의
   - 반복 프롬프트 감지를 위해 `prompt`, `source`, `project_root`, `timestamp`, `metadata`를 기록할 수 있게 한다.
   - `clarify.json`, `agent-result.json`, `verify.json` 같은 세션 산출물 파일은 기본 입력으로 요구하지 않는다.
   - 다른 모듈이 필요하다고 판단한 정보만 memory event의 metadata로 전달할 수 있게 한다.
   - 저장 형식은 초기에는 JSONL 또는 SQLite 중 하나를 선택하되, API 계약은 저장소 구현에 묶이지 않게 한다.

4. Memory 후보 생성
   - 반복 프롬프트 후보를 감지한다.
   - skill/rule/hook 문서에 반영할 후보를 만든다.
   - 후보마다 근거, 변경 대상, 위험도를 함께 기록한다.
   - 초기 구현에서는 후보 생성과 preview까지를 우선하고, 자동 적용은 별도 승인 흐름 뒤에만 수행한다.

5. Preview 및 diff
   - 실제 파일을 수정하기 전에 preview JSON을 생성한다.
   - Markdown 문서 변경안은 적용 전 diff로 확인할 수 있게 한다.
   - GUI가 표시하기 쉬운 JSON 형식을 유지한다.

6. 승인 기반 적용
   - 기본 실행은 preview 생성까지만 수행한다.
   - 명시적인 apply 옵션이 있을 때만 파일을 변경한다.
   - symlink와 상대 경로를 해석한 최종 경로가 프로젝트 루트 밖이면 접근을 거부한다.

## 예상 디렉터리 구조

```text
harnex-memory/
  pyproject.toml
  README.md
  src/
    harnex_memory/
      __init__.py
      api.py
      cli.py
      core/
        __init__.py
        documents.py
        models.py
        prompt_store.py
        analyzer.py
        preview.py
        apply.py
        paths.py
  tests/
    test_api.py
    test_documents.py
    test_prompt_store.py
    test_analyzer.py
    test_preview.py
    test_paths.py
```

## CLI 초안

```text
harnex-memory docs list --project-root <path>
harnex-memory docs preview --project-root <path> --target <skill|rule|hook> --content <path>
harnex-memory docs apply --project-root <path> --preview <path>
harnex-memory prompt record --project-root <path> --source <source> --prompt <text>
harnex-memory prompt suggest --project-root <path>
```

- `docs list`: 프로젝트의 skill/rule/hook 문서 상태를 조회한다.
- `docs preview`: 문서 변경안을 만들고 diff를 포함한 preview를 생성한다.
- `docs apply`: 승인된 preview를 바탕으로 파일 변경을 적용한다.
- `prompt record`: 다른 모듈에서 들어온 프롬프트를 memory store에 기록한다.
- `prompt suggest`: 반복 프롬프트를 분석해 skill/rule/hook 반영 후보를 생성한다.

## 산출물

```text
.harnex/
  memory/
    prompt-records.jsonl
    previews/
      <preview-id>.json
    apply-results/
      <apply-id>.json
```

preview JSON에는 다음 정보를 담는다.

- schema version
- project root
- preview id
- 변경 요청 출처
- memory 후보 목록
- 변경 예정 파일 목록
- 파일별 unified diff
- 적용 전 경고 및 차단 사유

## 보안 및 안정성 원칙

- 사용자가 지정한 project root와 그 하위만 읽고 쓴다.
- 최종 해석된 경로가 project root 밖이면 실패 처리한다.
- 기본 명령은 파일을 수정하지 않는다.
- 적용 결과는 `.harnex/memory/apply-results/` 아래에 남긴다.
- 오류는 GUI에서 표시하기 쉬운 구조화된 JSON으로 출력한다.

## 테스트 계획

- 다른 harnex 모듈에서 호출할 공개 API 테스트
- skill/rule/hook 문서 탐색 및 생성 테스트
- prompt record 저장 및 조회 테스트
- 반복 프롬프트 후보 추출 테스트
- preview JSON 생성 테스트
- unified diff 생성 테스트
- project root 밖 경로 차단 테스트
- apply 명령이 승인된 파일만 변경하는지 검증하는 테스트

## 마일스톤

1. 프로젝트 스캐폴딩과 기본 CLI entrypoint 작성
2. skill/rule/hook 문서 탐색 및 관리 API 구현
3. prompt memory 기록 API와 저장소 구현
4. 반복 프롬프트 기반 memory 후보 분석기 구현
5. preview JSON 및 diff 생성기 구현
6. 승인 기반 apply 구현
7. pytest/Ruff 검증 파이프라인 정리
8. 다른 harnex 모듈과 GUI 연동을 위한 API/출력 포맷 고정

