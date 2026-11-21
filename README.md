# Mini NPU Simulator

[실습·발표 가이드](docs/mission-guide.md)에서 시연 순서, 입력값, 설명 대본을 확인할 수 있습니다.

Python 3.8 이상, 표준 라이브러리만으로 실행하는 MAC 시뮬레이터입니다. 같은 위치의 필터와 패턴 값을 곱해 누적하고 Cross/X 점수를 비교합니다.

## 실행 방법

프로젝트 루트에서 실행합니다. `data.json`은 `main.py`와 같은 디렉터리에 둡니다.

```powershell
python main.py
```

메뉴에서 `1`은 3×3 사용자 입력, `2`는 루트 `data.json` 분석입니다. 모드 1 안에서 `1`은 직접 행렬 입력, `2`는 자동 생성 예시입니다.

## 모드 1: 직접 입력과 패턴 생성

직접 입력은 필터 A, 필터 B, 패턴을 각각 3행씩 받습니다. 각 행에는 공백으로 구분한 숫자 3개를 입력합니다. 빈 행, 숫자 개수 오류, 문자, NaN, Infinity는 오류 안내 후 같은 행에서 재입력합니다.

예를 들어 필터 A=Cross, 필터 B=X, 입력 패턴=X는 다음과 같습니다.

```text
필터 A: 0 1 0 / 1 1 1 / 0 1 0
필터 B: 1 0 1 / 0 1 0 / 1 0 1
패턴:   1 0 1 / 0 1 0 / 1 0 1
```

점수는 A=1, B=5이며 판정 B입니다. 자동 생성 예시는 필터 A를 Cross, 필터 B를 X로 만들고 입력 패턴을 Cross 또는 X로 선택합니다. 생성 함수는 양의 정수 N을 받습니다. X는 두 대각선을 채우며, 홀수 Cross는 가운데 행과 열을 채우고 짝수 Cross는 가운데 두 행과 두 열을 사용합니다.

## 모드 2: JSON 형식과 데이터 출처

루트 `data.json`은 과제 자료로부터 받은 것이 아니라 이 저장소에 직접 만든 정상 실행용 샘플입니다. 교육 제공 원본 파일은 이 작업 시작 시 프로젝트 루트에서 발견되지 않았습니다. 샘플은 `size_5`, `size_13`, `size_25` 필터 그룹을 모두 포함하고 각 그룹에 `cross`, `x` 행렬을 둡니다. 패턴 키는 `size_{N}_{idx}`이고 각 항목은 과제 필수 `input` 행렬과 `expected`를 가집니다.

`expected`의 `+`는 Cross로, `x`는 X로 정규화됩니다. 행렬 크기는 키의 N×N이어야 하고 원소는 bool이 아닌 유한한 JSON 숫자여야 합니다.

루트 샘플의 각 크기에는 Cross 입력과 X 입력이 하나씩 있어 정상 케이스는 총 6건입니다. `data.json`을 직접 열면 전체 필터와 6개 패턴을 확인할 수 있습니다.

### 오류 케이스 6 PASS·2 FAIL 재현

루트 샘플을 보존한 상태로 오류 포함 검증을 재현하려면 아래 스크립트로 `size_5_3`의 4×4 오류 케이스와 `size_13_3`의 0점 동점 케이스를 삽입합니다. 두 케이스는 각 크기의 정상 케이스 사이에 들어가 후속 처리를 확인할 수 있습니다.

```powershell
@'
import json
from pathlib import Path

path = Path("data.json")
document = json.loads(path.read_text(encoding="utf-8"))
updated = {}
for case_id, case in document["patterns"].items():
    updated[case_id] = case
    if case_id == "size_5_2":
        updated["size_5_3"] = {
            "input": [[0, 1, 1, 0], [1, 1, 1, 1], [1, 1, 1, 1], [0, 1, 1, 0]],
            "expected": "+",
        }
    if case_id == "size_13_2":
        updated["size_13_3"] = {"input": [[0] * 13 for _ in range(13)], "expected": "+"}
document["patterns"] = updated
path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
'@ | python
'2' | python .\main.py
git restore -- data.json
```

오류 포함 실행은 8건 중 정상 6건 PASS, 2건 FAIL을 예상합니다. `size_5_3`은 `input` 크기가 4×4라 실패하고, 다음 `size_13_1`은 PASS로 계속 처리됩니다. `size_13_3`은 Cross/X 점수가 모두 0이어서 UNDECIDED FAIL이며, 그 다음 25×25 정상 케이스는 PASS입니다. 확인 후 `git restore -- data.json`으로 자체 샘플을 복구합니다.

## 판정과 성능 측정

판정 기준은 `abs(score_cross - score_x) < 1e-9`입니다. 차이가 1e-9보다 작을 때만 UNDECIDED이며, 정확히 1e-9이면 동점이 아니므로 높은 점수 쪽으로 판정합니다.

2D MAC은 행·열 이중 반복문을 사용합니다. 1D MAC은 행 우선으로 평탄화한 필터와 패턴 배열을 단일 반복문으로 계산합니다. 평탄화 길이는 각각 N²입니다. 두 구현은 같은 값과 순서를 사용하며, 실행 전 점수 일치도 확인합니다.

각 구현을 10회 측정하고 평균을 MAC 1회당 ms로 표시합니다. 패턴 생성, 행렬 검증, 평탄화, 점수 일치 확인 및 출력은 시간 구간 밖에 있고, 측정 구간에는 MAC 함수 호출만 들어갑니다. 시간 값은 실행 환경과 부하에 따라 달라질 수 있습니다.

각 MAC 위치에서 곱하기와 누적을 한 번씩 하므로 계산량은 O(N²)입니다. 3×3, 5×5, 13×13, 25×25의 반복 수는 각각 9, 25, 169, 625입니다.

## 검증 결과 리포트

- 과제 명세에 맞춘 정상 샘플은 저장소에서 직접 만든 `data.json`으로 검증했습니다.
- 정상 샘플의 size 5·13·25 Cross/X 케이스는 6건 모두 PASS, FAIL 0건이었습니다.
- 오류 포함 검증은 위 명령으로 4×4 오류와 epsilon 동점 케이스를 추가해 8건으로 재현할 수 있습니다.
- 오류 포함 결과는 PASS 6건, FAIL 2건이며 총계 확인은 일치합니다.
- `size_5_3` 실패 사유는 5×5 키에 4×4 `input`을 넣은 크기 불일치입니다.
- `size_5_3` 뒤의 `size_13_1`이 PASS해 개별 케이스 오류 후에도 분석이 이어집니다.
- `size_13_3`은 두 점수 0의 동점이므로 UNDECIDED 및 FAIL입니다.
- 잘못된 `expected`는 라벨 오류로, 패턴 `input` 누락은 입력 필드 누락으로 케이스별 기록됩니다.
- Cross/X 필터가 빠지면 그 크기를 사용하는 케이스에 필터 누락 이유가 표시되고 다른 크기의 케이스는 계속 실행됩니다.
- 파일 없음과 잘못된 JSON은 이유를 안내하고 프로세스가 정상 종료하는 것을 별도로 확인했습니다.
- 직접 입력에서는 빈 행, 숫자 개수 오류, 문자 입력 후 같은 행에서 복구해 다음 행렬까지 완료했습니다.
- epsilon 1e-10 사례는 판정 불가, 정확히 1e-9인 사례는 B 점수가 높은 것으로 판정됐습니다.
- 기존 1e-10 증빙은 [02_epsilon_undecided.png](docs/screenshots/02_epsilon_undecided.png)에서 확인할 수 있습니다.
- 자동 생성 Cross는 A=5/B=1로 A, 자동 생성 X는 A=1/B=5로 B 판정됐습니다.
- `generate_pattern`은 모드 1 자동 생성과 3/5/13/25 성능 입력 생성에서 함께 사용됩니다.
- 네 크기 모두 2D·1D 점수가 일치했고 각 구현은 동일 입력으로 10회 측정됐습니다.
- 측정값은 MAC 호출만 포함하며 평탄화 비용을 제외합니다.
- 이전 오류 포함 실행 화면은 [04_json_and_benchmark.png](docs/screenshots/04_json_and_benchmark.png)입니다.
- 직접 입력 복구와 자동 생성 Cross 증빙은 [01_manual_input_recovery.png](docs/screenshots/01_manual_input_recovery.png), [03_generated_cross.png](docs/screenshots/03_generated_cross.png)에서 확인할 수 있습니다.
- Python 3.12.10에서 실행했고 `ast.parse(feature_version=(3, 8))` 문법 검사를 통과했습니다.
- 이 환경에는 Python 3.8 인터프리터가 없어 실제 Python 3.8 실행 검증은 하지 않았습니다.

이번 루트 정상 샘플 실행에서 얻은 실제 성능표입니다.

| 크기 | 반복 횟수 | N² | 2D 평균(ms) | 1D 평균(ms) |
|---|---:|---:|---:|---:|
| 3×3 | 10 | 9 | 0.000810 | 0.000450 |
| 5×5 | 10 | 25 | 0.001490 | 0.000900 |
| 13×13 | 10 | 169 | 0.007850 | 0.005220 |
| 25×25 | 10 | 625 | 0.027200 | 0.020410 |

## 증빙 이미지

- [직접 입력 오류 복구 후 B 판정](docs/screenshots/01_manual_input_recovery.png)
- [A=0, B=1e-10 허용오차 판정 불가](docs/screenshots/02_epsilon_undecided.png)
- [자동 생성 Cross의 A 판정](docs/screenshots/03_generated_cross.png)
- [오류 포함 JSON 검증 8건](docs/screenshots/04_json_and_benchmark.png)
