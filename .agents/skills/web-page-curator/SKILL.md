---
name: web-page-curator
description: >-
  Use this skill when the user asks to search the internet, discover, verify,
  and compile a curated list of web pages or URLs that contain specific
  information, topics, documentation, or rules.
---

# Web Page Curator Skill

인터넷에서 사용자가 필요로 하는 특정 주제나 정보를 담고 있는 웹페이지를 탐색하고, 실제 페이지 접속 및 본문 검증을 거쳐 신뢰할 수 있는 **웹페이지 목록(URL 디렉터리)**을 생성하는 워크플로우입니다.

---

## Workflow Steps

### 1. 탐색 조건 정의 (Define Search Criteria)
사용자의 요청에서 다음 항목을 파악합니다. 불명확한 경우 짧게 질문하여 확정합니다.
* **핵심 주제 및 필수 포함 내용**: 페이지 본문에 반드시 포함되어야 하는 정보나 키워드
* **우선/제외 도메인 및 언어**: 공식 문서, 국가/기관 사이트 등 우선할 도메인이나 제외할 사이트(단순 펌글, 광고성 블로그 등)
* **목표 수집 개수 및 출력 파일 경로**: 기본값은 워크스페이스 내 `curated_pages.md` (또는 사용자가 지정한 경로)

### 2. 다각도 후보 URL 탐색 (Multi-Angle Discovery)
`search_web` 도구를 사용하여 단일 검색어에 의존하지 않고 다양한 각도에서 후보 URL을 수집합니다.
1. **기본 키워드 검색**: 핵심 주제어로 검색하여 대표 페이지 확보
2. **세부/동의어 확장 검색**: 관련 전문 용어, 영문/국문 키워드, 하위 주제어로 추가 검색
3. **도메인 지정 검색**: 특정 신뢰 도메인이 확인되면 `search_web`의 `domain` 파라미터를 활용해 심층 탐색

### 3. URL 상태 및 본문 적합성 검증 (Verify URLs & Content)
검색 결과 요약만 믿지 않고, 수집한 후보 URL이 실제로 유효하며 필요한 내용을 담고 있는지 검증합니다.
* 헬퍼 스크립트 [verify_urls.py](./scripts/verify_urls.py)를 실행하여 후보 URL들의 HTTP 응답 상태, 리다이렉트 여부, 페이지 제목(`<title>`), 본문 내 핵심 키워드 포함 여부를 일괄 확인합니다.
  ```bash
  python3 .agents/skills/web-page-curator/scripts/verify_urls.py \
    --urls "https://example.com/page1" "https://example.com/page2" \
    --keywords "필수키워드1" "필수키워드2"
  ```
* **검증 기준**:
  * HTTP 4xx/5xx 에러 페이지나 빈 페이지는 목록에서 제외합니다.
  * 동일 페이지로 리다이렉트되거나 중복된 URL은 정규화(Canonical URL)하여 하나로 병합합니다.
  * CAPTCHA나 봇 차단(Cloudflare Turnstile 등)으로 보호된 페이지는 우회하지 않고, 목록의 비고란에 `직접 브라우저 확인 필요(접근 제한)`으로 명시합니다.

### 4. 웹페이지 목록 문서 작성 (Generate Curated List)
검증을 통과한 웹페이지들을 카테고리 또는 중요도 순으로 분류하여 문서화합니다.
* 기본 출력 양식은 [page_list_template.md](./resources/page_list_template.md) 템플릿을 따릅니다.
* 각 항목에는 **페이지 제목**, **클릭 가능한 URL**, **핵심 내용 요약(필요한 정보가 어디에 어떻게 있는지)**, **신뢰도/출처 구분**, **검증 상태**를 포함합니다.

### 5. 최종 결과 검증 (Final Validation)
파일을 저장한 뒤 다음 사항을 점검하고 사용자에게 완료를 보고합니다.
* 생성된 파일에 깨진 마크다운 링크나 누락된 URL이 없는지 확인
* 사용자가 요청한 필수 정보가 포함된 페이지들만 선별되었는지 요약 브리핑 제공
