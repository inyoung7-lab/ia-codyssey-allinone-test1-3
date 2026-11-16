# Mini NPU Simulator

Python 3.8 이상에서 실행하는 표준 라이브러리 기반 MAC 시뮬레이터입니다. 입력 행렬과 패턴의 같은 위치 값을 곱해 누적하고, Cross/X 점수를 비교합니다.

## 실행

프로젝트 루트에서 실행합니다.

```powershell
python main.py
```

메뉴에서 `1`은 사용자 입력 분석, `2`는 `data.json` 분석입니다. 모드 1에서는 다시 직접 입력 또는 3×3 자동 생성 예시를 선택합니다. 모드 2가 읽는 파일은 실행 명령이 가리키는 `main.py`와 같은 디렉터리의 `data.json`입니다. 현재 프로젝트 루트에는 원본 `data.json`이 없습니다.

## 모드 1: 사용자 입력과 자동 생성

직접 입력은 필터 A, 필터 B, 패턴을 각각 3행씩 입력합니다. 각 행은 공백으로 구분된 유한한 숫자 3개여야 하며, 열 수 오류·숫자 오류·NaN·Infinity가 있으면 해당 행만 다시 입력합니다.

예를 들어 필터 A에 Cross, 필터 B에 X, 패턴에 X를 넣을 때 각 행 입력은 다음과 같습니다.

```text
필터 A: 0 1 0 / 1 1 1 / 0 1 0
필터 B: 1 0 1 / 0 1 0 / 1 0 1
패턴:   1 0 1 / 0 1 0 / 1 0 1
```

이 입력은 A 점수 1, B 점수 5, 판정 B를 만듭니다. 자동 생성 예시는 필터 A=Cross, 필터 B=X로 만들고, 입력 패턴은 Cross 또는 X 중 선택합니다. N은 양의 정수이며, X는 두 대각선을 채웁니다. 홀수 Cross는 가운데 행과 열을 채우고, 짝수 Cross는 가운데 두 행과 가운데 두 열을 채웁니다.

## 모드 2: JSON 규칙

`data.json`의 최상위에는 `filters`와 `patterns` 객체를 둡니다. 필터 그룹은 `size_5`, `size_13`, `size_25` 키를 사용하고, 각 그룹에는 `cross`와 `x` 행렬을 둡니다. 각 행렬은 키의 N과 같은 N×N 크기여야 하며 원소는 bool이 아닌 유한한 JSON 숫자여야 합니다.

패턴 키는 `size_{N}_{idx}` 형식입니다. 과제 필수 패턴 입력 키는 `input`이고 각 항목은 `input` 행렬과 `expected`를 가집니다. 이전 파일과의 호환을 위해 `input`이 없을 때만 `matrix`, `pattern`, `data`, `values`를 대체 키로 읽습니다.

```json
{
  "filters": {
    "size_5": {
      "cross": [[0,0,1,0,0], [0,0,1,0,0], [1,1,1,1,1], [0,0,1,0,0], [0,0,1,0,0]],
      "x": [[1,0,0,0,1], [0,1,0,1,0], [0,0,1,0,0], [0,1,0,1,0], [1,0,0,0,1]]
    }
  },
  "patterns": {
    "size_5_1": {"input": [[0,0,1,0,0], [0,0,1,0,0], [1,1,1,1,1], [0,0,1,0,0], [0,0,1,0,0]], "expected": "+"}
  }
}
```

필터 라벨은 소문자 `cross`와 `x`입니다. `expected`의 `+`와 `Cross`는 Cross로, `x`와 `X`는 X로 정규화됩니다. 크기 또는 키 형식 오류, 누락된 필터, 라벨 오류, 행렬 크기 오류, 잘못된 숫자는 영향을 받는 케이스의 FAIL 사유로 기록되고 다음 케이스를 계속 처리합니다.

## 판정과 MAC 비교

판정은 `abs(score_cross - score_x) < 1e-9`일 때만 UNDECIDED입니다. 비교는 엄격한 미만(`<`)이므로 차이가 정확히 `1e-9`인 경우에는 동점으로 처리하지 않습니다. JSON에서 UNDECIDED가 나오면 기대 라벨과 무관하게 FAIL입니다.

2D MAC은 행·열 이중 반복문을 사용하고, 1D MAC은 행 우선 순서로 평탄화한 배열을 단일 반복문으로 누적합니다. 두 방식은 같은 값을 같은 순서로 처리하며, 실행 전에 점수 일치도 확인합니다. 두 MAC은 각각 10회 측정하고 평균을 MAC 1회당 ms로 표시합니다. 입력 검증, 패턴 생성, 평탄화 및 출력은 측정 구간에 포함하지 않습니다. 모드 2 성능표는 3×3, 5×5, 13×13, 25×25에서 Cross 필터와 X 입력 패턴으로 측정합니다.

## 결과 리포트

- 제출 전 구문 검사는 `ast.parse(..., feature_version=(3, 8))`로 수행했고 통과했습니다.
- 구문 검사는 Python 3.12.10에서 실행했습니다. 이는 Python 3.8 문법 파싱 결과이며 Python 3.8 인터프리터에서의 실행 검증을 뜻하지 않습니다.
- 이 환경에는 Python 3.8 실행기가 설치되어 있지 않아 실제 Python 3.8 실행은 확인하지 못했습니다.
- 소스에서 사용하는 `json`, `math`, `os`, `re`, `time`은 표준 라이브러리 모듈이고, 사용 API는 Python 3.8 문서에 있는 `json.load`, `math.isfinite`, `os.path`, `re.compile`/`re.match`, `time.perf_counter`와 기본 내장 함수입니다.
- 허용오차 콘솔 재검증은 직접 입력으로 A=0, B=1e-10을 만들었고 `판정: 판정 불가 (UNDECIDED)`를 출력했습니다.
- 이번 검증은 과제 명세에 맞춘 임시 데이터 검증으로, 새 별도 임시 디렉터리에서 최신 `main.py` 복사본과 `input`만 사용하는 JSON을 함께 실행했습니다.
- 기존 `submission_check_temp\data.json`은 이번 공식 스키마 재검증에 재사용하지 않았습니다.
- 교육 제공 원본 `data.json`은 프로젝트 루트에 없어 별도 원본 검증은 하지 않았고, 루트에 임시 파일을 만들지 않았습니다.
- 과제 명세에 맞춘 임시 데이터 8건은 정상 Cross/X 6건, 4×4 크기 오류 1건, 1e-9 미만 동점 1건으로 구성했습니다.
- 정상 Cross/X 케이스 6건은 모두 PASS했고, 크기 오류와 UNDECIDED 동점은 각각 FAIL로 기록되어 총계는 테스트 8건·통과 6건·실패 2건이었습니다.
- `size_5_3`은 키가 5×5를 요구하지만 `input` 행렬이 4×4여서 FAIL이 됐습니다.
- `size_5_3` 바로 다음 `size_13_1`은 Cross 점수 25, X 점수 1로 PASS 처리되어 크기 오류 뒤에도 처리가 계속됨을 확인했습니다.
- `size_13_3`은 Cross와 X 점수가 모두 0인 UNDECIDED 동점으로 FAIL이 됐고, 이후 25×25의 정상 케이스도 PASS로 처리됐습니다.
- 최종 콘솔은 실패 ID와 각각의 이유를 나열했고, 총계 검사는 8 = 6 + 2로 일치했습니다.
- 기존 커밋 `e84209f`의 `_extract_pattern`은 `raw_pattern.get("matrix")`로 JSON의 실제 `matrix` 키를 읽었고, `.matrix`는 오류 문구에만 쓰인 경로가 아니었습니다.
- 이 제출 직전 수정은 과제 필수 `input`을 먼저 읽고 오류 경로에도 `.input`을 표시합니다. `matrix` 등은 구버전 데이터용 대체 키로만 남겼습니다.
- 스키마 오류를 진단할 때는 최상위 객체, `filters`/`patterns`, `size_N` 및 `size_N_idx` 키, 패턴 `input`, N×N 행 길이, 숫자 원소를 순서대로 확인합니다.
- 라벨 오류를 진단할 때는 필터 키 `cross`/`x`와 패턴 `expected` 값 `+`/`x` 또는 `Cross`/`X`의 위치를 구분해 확인합니다.
- 판정이 예상과 다르면 Cross 점수, X 점수, 정규화된 expected를 함께 비교하고 점수 차이가 1e-9보다 작은지 확인합니다.
- 부동소수점 입력의 수치 비교가 의심되면 같은 데이터를 유지한 채 두 MAC 점수를 확인하고, 이 구현의 비교 기준이 엄격한 `< 1e-9`임을 적용합니다.
- MAC은 각 위치에서 곱하기 한 번과 누적 한 번을 수행하므로 N×N에서 반복 수가 N²인 O(N²) 연산입니다.
- 따라서 크기별 N² 연산 수는 3×3에서 9회, 5×5에서 25회, 13×13에서 169회, 25×25에서 625회입니다.
- 아래 1D 측정 시간은 행렬을 평탄화한 뒤 MAC 함수 호출만 잰 값이며 평탄화 비용을 포함하지 않습니다.
- 성능값은 10회 측정의 MAC 1회당 평균이며 실행 환경과 부하에 따라 달라질 수 있습니다.
- 과제 명세 스키마 최종 검증에서는 3×3, 5×5, 13×13, 25×25 모두 1D 평균이 2D보다 짧게 나왔으며, 표의 실측값을 그대로 기록했습니다.

이번 임시 검증 실행에서 얻은 실제 성능표는 다음과 같습니다.

| 크기 | 반복 횟수 | N² | 2D 평균(ms) | 1D 평균(ms) |
|---|---:|---:|---:|---:|
| 3×3 | 10 | 9 | 0.001470 | 0.000880 |
| 5×5 | 10 | 25 | 0.002520 | 0.001560 |
| 13×13 | 10 | 169 | 0.013880 | 0.008880 |
| 25×25 | 10 | 625 | 0.049990 | 0.036640 |

## 증빙 이미지

아래 화면은 프로젝트 루트의 `docs/screenshots/`에 상대 경로로 보관합니다.

- [직접 입력 오류 복구 후 B 판정](docs/screenshots/01_manual_input_recovery.png)
- [A=0, B=1e-10 허용오차 판정 불가](docs/screenshots/02_epsilon_undecided.png)
- [자동 생성 Cross의 A 판정](docs/screenshots/03_generated_cross.png)
- [공식 `input` JSON 캡처 (8건, 6 PASS·2 FAIL)](docs/screenshots/04_json_and_benchmark.png)

네 PNG의 ZIP은 Windows 다운로드 폴더의 `mini-npu-mission-screenshots.zip`에 있습니다. 원본 PNG는 다운로드 폴더에 보존했습니다.

## VS Code에서 임시 JSON 실행 및 캡처

`submission_check_temp/official_input8/`에는 최신 루트 `main.py` 복사본과 `input` 전용 8건 검증 JSON을 캡처용으로 보관합니다. 상위 폴더의 이전 `submission_check_temp/data.json`은 구버전 `matrix` 키를 쓰는 호환성 샘플이므로 이번 검증에 사용하지 않았습니다.

VS Code PowerShell 터미널에서 다음 두 줄을 실행하면 모드 2가 시작되고 콘솔 출력이 나타납니다.

```powershell
$env:PYTHONIOENCODING = 'utf-8'
Set-Location -LiteralPath 'C:\Users\userr\codyssey\ia-codyssey-allinone-test1-3\submission_check_temp\official_input8'
'2' | python .\main.py
```

Python 3.8 문법과 표준 라이브러리 API 확인은 [Python 3.8 AST 문서](https://docs.python.org/3.8/library/ast.html), [math 문서](https://docs.python.org/3.8/library/math.html), [json 문서](https://docs.python.org/3.8/library/json.html), [time 문서](https://docs.python.org/3.8/library/time.html), [re 문서](https://docs.python.org/3.8/library/re.html)를 참고했습니다.
