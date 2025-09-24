import re
import unicodedata
import camelot
import fitz
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



PAGE_SPLIT_RE = re.compile(r"\n{0,2}=== 페이지\s*(\d+)\s*===\n{0,2}")


def rect_iou(a, b):
    """
    a, b: (x0, y0, x1, y1)  # 모두 상단-좌측(0,0) 기준의 PDF 좌표(페이지 top-left origin)

    Args:
        a (tuple): 첫 번째 사각형의 좌표 (x0, y0, x1, y1)
        b (tuple): 두 번째 사각형의 좌표 (x0, y0, x1, y1)
    Returns:
        float: 두 사각형의 IoU (Intersection over Union) 값
    """
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    inter_x0, inter_y0 = max(ax0, bx0), max(ay0, by0)
    inter_x1, inter_y1 = min(ax1, bx1), min(ay1, by1)
    iw = max(0, inter_x1 - inter_x0)
    ih = max(0, inter_y1 - inter_y0)
    inter = iw * ih
    if inter == 0:
        return 0.0
    a_area = max(0, (ax1 - ax0)) * max(0, (ay1 - ay0))
    b_area = max(0, (bx1 - bx0)) * max(0, (by1 - by0))
    union = a_area + b_area - inter
    if union <= 0:
        return 0.0
    return inter / union


def overlaps_any(bbox, regions, iou_thresh=0.05):
    """
    bbox: (x0, y0, x1, y1)
    regions: [(x0, y0, x1, y1), ...]
    iou_thresh: float
    Args:
        bbox (tuple): 비교할 사각형의 좌표 (x0, y0, x1, y1)
        regions (list): 비교 대상 사각형들의 좌표 리스트 [(x0, y0, x1, y1), ...]
        iou_thresh (float): IoU 임계값
    Returns:
        bool: bbox가 regions 내의 어떤 사각형과라도 iou_thresh 이상 겹치는지 여부
    """
    return any(rect_iou(bbox, r) >= iou_thresh for r in regions)


def extract_tables_with_fitz_and_camelot(pdf_stream: bytes, page_index: int):
    """
    page_index: 0-based
    반환:
      table_items: [
        {
          "bbox": (x0,y0,x1,y1),
          "raw_data": 2D list,
          "html": "<table>...</table>",
          "source": "fitz" | "camelot-lattice" | "camelot-stream"
        }, ...
      ]
    """
    table_items = []
    bboxes = []
    # 1) fitz 우선
    pdf_stream.seek(0)
    doc = fitz.open("pdf", pdf_stream)
    page = doc[page_index]
    try:
        finder = page.find_tables()
        if finder and getattr(finder, "tables", None):
            for t in finder.tables:
                # t.bbox: (x0, y0, x1, y1)
                tb = getattr(t, "bbox", None)
                data = None
                try:
                    data = t.extract()
                except Exception:
                    data = None

                if tb and data and len(data) > 0:
                    # html_table = convert_table_to_html(data)
                    markeddown_table = convert_table_to_markdown(data, header_rows=1)
                    table_items.append({"bbox": tb, "raw_data": data, "markdown": markeddown_table, "source": "fitz"})
                    bboxes.append(tb)
    except Exception as e:
        logger.error(f"  - fitz 테이블 탐지 오류: {e}")
    finally:
        doc.close()

    # fitz에서 아무 것도 못 찾았거나, 너무 빈약하면 Camelot 백업
    need_backup = len(table_items) == 0

    if need_backup:
        # 2) Camelot lattice → stream 순서로 시도
        page_onebased = page_index + 1

        for flavor in ("lattice", "stream"):
            try:
                pdf_stream.seek(0)
                tables = camelot.read_pdf(pdf_stream, pages=str(page_onebased), flavor=flavor)
                if tables and len(tables) > 0:
                    for t in tables:
                        data = t.df.values.tolist()
                        if not data or all(
                            (row is None or all((c is None or str(c).strip() == "" for c in row))) for row in data
                        ):
                            continue
                        tb = None
                        for attr in ("_bbox", "bbox"):
                            if hasattr(t, attr):
                                tb = getattr(t, attr)
                                if tb and len(tb) == 4:
                                    # Camelot bbox는 (x1,y1,x2,y2) with bottom-left origin일 수 있음 → 상단원점계로 변환 필요
                                    pass
                        # html_table = convert_table_to_html(data)
                        markeddown_table = convert_table_to_markdown(data, header_rows=1)
                        table_items.append(
                            {
                                "bbox": tb,  # None일 수도 있음
                                "raw_data": data,
                                # "html": html_table,
                                "markdown": markeddown_table,
                                "source": f"camelot-{flavor}",
                            }
                        )
                if len(table_items) > 0:
                    break  # lattice에서 성공하면 stream은 생략
            except Exception as e:
                logger.error(f"  - Camelot({flavor}) 오류: {e}")

    return table_items


def extract_text_without_tables(plumber_page, table_bboxes, iou_thresh=0.05, x_tol=2, y_tol=3):
    """
    - pdfplumber.Page.extract_words()로 단어 bbox 얻기
    - 표 bbox와 IoU 겹치는 단어 drop
    - y(위치) 기준으로 라인 재구성
    """
    words = plumber_page.extract_words(use_text_flow=True, extra_attrs=["size"])
    # words 예: [{'text': 'Hello', 'x0': 72.0, 'x1': 90.3, 'top': 100.1, 'bottom': 112.4, ...}, ...]

    ##################filtered 수정################################
    def inside_any(bbox, table_bboxes, margin=0.5):
        """
        처음에는 overlap(겹치는 것)을 잡으려 시도했지만 실패 -> 포함 여부로 변경
        IoU -> 포함 여부 검사로 변경
        """
        x0, top, x1, bottom = bbox
        for tx0, ttop, tx1, tbottom in table_bboxes:
            if x0 >= tx0 - margin and x1 <= tx1 + margin and top >= ttop - margin and bottom <= tbottom + margin:
                return True
        return False

    filtered = [w for w in words if not inside_any((w["x0"], w["top"], w["x1"], w["bottom"]), table_bboxes)]
    ##################filtered 수정################################

    # 라인 재구성: y 중심값으로 그룹핑 후 x 정렬
    # (간단 휴리스틱. 필요시 더 정교한 단락 재조립 로직 추가)
    lines = []
    filtered.sort(key=lambda w: (w["top"], w["x0"]))
    current_line = []
    last_top = None

    for w in filtered:
        if last_top is None:
            current_line = [w]
            last_top = w["top"]
            continue
        if abs(w["top"] - last_top) <= y_tol:
            current_line.append(w)
            last_top = (last_top + w["top"]) / 2
        else:
            current_line.sort(key=lambda x: x["x0"])
            lines.append(" ".join([x["text"] for x in current_line]))
            current_line = [w]
            last_top = w["top"]

    if current_line:
        current_line.sort(key=lambda x: x["x0"])
        lines.append(" ".join([x["text"] for x in current_line]))

    # 하이픈 연결, 중복 공백 정리 등 간단 정제
    text = "\n".join(lines)
    text = fix_hyphenation(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def fix_hyphenation(text):
    # "examp-\nle" → "example" 같은 단순 하이픈 연결
    text = re.sub(r"-\s*\n\s*", "", text)
    return text


def convert_table_to_html(table_data):
    """
    테이블 데이터에 html 태그 붙이기
    """
    if not table_data:
        return ""

    html = "<table>"
    for row in table_data:
        if row and any((cell is not None and str(cell).strip() != "") for cell in row):
            html += "<tr>"
            for cell in row:
                cell_value = "" if cell is None else str(cell)
                html += f"<td>{cell_value}</td>"
            html += "</tr>"
    html += "</table>"
    return html


def convert_table_to_markdown(table_data, header_rows=1, max_cols=None):
    if not table_data:
        return ""
    rows = [["" if c is None else str(c).strip() for c in row] for row in table_data]
    # 공백 행 제거
    rows = [r for r in rows if any(cell != "" for cell in r)]
    if not rows:
        return ""

    # 열 수 정규화 (rag에서 열 개수 일관이 중요)
    width = max(len(r) for r in rows)
    if max_cols is not None:
        width = min(width, max_cols)
    rows = [(r + [""] * (width - len(r)))[:width] for r in rows]

    def esc(cell):
        # 파이프·개행 이스케이프
        return cell.replace("|", "\\|").replace("\n", " ").strip()

    header = rows[0] if header_rows >= 1 else [f"col{i+1}" for i in range(width)]
    body = rows[header_rows:] if header_rows >= 1 and len(rows) > 1 else rows

    lines = []
    lines.append("| " + " | ".join(esc(c) for c in header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for r in body:
        lines.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(lines)


def normalize_for_compare(s: str) -> str:
    """비교용 정규화: 유니코드 정규화, 공백 축약, 숫자 천단위 구분자 제거."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    # 1) 공백 축약
    s = re.sub(r"\s+", " ", s).strip()
    # 2) 1,234 같은 숫자 천단위 콤마 제거 (숫자 사이의 콤마만)
    s = re.sub(r"(?<=\d),(?=\d)", "", s)
    return s


def build_table_line_set(table_data, min_nonempty=2):
    """
    표의 각 행을 '셀들을 공백으로 이어붙인 한 줄'로 만들어 정규화하고 집합으로 수집.
    min_nonempty: 비어있지 않은 셀이 최소 몇 개 이상인 행만 후보로 볼지.
    """
    line_set = set()
    for row in table_data or []:
        # 비어있지 않은 셀들만 추림
        cells = [str(c).strip() for c in row if c is not None and str(c).strip() != ""]
        if len(cells) >= min_nonempty:
            joined = " ".join(cells)
            norm = normalize_for_compare(joined)
            if norm:
                line_set.add(norm)
    return line_set


def remove_table_line_duplicates(text: str, table_items: list) -> str:
    """
    본문 텍스트에서 표 행(한 줄)과 '정확히 동일한 라인'만 삭제.
    - 안전: 문장 중 일부 단어가 겹친다고 해서 지우지 않음(라인 완전 일치만 제거)
    """
    if not text:
        return text

    # 테이블들의 라인 집합 모으기
    line_set = set()
    for t in table_items or []:
        raw = t.get("raw_data")
        if raw:
            line_set |= build_table_line_set(raw, min_nonempty=2)

    if not line_set:
        return text

    out_lines = []
    for line in text.splitlines():
        norm = normalize_for_compare(line)
        if norm and norm in line_set:
            # 이 라인은 표 행과 동일 → 제거
            continue
        out_lines.append(line)

    # 연속 빈 줄 정리
    out = "\n".join([ln for ln in out_lines if ln.strip() != ""])
    return out


def get_text_and_tables(pdf_stream: bytes, file_name: str):
    """
    TEXT는 pdfplumber를 사용(표 bbox 마스킹),
    Table은 fitz(+Camelot 백업)를 사용하여 추출
    """
    pdf_stream.seek(0)
    with pdfplumber.open(pdf_stream) as pdf:
        pages = pdf.pages
        logger.info(f"[{file_name}] 총 페이지 수: {len(pages)}")
    all_page_data = []

    # 2) 페이지별 처리
    for page_index in range(len(pages)):
        logger.info(f"[{file_name}] - {page_index + 1} 페이지 처리 시작")

        page_data = {"page": page_index + 1, "text": "", "tables": []}

        table_items = extract_tables_with_fitz_and_camelot(pdf_stream, page_index)

        table_bboxes = [t["bbox"] for t in table_items if t.get("bbox") is not None]
        pdf_stream.seek(0)
        with pdfplumber.open(pdf_stream) as pdf2:
            plumber_page = pdf2.pages[page_index]
            plumber_page = plumber_page.dedupe_chars(tolerance=1)
            text = extract_text_without_tables(plumber_page, table_bboxes, iou_thresh=0.05)
            text = remove_table_line_duplicates(text, table_items)

            if text:
                page_data["text"] = text
                logger.info(f" - 텍스트 추출(마스킹) 완료: {len(text)} chars")

        if len(table_items) > 0:
            logger.info(f" - {len(table_items)} 개의 테이블 있음")
            for i, t in enumerate(table_items):
                page_data["tables"].append(
                    {
                        "table_index": i + 1,
                        # "html": t["html"],
                        "markdown": t["markdown"],
                        "raw_data": t["raw_data"],
                        "source": t["source"],
                        "bbox": t.get("bbox"),
                    }
                )
        else:
            logger.info("  - 테이블 없음")

        all_page_data.append(page_data)

    return all_page_data


def text_to_documents(
    text_content: str, file_name: str, chunk_size: int = 500, chunk_overlap: int = 100
) -> list[Document]:
    # 페이지 단위 분리
    parts = PAGE_SPLIT_RE.split(text_content)
    docs = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],  # 페이지 내부 세분화 규칙
    )

    for i in range(1, len(parts), 2):
        page_header = parts[i]
        page_content = parts[i + 1] if i + 1 < len(parts) else ""
        if not page_content.strip():
            continue

        # 페이지 번호 추출
        match = re.search(r"페이지\s*(\d+)", page_header)
        page_num = int(match.group(1)) if match else None

        # 페이지 텍스트를 chunk_size 단위로 쪼갬
        chunks = splitter.split_text(page_content)
        logger.debug(f"  - {file_name} 페이지 {page_num}: {len(chunks)} chunks")
        for idx, chunk in enumerate(chunks):
            docs.append(
                Document(
                    page_content=chunk.strip(),
                    metadata={
                        "source": file_name,
                        "page": page_num,
                        "chunk_index": idx,
                        "is_page_split": len(chunks) > 1,  # 페이지가 쪼개졌는지 여부
                    },
                )
            )
    return docs


def convert_pdf_to_text(pdf_stream: bytes, file_name: str) -> list[Document]:
    """
    pdf -> txt
    """
    page_data = get_text_and_tables(pdf_stream, file_name)
    txt_content = ""
    for page_info in page_data:
        txt_content += f"=== 페이지 {page_info['page']} ===\n\n"
        if page_info["text"]:
            txt_content += f"[텍스트]\n{page_info['text']}\n\n"
        # if page_info["tables"]:
        #     txt_content += f"[테이블 {len(page_info['tables'])}개]\n"
        #     for table_info in page_info["tables"]:
        #         txt_content += f"\n--- 테이블 {table_info['table_index']} ({table_info.get('source')}) ---\n"
        #         txt_content += table_info["html"] + "\n\n"
        if page_info["tables"]:
            txt_content += f"[테이블 {len(page_info['tables'])}개]\n"
            for table_info in page_info["tables"]:
                txt_content += f"\n--- 테이블 {table_info['table_index']} ({table_info.get('source')}) ---\n"
                txt_content += table_info["markdown"] + "\n\n"
        txt_content += "=" * 20 + "\n\n"
    logger.info(f"[{file_name}] PDF to TEXT 변환 완료, 총 {len(page_data)} 페이지")
    documents = text_to_documents(txt_content, file_name, chunk_size=800, chunk_overlap=100)
    logger.info(f"[{file_name}] TEXT to {len(documents)} Documents 변환 완료")
    return documents
