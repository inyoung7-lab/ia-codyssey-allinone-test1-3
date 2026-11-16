"""Mini NPU Simulator with interactive and JSON analysis modes."""

import json
import math
import os
import re
import time


SIZE = 3
UNDECIDED_THRESHOLD = 1e-9
MAC_TIMING_RUNS = 10
JSON_SIZES = (3, 5, 13, 25)
PATTERN_KEY = re.compile(r"^size_(\d+)_(\d+)$")


def validate_square_matrix(matrix, name="행렬"):
    """Validate a non-empty square matrix; call outside timed MAC runs."""
    if not matrix:
        raise ValueError("{}는 비어 있을 수 없습니다.".format(name))
    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise ValueError("{}는 정사각형이어야 합니다.".format(name))
    for row in matrix:
        for value in row:
            if not math.isfinite(value):
                raise ValueError("{}에는 유한한 숫자만 사용할 수 있습니다.".format(name))
    return size


def mac(matrix, pattern):
    """Multiply values at matching positions and accumulate an n-by-n score."""
    score = 0.0
    for row in range(len(matrix)):
        for column in range(len(matrix[row])):
            score += matrix[row][column] * pattern[row][column]
    return score


def mac_1d(filter_values, pattern_values):
    """Multiply and accumulate equal-position values in flattened arrays."""
    score = 0.0
    for index in range(len(filter_values)):
        score += filter_values[index] * pattern_values[index]
    return score


def flatten_matrix(matrix):
    """Flatten a matrix in row-major order; call after validating its shape."""
    return [value for row in matrix for value in row]


def generate_pattern(size, label):
    """Create a Cross or X matrix. Even Cross uses both center rows/columns."""
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("N은 양의 정수여야 합니다.")
    normalized = {"+": "Cross", "cross": "Cross", "x": "X"}.get(
        label.strip().lower() if isinstance(label, str) else label
    )
    if normalized is None:
        raise ValueError("패턴은 Cross 또는 X여야 합니다.")

    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    if normalized == "Cross":
        centers = (size // 2,) if size % 2 else (size // 2 - 1, size // 2)
        for center in centers:
            for index in range(size):
                matrix[center][index] = 1.0
                matrix[index][center] = 1.0
    else:
        for index in range(size):
            matrix[index][index] = 1.0
            matrix[index][size - index - 1] = 1.0
    return matrix


def _measure_mac_pair(matrix, pattern, repeats=MAC_TIMING_RUNS):
    """Return paired average times; setup and score equivalence are untimed."""
    size = validate_square_matrix(matrix, "필터")
    if validate_square_matrix(pattern, "패턴") != size:
        raise ValueError("필터와 패턴 크기가 같아야 합니다.")
    flat_matrix = flatten_matrix(matrix)
    flat_pattern = flatten_matrix(pattern)
    if len(flat_matrix) != len(flat_pattern):
        raise ValueError("평탄화한 필터와 패턴 길이가 같아야 합니다.")

    score_2d = mac(matrix, pattern)
    score_1d = mac_1d(flat_matrix, flat_pattern)
    if score_2d != score_1d:
        raise ValueError("2D와 1D MAC 점수가 일치하지 않습니다.")

    times_2d = []
    times_1d = []
    for _ in range(repeats):
        started = time.perf_counter()
        mac(matrix, pattern)
        times_2d.append(time.perf_counter() - started)

        started = time.perf_counter()
        mac_1d(flat_matrix, flat_pattern)
        times_1d.append(time.perf_counter() - started)
    average_2d = sum(times_2d) / repeats * 1000.0
    average_1d = sum(times_1d) / repeats * 1000.0
    return average_2d, average_1d


def _print_mac_comparison_header():
    print("평균은 MAC 1회당 시간이며, 평탄화 비용은 측정에서 제외합니다.")
    print("크기 | 반복 횟수 | N² | 2D 평균(ms) | 1D 평균(ms)")


def _print_mac_comparison_row(size, average_2d, average_1d):
    print("{}x{} | {} | {} | {:.6f} | {:.6f}".format(
        size, size, MAC_TIMING_RUNS, size * size, average_2d, average_1d
    ))


def read_matrix(label):
    print("{}를 입력하세요 (각 행에 공백으로 구분된 숫자 3개).".format(label))
    matrix = []
    for row_index in range(SIZE):
        while True:
            raw = input("{} {}행: ".format(label, row_index + 1))
            parts = raw.split()
            if len(parts) != SIZE:
                print("오류: 한 행에 숫자 3개를 입력하세요. 다시 입력해 주세요.")
                continue
            try:
                values = [float(part) for part in parts]
            except ValueError:
                print("오류: 숫자로 읽을 수 없는 값이 있습니다. 다시 입력해 주세요.")
                continue
            if not all(math.isfinite(value) for value in values):
                print("오류: NaN과 Infinity를 포함한 유한하지 않은 값은 사용할 수 없습니다. 다시 입력해 주세요.")
                continue
            matrix.append(values)
            break
    print("{} 저장 완료".format(label))
    return matrix


def decide(score_a, score_b):
    if abs(score_a - score_b) < UNDECIDED_THRESHOLD:
        return "UNDECIDED"
    return "Cross" if score_a > score_b else "X"


def run_user_input_mode():
    while True:
        method = input("입력 방법을 선택하세요 (1: 직접 입력, 2: 3x3 자동 생성 예시): ").strip()
        if method in ("1", "2"):
            break
        print("오류: 1 또는 2를 입력하세요.")

    if method == "1":
        filter_a = read_matrix("필터 A")
        filter_b = read_matrix("필터 B")
        pattern = read_matrix("패턴")
    else:
        print("짝수 N의 Cross는 가운데 두 행과 가운데 두 열을 사용합니다.")
        filter_a = generate_pattern(SIZE, "Cross")
        filter_b = generate_pattern(SIZE, "X")
        print("필터 A=Cross, 필터 B=X로 자동 생성했습니다.")
        while True:
            pattern_choice = input("입력 패턴을 선택하세요 (1: Cross, 2: X): ").strip()
            if pattern_choice in ("1", "2"):
                break
            print("오류: 1 또는 2를 입력하세요.")
        pattern_label = "Cross" if pattern_choice == "1" else "X"
        pattern = generate_pattern(SIZE, pattern_label)
        print("입력 패턴 {}를 자동 생성했습니다.".format(pattern_label))

    # Matrix checks and all console output stay outside the timed MAC calls.
    size = validate_square_matrix(filter_a, "필터 A")
    if validate_square_matrix(filter_b, "필터 B") != size:
        raise ValueError("모든 행렬의 크기가 같아야 합니다.")
    if validate_square_matrix(pattern, "패턴") != size:
        raise ValueError("모든 행렬의 크기가 같아야 합니다.")

    flat_pattern = flatten_matrix(pattern)
    score_a = mac(filter_a, pattern)
    score_b = mac(filter_b, pattern)
    if mac_1d(flatten_matrix(filter_a), flat_pattern) != score_a:
        raise ValueError("필터 A의 2D와 1D MAC 점수가 일치하지 않습니다.")
    if mac_1d(flatten_matrix(filter_b), flat_pattern) != score_b:
        raise ValueError("필터 B의 2D와 1D MAC 점수가 일치하지 않습니다.")
    print("\n분석 결과")
    print("A 점수: {:.12g}".format(score_a))
    print("B 점수: {:.12g}".format(score_b))
    result = decide(score_a, score_b)
    if result == "UNDECIDED":
        print("판정: 판정 불가 (UNDECIDED)")
    else:
        print("판정: {}".format("A" if result == "Cross" else "B"))

    average_2d, average_1d = _measure_mac_pair(filter_a, pattern)
    print("\nMAC 성능 비교 (필터 A 기준)")
    _print_mac_comparison_header()
    _print_mac_comparison_row(size, average_2d, average_1d)


def _json_number(value, location):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("{}: bool이 아닌 JSON 숫자가 필요합니다.".format(location))
    try:
        number = float(value)
    except (OverflowError, ValueError):
        raise ValueError("{}: 유한한 숫자가 필요합니다.".format(location))
    if not math.isfinite(number):
        raise ValueError("{}: NaN/Infinity는 허용되지 않습니다.".format(location))
    return number


def _json_matrix(raw, size, location):
    if not isinstance(raw, list) or len(raw) != size:
        raise ValueError("{}: {}x{} 행렬이어야 합니다.".format(location, size, size))
    matrix = []
    for row_index, row in enumerate(raw):
        if not isinstance(row, list) or len(row) != size:
            raise ValueError("{}: {}행은 숫자 {}개여야 합니다.".format(location, row_index + 1, size))
        matrix.append([
            _json_number(value, "{}[{}][{}]".format(location, row_index, column_index))
            for column_index, value in enumerate(row)
        ])
    return matrix


def _normalize_expected(raw):
    if not isinstance(raw, str):
        raise ValueError("expected는 '+', 'x', 'Cross', 'X' 중 하나여야 합니다.")
    normalized = {"+": "Cross", "cross": "Cross", "x": "X"}.get(raw.strip().lower())
    if normalized is None:
        raise ValueError("expected 라벨 오류: {!r}".format(raw))
    return normalized


def load_json_document(path):
    try:
        with open(path, "r", encoding="utf-8") as source:
            document = json.load(source, parse_constant=_reject_json_constant)
    except FileNotFoundError:
        print("JSON 분석을 종료합니다: data.json 파일이 없습니다.")
        return None
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
        print("JSON 분석을 종료합니다: JSON 파싱 실패 - {}".format(error))
        return None

    if not isinstance(document, dict):
        print("JSON 분석을 종료합니다: 최상위 구조는 객체여야 합니다.")
        return None
    if not isinstance(document.get("filters"), dict) or not isinstance(document.get("patterns"), dict):
        print("JSON 분석을 종료합니다: 최상위 filters와 patterns는 객체여야 합니다.")
        return None
    return document


def _reject_json_constant(constant):
    raise ValueError("JSON 표준에 없는 상수 {}가 포함되어 있습니다.".format(constant))


def _extract_pattern(raw_pattern, key):
    if not isinstance(raw_pattern, dict):
        raise ValueError("패턴 항목은 matrix와 expected를 가진 객체여야 합니다.")
    match = PATTERN_KEY.match(key)
    if not match:
        raise ValueError("키 형식 오류: size_{N}_{idx}가 필요합니다.")
    size = int(match.group(1))
    if size <= 0:
        raise ValueError("키의 N은 양의 정수여야 합니다.")
    input_field = None
    if "input" in raw_pattern:
        input_field = "input"
    else:
        # Keep earlier field names as fallbacks; the assignment schema is input.
        for alias in ("matrix", "pattern", "data", "values"):
            if alias in raw_pattern:
                input_field = alias
                break
    if input_field is None:
        raise ValueError("패턴 입력 필드가 없습니다 (input).")
    matrix = _json_matrix(raw_pattern[input_field], size, "patterns.{}.{}".format(key, input_field))
    expected = _normalize_expected(raw_pattern.get("expected"))
    return size, matrix, expected


def _load_filters(raw_filters):
    normalized = {}
    errors = {}
    for size_key, raw_group in raw_filters.items():
        match = re.match(r"^size_(\d+)$", size_key) if isinstance(size_key, str) else None
        if not match:
            errors[size_key] = "필터 크기 키 형식 오류: size_N이 필요합니다."
            continue
        size = int(match.group(1))
        if size <= 0:
            errors[size_key] = "필터 크기는 양의 정수여야 합니다."
            continue
        if not isinstance(raw_group, dict):
            errors[size_key] = "필터 그룹은 cross와 x를 가진 객체여야 합니다."
            continue
        group = {}
        group_errors = []
        for label, aliases in (("Cross", ("cross",)), ("X", ("x",))):
            raw_matrix = None
            for alias in aliases:
                if alias in raw_group:
                    raw_matrix = raw_group[alias]
                    break
            if raw_matrix is None:
                group_errors.append("{} 필터가 없습니다.".format(label))
                continue
            try:
                group[label] = _json_matrix(raw_matrix, size, "filters.{}.{}".format(size_key, label.lower()))
            except ValueError as error:
                group_errors.append(str(error))
        normalized[size] = group
        if group_errors:
            errors[size_key] = "; ".join(group_errors)
    for required_size in (5, 13, 25):
        required_key = "size_{}".format(required_size)
        if required_key not in raw_filters:
            errors.setdefault(required_key, "필수 필터 {}가 없습니다.".format(required_key))
    return normalized, errors


def _case_entries(patterns):
    entries = []
    for key, raw_pattern in patterns.items():
        case_id = str(key)
        try:
            size, matrix, expected = _extract_pattern(raw_pattern, key)
            entries.append({"id": case_id, "size": size, "matrix": matrix, "expected": expected})
        except (ValueError, TypeError) as error:
            # Try to retain a size for linking a malformed entry to its filter.
            match = PATTERN_KEY.match(key) if isinstance(key, str) else None
            size = int(match.group(1)) if match else None
            entries.append({"id": case_id, "size": size, "error": str(error)})
    return entries


def _benchmark_sizes():
    rows = []
    for size in JSON_SIZES:
        # Generate representative operands and flatten them before measurement.
        filter_matrix = generate_pattern(size, "Cross")
        pattern = generate_pattern(size, "X")
        average_2d, average_1d = _measure_mac_pair(filter_matrix, pattern)
        rows.append((size, average_2d, average_1d))
    return rows


def run_json_analysis(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
    document = load_json_document(path)
    if document is None:
        return

    filters, filter_errors = _load_filters(document["filters"])
    entries = _case_entries(document["patterns"])
    failures = []
    total = passed = 0

    print("\nJSON 분석 결과")
    for entry in entries:
        total += 1
        case_id = entry["id"]
        reasons = []
        size = entry.get("size")
        if entry.get("error"):
            reasons.append(entry["error"])
        if size is not None:
            size_key = "size_{}".format(size)
            if size_key in filter_errors:
                reasons.append(filter_errors[size_key])
            group = filters.get(size, {})
            if "Cross" not in group:
                reasons.append("{} Cross 필터를 사용할 수 없습니다.".format(size_key))
            if "X" not in group:
                reasons.append("{} X 필터를 사용할 수 없습니다.".format(size_key))
        else:
            group = {}
            reasons.append("필터 크기에 연결할 수 없습니다.")

        if reasons:
            reason = "; ".join(dict.fromkeys(reasons))
            failures.append((case_id, reason))
            print("{}: FAIL - {}".format(case_id, reason))
            continue

        flat_pattern = flatten_matrix(entry["matrix"])
        cross_score = mac(group["Cross"], entry["matrix"])
        x_score = mac(group["X"], entry["matrix"])
        cross_score_1d = mac_1d(flatten_matrix(group["Cross"]), flat_pattern)
        x_score_1d = mac_1d(flatten_matrix(group["X"]), flat_pattern)
        if cross_score_1d != cross_score or x_score_1d != x_score:
            reason = "2D와 1D MAC 점수가 일치하지 않습니다."
            failures.append((case_id, reason))
            print("{}: FAIL - {}".format(case_id, reason))
            continue
        result = decide(cross_score, x_score)
        passed_case = result != "UNDECIDED" and result == entry["expected"]
        status = "PASS" if passed_case else "FAIL"
        print("{}: Cross={:.12g}, X={:.12g}, 판정={}, expected={}, {}".format(
            case_id, cross_score, x_score,
            "판정 불가 (UNDECIDED)" if result == "UNDECIDED" else result,
            entry["expected"], status,
        ))
        if passed_case:
            passed += 1
        else:
            reason = "동점(UNDECIDED)" if result == "UNDECIDED" else "판정 {} != expected {}".format(result, entry["expected"])
            failures.append((case_id, reason))

    print("\n성능 표")
    _print_mac_comparison_header()
    for size, average_2d, average_1d in _benchmark_sizes():
        _print_mac_comparison_row(size, average_2d, average_1d)

    failed = total - passed
    print("\n최종 총계: 테스트 {}건, 통과 {}건, 실패 {}건".format(total, passed, failed))
    if failures:
        print("실패 ID 및 사유:")
        for case_id, reason in failures:
            print("- {}: {}".format(case_id, reason))
    else:
        print("실패 ID 및 사유: 없음")
    if total != passed + failed or failed != len(failures):
        print("총계 확인: 불일치")
    else:
        print("총계 확인: 일치")


def main():
    print("Mini NPU Simulator")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    while True:
        choice = input("모드를 선택하세요 (1/2): ").strip()
        if choice == "1":
            run_user_input_mode()
            return
        if choice == "2":
            run_json_analysis()
            return
        print("오류: 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
