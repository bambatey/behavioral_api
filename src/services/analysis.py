from collections import defaultdict
from io import BytesIO
from typing import TYPE_CHECKING

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from src.datalayer.repository import ParticipantRepository, TrialResultRepository

if TYPE_CHECKING:
    from firebase_admin.firestore_async import AsyncClient


HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF")


class AnalysisService:
    """Per-participant × per-condition mean Likert export."""

    def __init__(self, db: "AsyncClient"):
        self.db = db
        self.participant_repo = ParticipantRepository(db)
        self.trial_repo = TrialResultRepository(db)

    async def export(self) -> bytes:
        participants = {p.id: p for p in await self.participant_repo.get_all()}
        trials = await self.trial_repo.get_all()

        # Critical (non-filler) trials with a usable Likert response
        critical = [
            t for t in trials
            if not t.is_filler
            and t.position is not None
            and t.bias is not None
            and isinstance(t.response, int)
        ]

        # Aggregate: per (participant, position, bias)
        per_pos_bias: dict = defaultdict(list)
        # Aggregate: per (participant, position) — bias collapsed
        per_pos: dict = defaultdict(list)
        for t in critical:
            per_pos_bias[(t.participant_id, t.position, t.bias)].append(t.response)
            per_pos[(t.participant_id, t.position)].append(t.response)

        wb = Workbook()

        # ----- Sheet 1: Per (Participant × Position × Bias) — 12 rows / participant -----
        ws1 = wb.active
        ws1.title = "Position x Bias"
        self._header(ws1, [
            "Participant ID", "Name", "Assignment Index",
            "Position", "Bias", "N trials", "Mean Likert",
        ])
        rows1 = []
        for (pid, pos, bias), vals in per_pos_bias.items():
            p = participants.get(pid)
            rows1.append((
                pid,
                p.name if p else None,
                p.assignment_index if p else None,
                pos,
                bias,
                len(vals),
                round(sum(vals) / len(vals), 2),
            ))
        rows1.sort(key=lambda r: ((r[1] or "").lower(), r[3], r[4] or ""))
        self._write_rows(ws1, rows1, start_row=2)

        # ----- Sheet 2: Per (Participant × Position) — 6 rows / participant -----
        ws2 = wb.create_sheet("Position")
        self._header(ws2, [
            "Participant ID", "Name", "Assignment Index",
            "Position", "N trials", "Mean Likert",
        ])
        rows2 = []
        for (pid, pos), vals in per_pos.items():
            p = participants.get(pid)
            rows2.append((
                pid,
                p.name if p else None,
                p.assignment_index if p else None,
                pos,
                len(vals),
                round(sum(vals) / len(vals), 2),
            ))
        rows2.sort(key=lambda r: ((r[1] or "").lower(), r[3]))
        self._write_rows(ws2, rows2, start_row=2)

        # ----- Sheet 3: Wide format (participant per row, 12 columns of conditions) -----
        ws3 = wb.create_sheet("Wide Format")
        bias_list = ["subject", "object"]
        condition_cols = [f"pos{p}_{b}" for p in range(1, 7) for b in bias_list]
        self._header(
            ws3,
            ["Participant ID", "Name", "Assignment Index"] + condition_cols,
        )
        # one row per participant
        wide_rows = []
        for pid, p in participants.items():
            row = [pid, p.name, p.assignment_index]
            for pos in range(1, 7):
                for bias in bias_list:
                    vals = per_pos_bias.get((pid, pos, bias))
                    row.append(round(sum(vals) / len(vals), 2) if vals else None)
            wide_rows.append(row)
        wide_rows.sort(key=lambda r: (r[1] or "").lower())
        self._write_rows(ws3, wide_rows, start_row=2)

        # ----- Sheet 4: Group-level means (across participants) -----
        ws4 = wb.create_sheet("Group Means")
        self._header(ws4, ["Position", "Bias", "N participants", "N trials", "Mean Likert", "SD"])
        # gather across participants
        group: dict = defaultdict(list)  # (pos, bias) -> [all_likerts]
        for (_, pos, bias), vals in per_pos_bias.items():
            group[(pos, bias)].extend(vals)
        group_rows = []
        for (pos, bias), vals in group.items():
            # count distinct participants who contributed
            participant_ids = {pid for (pid, p2, b2) in per_pos_bias if p2 == pos and b2 == bias}
            mean = sum(vals) / len(vals) if vals else None
            sd = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5 if mean is not None and len(vals) > 1 else None
            group_rows.append((
                pos,
                bias,
                len(participant_ids),
                len(vals),
                round(mean, 2) if mean is not None else None,
                round(sd, 2) if sd is not None else None,
            ))
        group_rows.sort(key=lambda r: (r[0], r[1] or ""))
        self._write_rows(ws4, group_rows, start_row=2)

        # Auto-width all sheets
        for ws in [ws1, ws2, ws3, ws4]:
            for col in ws.columns:
                max_len = max((len(str(c.value)) for c in col if c.value is not None), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)
            ws.freeze_panes = "A2"

        out = BytesIO()
        wb.save(out)
        out.seek(0)
        return out.getvalue()

    @staticmethod
    def _header(ws, titles):
        for col_num, title in enumerate(titles, start=1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = title
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")

    @staticmethod
    def _write_rows(ws, rows, start_row: int = 2):
        for r_idx, row in enumerate(rows, start=start_row):
            for c_idx, val in enumerate(row, start=1):
                ws.cell(row=r_idx, column=c_idx).value = val
