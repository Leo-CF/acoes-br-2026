import tkinter as tk
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

SQ = 64
ML, MT, MB = 20, 8, 20
CW = ML + SQ * 8 + 8    # 540
CH = MT + SQ * 8 + MB   # 540

C = {
    "bg":       "#0e1117",
    "sidebar":  "#161b22",
    "light":    "#f0d9b5",
    "dark":     "#b58863",
    "sel":      "#7bc97e",
    "check_sq": "#e63946",
    "last":     "#cdd16e",
    "fg":       "#ffffff",
    "hint":     "#888888",
    "red":      "#e63946",
    "red_hov":  "#c0392b",
    "neu":      "#1e222a",
    "neu_hov":  "#2e3340",
}

SYMS = {
    ('w', 'K'): '♔', ('w', 'Q'): '♕', ('w', 'R'): '♖',
    ('w', 'B'): '♗', ('w', 'N'): '♘', ('w', 'P'): '♙',
    ('b', 'K'): '♚', ('b', 'Q'): '♛', ('b', 'R'): '♜',
    ('b', 'B'): '♝', ('b', 'N'): '♞', ('b', 'P'): '♟',
}
PFONT = ("Segoe UI Symbol", 38)
LFONT = ("Segoe UI", 9)


# ── chess logic ────────────────────────────────────────────────────────────

class ChessGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = self._init_board()
        self.turn = 'w'
        self.en_passant = None
        self.castling = {'w': {'K': True, 'Q': True}, 'b': {'K': True, 'Q': True}}
        self.last_move = None

    def _init_board(self):
        b = [[None] * 8 for _ in range(8)]
        for c, t in enumerate('RNBQKBNR'):
            b[0][c] = ('b', t)
            b[7][c] = ('w', t)
        for c in range(8):
            b[1][c] = ('b', 'P')
            b[6][c] = ('w', 'P')
        return b

    def _opp(self, color):
        return 'b' if color == 'w' else 'w'

    def _king_pos(self, color, board=None):
        if board is None:
            board = self.board
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p and p[0] == color and p[1] == 'K':
                    return (r, c)
        return None

    def _pawn_attacks(self, row, col, color):
        d = -1 if color == 'w' else 1
        nr = row + d
        if not (0 <= nr < 8):
            return []
        return [(nr, col + dc) for dc in (-1, 1) if 0 <= col + dc < 8]

    def _pseudo_moves(self, row, col, board=None):
        if board is None:
            board = self.board
        p = board[row][col]
        if p is None:
            return []
        color, pt = p
        moves = []

        if pt == 'P':
            d = -1 if color == 'w' else 1
            nr = row + d
            if 0 <= nr < 8 and board[nr][col] is None:
                moves.append((nr, col))
                start = 6 if color == 'w' else 1
                if row == start and board[row + 2 * d][col] is None:
                    moves.append((row + 2 * d, col))
            for dc in (-1, 1):
                nc = col + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    tgt = board[nr][nc]
                    if (tgt and tgt[0] != color) or (nr, nc) == self.en_passant:
                        moves.append((nr, nc))

        elif pt == 'N':
            for dr, dc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    tgt = board[nr][nc]
                    if tgt is None or tgt[0] != color:
                        moves.append((nr, nc))

        elif pt in ('B', 'R', 'Q'):
            dirs = []
            if pt in ('B', 'Q'): dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
            if pt in ('R', 'Q'): dirs += [(-1,0),(1,0),(0,-1),(0,1)]
            for dr, dc in dirs:
                nr, nc = row + dr, col + dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    tgt = board[nr][nc]
                    if tgt is None:
                        moves.append((nr, nc))
                    elif tgt[0] != color:
                        moves.append((nr, nc))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif pt == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        tgt = board[nr][nc]
                        if tgt is None or tgt[0] != color:
                            moves.append((nr, nc))

        return moves

    def _attacked(self, row, col, by, board=None):
        if board is None:
            board = self.board
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p is None or p[0] != by:
                    continue
                color, pt = p
                if pt == 'P':
                    if (row, col) in self._pawn_attacks(r, c, color):
                        return True
                elif (row, col) in self._pseudo_moves(r, c, board):
                    return True
        return False

    def in_check(self, color, board=None):
        kp = self._king_pos(color, board)
        return kp is not None and self._attacked(kp[0], kp[1], self._opp(color), board)

    def legal_moves(self, row, col):
        p = self.board[row][col]
        if p is None or p[0] != self.turn:
            return []
        color, pt = p
        result = []
        for nr, nc in self._pseudo_moves(row, col):
            tmp = [r[:] for r in self.board]
            if pt == 'P' and (nr, nc) == self.en_passant:
                tmp[row][nc] = None
            tmp[nr][nc] = tmp[row][col]
            tmp[row][col] = None
            if not self.in_check(color, tmp):
                result.append((nr, nc))
        if pt == 'K':
            result += self._castling_moves(color)
        return result

    def _castling_moves(self, color):
        moves = []
        rank = 7 if color == 'w' else 0
        opp = self._opp(color)
        if self.castling[color]['K']:
            if (self.board[rank][5] is None and self.board[rank][6] is None
                    and self.board[rank][7] == (color, 'R')
                    and not self._attacked(rank, 4, opp)
                    and not self._attacked(rank, 5, opp)
                    and not self._attacked(rank, 6, opp)):
                moves.append((rank, 6))
        if self.castling[color]['Q']:
            if (self.board[rank][3] is None and self.board[rank][2] is None
                    and self.board[rank][1] is None
                    and self.board[rank][0] == (color, 'R')
                    and not self._attacked(rank, 4, opp)
                    and not self._attacked(rank, 3, opp)
                    and not self._attacked(rank, 2, opp)):
                moves.append((rank, 2))
        return moves

    def make_move(self, fr, fc, tr, tc):
        """Execute move. Returns ('promo', (r, c)) or ('ok', None)."""
        p = self.board[fr][fc]
        color, pt = p

        if pt == 'K':
            self.castling[color] = {'K': False, 'Q': False}
        if pt == 'R':
            rank = 7 if color == 'w' else 0
            if fr == rank and fc == 0: self.castling[color]['Q'] = False
            if fr == rank and fc == 7: self.castling[color]['K'] = False
        opp_rank = 0 if color == 'w' else 7
        if (tr, tc) == (opp_rank, 0): self.castling[self._opp(color)]['Q'] = False
        if (tr, tc) == (opp_rank, 7): self.castling[self._opp(color)]['K'] = False

        if pt == 'P' and (tr, tc) == self.en_passant:
            self.board[fr][tc] = None

        if pt == 'K' and fc == 4:
            rank = 7 if color == 'w' else 0
            if tc == 6:
                self.board[rank][5] = self.board[rank][7]
                self.board[rank][7] = None
            elif tc == 2:
                self.board[rank][3] = self.board[rank][0]
                self.board[rank][0] = None

        self.en_passant = None
        if pt == 'P' and abs(tr - fr) == 2:
            self.en_passant = ((fr + tr) // 2, fc)

        self.board[tr][tc] = p
        self.board[fr][fc] = None
        self.last_move = ((fr, fc), (tr, tc))

        if pt == 'P' and (tr == 0 or tr == 7):
            return 'promo', (tr, tc)

        self.turn = self._opp(color)
        return 'ok', None

    def finish_promotion(self, row, col, piece_type):
        color = self.board[row][col][0]
        self.board[row][col] = (color, piece_type)
        self.turn = self._opp(color)

    def status(self):
        color = self.turn
        chk = self.in_check(color)
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p[0] == color and self.legal_moves(r, c):
                    return 'check' if chk else 'playing'
        return 'checkmate' if chk else 'stalemate'


# ── promotion dialog ────────────────────────────────────────────────────────

class PromotionDialog(ctk.CTkToplevel):
    def __init__(self, parent, color):
        super().__init__(parent)
        self.title("Promoção de Peão")
        self.resizable(False, False)
        self.grab_set()
        self.choice = 'Q'

        ctk.CTkLabel(
            self, text="Escolha a peça:",
            font=ctk.CTkFont("Segoe UI", 14),
        ).pack(pady=(16, 8), padx=16)

        row_frame = ctk.CTkFrame(self, fg_color="transparent")
        row_frame.pack(padx=16, pady=(0, 16))

        for pt, name in [('Q', 'Dama'), ('R', 'Torre'), ('B', 'Bispo'), ('N', 'Cavalo')]:
            sym = SYMS[(color, pt)]
            ctk.CTkButton(
                row_frame, text=f"{sym}\n{name}",
                font=ctk.CTkFont("Segoe UI Symbol", 20),
                width=80, height=80, corner_radius=8,
                fg_color=C["neu"], hover_color=C["neu_hov"],
                command=lambda t=pt: self._pick(t),
            ).pack(side="left", padx=4)

    def _pick(self, t):
        self.choice = t
        self.destroy()


# ── menu frame ──────────────────────────────────────────────────────────────

class MenuFrame(ctk.CTkFrame):
    def __init__(self, parent, on_start):
        super().__init__(parent, fg_color=C["bg"])
        self._on_start = on_start

        ctk.CTkLabel(
            self, text="♟  Xadrez",
            font=ctk.CTkFont("Segoe UI Symbol", 52, weight="bold"),
            text_color=C["fg"],
        ).place(relx=0.5, rely=0.32, anchor="center")

        ctk.CTkLabel(
            self, text="dois jogadores  •  local",
            font=ctk.CTkFont("Segoe UI", 15),
            text_color=C["hint"],
        ).place(relx=0.5, rely=0.44, anchor="center")

        ctk.CTkButton(
            self,
            text="▶  Iniciar Partida",
            font=ctk.CTkFont("Segoe UI", 15, weight="bold"),
            width=200, height=52, corner_radius=26,
            fg_color=C["red"], hover_color=C["red_hov"],
            command=self._on_start,
        ).place(relx=0.5, rely=0.58, anchor="center")


# ── game frame ──────────────────────────────────────────────────────────────

class GameFrame(ctk.CTkFrame):
    def __init__(self, parent, on_menu):
        super().__init__(parent, fg_color=C["bg"])
        self._on_menu = on_menu
        self.game = ChessGame()
        self._selected = None
        self._valid = []
        self._build()

    def start_new(self):
        self.game.reset()
        self._selected = None
        self._valid = []
        self._refresh()

    def _build(self):
        self._cv = tk.Canvas(
            self, width=CW, height=CH,
            bg=C["bg"], highlightthickness=0,
        )
        self._cv.pack(side="left", padx=(12, 0), pady=12)
        self._cv.bind("<Button-1>", self._click)

        sb = ctk.CTkFrame(self, fg_color=C["sidebar"], corner_radius=12, width=170)
        sb.pack(side="left", fill="y", padx=12, pady=12)
        sb.pack_propagate(False)

        ctk.CTkLabel(
            sb, text="Xadrez",
            font=ctk.CTkFont("Segoe UI", 22, weight="bold"),
        ).pack(pady=(24, 4))

        self._lbl_turn = ctk.CTkLabel(
            sb, text="",
            font=ctk.CTkFont("Segoe UI Symbol", 14),
        )
        self._lbl_turn.pack(pady=4)

        self._lbl_status = ctk.CTkLabel(
            sb, text="",
            font=ctk.CTkFont("Segoe UI", 13, weight="bold"),
        )
        self._lbl_status.pack(pady=2)

        ctk.CTkButton(
            sb, text="⟳  Nova Partida",
            font=ctk.CTkFont("Segoe UI", 12),
            width=140, height=36, corner_radius=8,
            fg_color=C["neu"], hover_color=C["neu_hov"],
            command=self.start_new,
        ).pack(pady=(50, 8))

        ctk.CTkButton(
            sb, text="← Menu",
            font=ctk.CTkFont("Segoe UI", 12),
            width=140, height=36, corner_radius=8,
            fg_color=C["neu"], hover_color=C["neu_hov"],
            command=self._on_menu,
        ).pack(pady=8)

    def _sq_rect(self, r, c):
        x0 = ML + c * SQ
        y0 = MT + r * SQ
        return x0, y0, x0 + SQ, y0 + SQ

    def _sq_center(self, r, c):
        x0, y0, x1, y1 = self._sq_rect(r, c)
        return (x0 + x1) // 2, (y0 + y1) // 2

    def _refresh(self):
        cv = self._cv
        cv.delete("all")
        g = self.game
        st = g.status()
        last_sqs = set(g.last_move) if g.last_move else set()

        for r in range(8):
            for c in range(8):
                x0, y0, x1, y1 = self._sq_rect(r, c)
                color = C["light"] if (r + c) % 2 == 0 else C["dark"]
                if (r, c) in last_sqs:
                    color = C["last"]
                cv.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

        if self._selected:
            x0, y0, x1, y1 = self._sq_rect(*self._selected)
            cv.create_rectangle(x0, y0, x1, y1, fill=C["sel"], outline="")

        if st in ('check', 'checkmate'):
            kp = g._king_pos(g.turn)
            if kp:
                x0, y0, x1, y1 = self._sq_rect(*kp)
                cv.create_rectangle(x0, y0, x1, y1, fill=C["check_sq"], outline="")

        for r, c in self._valid:
            x0, y0, x1, y1 = self._sq_rect(r, c)
            cx_, cy_ = self._sq_center(r, c)
            if g.board[r][c]:
                cv.create_oval(x0 + 3, y0 + 3, x1 - 3, y1 - 3,
                               outline=C["sel"], width=4, fill="")
            else:
                d = 9
                cv.create_oval(cx_ - d, cy_ - d, cx_ + d, cy_ + d,
                               fill=C["sel"], outline="")

        for r in range(8):
            for c in range(8):
                p = g.board[r][c]
                if p:
                    cx_, cy_ = self._sq_center(r, c)
                    fill = "#ffffff" if p[0] == 'w' else "#111111"
                    shd  = "#444444" if p[0] == 'w' else "#999999"
                    cv.create_text(cx_ + 1, cy_ + 2, text=SYMS[p], font=PFONT, fill=shd)
                    cv.create_text(cx_, cy_, text=SYMS[p], font=PFONT, fill=fill)

        for c, ltr in enumerate("abcdefgh"):
            cv.create_text(ML + c * SQ + SQ // 2, MT + 8 * SQ + 10,
                           text=ltr, font=LFONT,
                           fill=C["light"] if c % 2 == 0 else C["dark"])
        for r in range(8):
            cv.create_text(ML // 2, MT + r * SQ + SQ // 2,
                           text=str(8 - r), font=LFONT,
                           fill=C["dark"] if r % 2 == 0 else C["light"])

        sym = "♔" if g.turn == 'w' else "♚"
        name = "Brancas" if g.turn == 'w' else "Pretas"
        self._lbl_turn.configure(text=f"{sym}  {name}")

        status_info = {
            'playing':   ('', C["hint"]),
            'check':     ('Xeque!', C["red"]),
            'checkmate': ('Xeque-mate!', C["red"]),
            'stalemate': ('Empate', C["hint"]),
        }
        txt, clr = status_info.get(st, ('', C["hint"]))
        self._lbl_status.configure(text=txt, text_color=clr)

        if st in ('checkmate', 'stalemate'):
            self._selected = None
            self._valid = []

    def _click(self, event):
        col = (event.x - ML) // SQ
        row = (event.y - MT) // SQ
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        g = self.game
        if g.status() in ('checkmate', 'stalemate'):
            return
        p = g.board[row][col]

        if self._selected:
            if (row, col) in self._valid:
                result, extra = g.make_move(*self._selected, row, col)
                self._selected = None
                self._valid = []
                if result == 'promo':
                    self._refresh()
                    self._do_promotion(*extra)
                else:
                    self._refresh()
                return
            if p and p[0] == g.turn:
                self._selected = (row, col)
                self._valid = g.legal_moves(row, col)
                self._refresh()
                return
            self._selected = None
            self._valid = []
            self._refresh()
            return

        if p and p[0] == g.turn:
            self._selected = (row, col)
            self._valid = g.legal_moves(row, col)
            self._refresh()

    def _do_promotion(self, row, col):
        color = self.game.board[row][col][0]
        dlg = PromotionDialog(self.winfo_toplevel(), color)
        self.wait_window(dlg)
        self.game.finish_promotion(row, col, dlg.choice)
        self._refresh()


# ── main app ────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Xadrez")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.geometry(f"{12 + CW + 12 + 170 + 12}x{12 + CH + 12}")  # 746x564

        self._menu = MenuFrame(self, self._start)
        self._game = GameFrame(self, self._to_menu)
        self._to_menu()

    def _to_menu(self):
        self._game.pack_forget()
        self._menu.pack(fill="both", expand=True)

    def _start(self):
        self._menu.pack_forget()
        self._game.start_new()
        self._game.pack(fill="both", expand=True)


if __name__ == "__main__":
    App().mainloop()
