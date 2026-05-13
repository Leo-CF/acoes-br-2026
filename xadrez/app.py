import sys
import pygame

pygame.init()

# ── layout ──────────────────────────────────────────────────────────────────
SQ    = 64
BX, BY = 16, 16                  # board top-left
SBX   = BX + SQ * 8 + 16        # sidebar left  (= 544)
SBW   = 180                      # sidebar width
WIN_W = SBX + SBW + 12          # 736
WIN_H = BY + SQ * 8 + BY        # 544

# ── colors ───────────────────────────────────────────────────────────────────
C = {
    "bg":       (14,  17,  23),
    "sidebar":  (22,  27,  34),
    "light":    (240, 217, 181),
    "dark":     (181, 136, 99),
    "sel":      (123, 201, 126),
    "check_sq": (230, 57,  70),
    "last":     (205, 209, 110),
    "fg":       (255, 255, 255),
    "hint":     (136, 136, 136),
    "red":      (230, 57,  70),
    "red_hov":  (192, 57,  43),
    "neu":      (30,  34,  42),
    "neu_hov":  (46,  51,  64),
}

SYMS = {
    ('w','K'):'♔', ('w','Q'):'♕', ('w','R'):'♖',
    ('w','B'):'♗', ('w','N'):'♘', ('w','P'):'♙',
    ('b','K'):'♚', ('b','Q'):'♛', ('b','R'):'♜',
    ('b','B'):'♝', ('b','N'):'♞', ('b','P'):'♟',
}


def _font(names, size, bold=False):
    for name in names:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
    return pygame.font.Font(None, size)


# ── chess logic ──────────────────────────────────────────────────────────────

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
        opp  = self._opp(color)
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
        """Returns ('promo', (r,c)) or ('ok', None)."""
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
        chk   = self.in_check(color)
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p[0] == color and self.legal_moves(r, c):
                    return 'check' if chk else 'playing'
        return 'checkmate' if chk else 'stalemate'


# ── app ──────────────────────────────────────────────────────────────────────

class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Xadrez")
        self.clock = pygame.time.Clock()

        chess_names = ["segoeuisymbol", "seguisymbol", "arialunicodems", "notosanssymbols2"]
        ui_names    = ["segoui", "segoeui", "calibri", "arial", "helvetica"]
        self.pf = _font(chess_names, 42)          # piece symbols (large)
        self.sf = _font(chess_names, 18)          # piece symbols (small, sidebar)
        self.uf = _font(ui_names,    14)          # UI text
        self.ub = _font(ui_names,    14, True)    # UI text bold
        self.lf = _font(ui_names,    11)          # board coordinate labels
        self.tf = _font(ui_names,    52, True)    # menu title

        self.state     = "menu"
        self.game      = ChessGame()
        self.selected  = None
        self.valid     = []
        self.promoting = None        # (row, col) while waiting for promo choice
        self._status   = 'playing'  # cached — updated after every move

    # ── main loop ─────────────────────────────────────────────────────────
    def run(self):
        while True:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._handle(event, mouse)
            self.screen.fill(C["bg"])
            self._draw(mouse)
            pygame.display.flip()
            self.clock.tick(60)

    # ── event handling ────────────────────────────────────────────────────
    def _handle(self, event, mouse):
        click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

        if self.state == "menu":
            if click and self._r_start().collidepoint(mouse):
                self._new_game()
            return

        # game state
        if self.promoting:
            if click:
                for pt, rect in self._promo_rects().items():
                    if rect.collidepoint(mouse):
                        self.game.finish_promotion(*self.promoting, pt)
                        self.promoting = None
                        self._status = self.game.status()
                        break
            return

        if click and self._r_new().collidepoint(mouse):
            self._new_game()
        elif click and self._r_menu().collidepoint(mouse):
            self.state = "menu"
        elif click:
            self._board_click(mouse)

    def _new_game(self):
        self.game.reset()
        self.selected  = None
        self.valid     = []
        self.promoting = None
        self._status   = 'playing'
        self.state     = "game"

    def _board_click(self, mouse):
        if self._status in ('checkmate', 'stalemate'):
            return
        col = (mouse[0] - BX) // SQ
        row = (mouse[1] - BY) // SQ
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        g = self.game
        p = g.board[row][col]

        if self.selected:
            if (row, col) in self.valid:
                result, extra = g.make_move(*self.selected, row, col)
                self.selected = None
                self.valid    = []
                if result == 'promo':
                    self.promoting = extra
                else:
                    self._status = g.status()
                return
            if p and p[0] == g.turn:
                self.selected = (row, col)
                self.valid    = g.legal_moves(row, col)
                return
            self.selected = None
            self.valid    = []
            return

        if p and p[0] == g.turn:
            self.selected = (row, col)
            self.valid    = g.legal_moves(row, col)

    # ── button rects ──────────────────────────────────────────────────────
    def _r_start(self):
        return pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 10, 200, 52)

    def _r_new(self):
        return pygame.Rect(SBX + SBW // 2 - 70, BY + SQ * 8 - 96, 140, 36)

    def _r_menu(self):
        return pygame.Rect(SBX + SBW // 2 - 70, BY + SQ * 8 - 52, 140, 36)

    def _promo_rects(self):
        bsz  = 82
        gap  = 8
        pw   = 4 * bsz + 3 * gap + 32
        px   = (WIN_W - pw) // 2
        py   = (WIN_H - 148) // 2
        bx0  = px + 16
        by0  = py + 46
        return {pt: pygame.Rect(bx0 + i * (bsz + gap), by0, bsz, bsz)
                for i, pt in enumerate(['Q', 'R', 'B', 'N'])}

    # ── drawing ───────────────────────────────────────────────────────────
    def _draw(self, mouse):
        if self.state == "menu":
            self._draw_menu(mouse)
        else:
            self._draw_board()
            self._draw_sidebar(mouse)
            if self.promoting:
                self._draw_promo(mouse)

    def _draw_menu(self, mouse):
        t = self.tf.render("Xadrez", True, C["fg"])
        self.screen.blit(t, t.get_rect(center=(WIN_W // 2, WIN_H // 2 - 60)))

        dec = self.sf.render("♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜", True, (55, 62, 75))
        self.screen.blit(dec, dec.get_rect(center=(WIN_W // 2, WIN_H // 2 - 12)))

        sub = self.uf.render("dois jogadores  •  local", True, C["hint"])
        self.screen.blit(sub, sub.get_rect(center=(WIN_W // 2, WIN_H // 2 + 14)))

        self._btn(self._r_start(), "▶  Iniciar Partida", mouse,
                  C["red"], C["red_hov"], bold=True, radius=26)

    def _draw_board(self):
        g        = self.game
        st       = self._status
        last_sqs = set(g.last_move) if g.last_move else set()

        # Squares
        for r in range(8):
            for c in range(8):
                color = C["light"] if (r + c) % 2 == 0 else C["dark"]
                if (r, c) in last_sqs:
                    color = C["last"]
                pygame.draw.rect(self.screen, color,
                                 (BX + c * SQ, BY + r * SQ, SQ, SQ))

        # Selected
        if self.selected:
            r, c = self.selected
            pygame.draw.rect(self.screen, C["sel"],
                             (BX + c * SQ, BY + r * SQ, SQ, SQ))

        # King in check
        if st in ('check', 'checkmate'):
            kp = g._king_pos(g.turn)
            if kp:
                r, c = kp
                pygame.draw.rect(self.screen, C["check_sq"],
                                 (BX + c * SQ, BY + r * SQ, SQ, SQ))

        # Valid-move indicators
        for r, c in self.valid:
            cx_ = BX + c * SQ + SQ // 2
            cy_ = BY + r * SQ + SQ // 2
            if g.board[r][c]:
                pygame.draw.circle(self.screen, C["sel"], (cx_, cy_), SQ // 2 - 3, 4)
            else:
                pygame.draw.circle(self.screen, C["sel"], (cx_, cy_), 9)

        # Pieces (shadow + fill)
        for r in range(8):
            for c in range(8):
                p = g.board[r][c]
                if not p:
                    continue
                cx_ = BX + c * SQ + SQ // 2
                cy_ = BY + r * SQ + SQ // 2
                fill = (255, 255, 255) if p[0] == 'w' else (17,  17,  17)
                shd  = (68,  68,  68)  if p[0] == 'w' else (153, 153, 153)
                for dx, dy, col in ((1, 2, shd), (0, 0, fill)):
                    s = self.pf.render(SYMS[p], True, col)
                    self.screen.blit(s, s.get_rect(center=(cx_ + dx, cy_ + dy)))

        # Coordinate labels (inside squares)
        for c, ltr in enumerate("abcdefgh"):
            col = C["light"] if c % 2 == 0 else C["dark"]
            s   = self.lf.render(ltr, True, col)
            self.screen.blit(s, (BX + (c + 1) * SQ - s.get_width() - 3,
                                 BY + 7 * SQ + SQ - s.get_height() - 3))
        for r in range(8):
            col = C["dark"] if r % 2 == 0 else C["light"]
            s   = self.lf.render(str(8 - r), True, col)
            self.screen.blit(s, (BX + 3, BY + r * SQ + 3))

    def _draw_sidebar(self, mouse):
        pygame.draw.rect(self.screen, C["sidebar"],
                         (SBX, BY, SBW, SQ * 8), border_radius=12)
        cx = SBX + SBW // 2
        g  = self.game

        t = self.ub.render("Xadrez", True, C["fg"])
        self.screen.blit(t, t.get_rect(center=(cx, BY + 28)))

        # Turn: symbol + name side by side
        sym_s  = self.sf.render("♔" if g.turn == 'w' else "♚", True, C["fg"])
        name_s = self.uf.render("Brancas" if g.turn == 'w' else "Pretas", True, C["fg"])
        total  = sym_s.get_width() + 6 + name_s.get_width()
        bx     = cx - total // 2
        mid    = BY + 60
        self.screen.blit(sym_s,  (bx, mid - sym_s.get_height() // 2))
        self.screen.blit(name_s, (bx + sym_s.get_width() + 6,
                                  mid - name_s.get_height() // 2))

        # Status
        st_map = {
            'check':     ("Xeque!",      C["red"]),
            'checkmate': ("Xeque-mate!", C["red"]),
            'stalemate': ("Empate",      C["hint"]),
        }
        if self._status in st_map:
            txt, clr = st_map[self._status]
            s = self.ub.render(txt, True, clr)
            self.screen.blit(s, s.get_rect(center=(cx, BY + 84)))

        self._btn(self._r_new(),  "⟳  Nova Partida", mouse, C["neu"], C["neu_hov"])
        self._btn(self._r_menu(), "←  Menu",          mouse, C["neu"], C["neu_hov"])

    def _draw_promo(self, mouse):
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        self.screen.blit(ov, (0, 0))

        rects = self._promo_rects()
        bsz   = 82
        gap   = 8
        pw    = 4 * bsz + 3 * gap + 32
        ph    = 148
        px    = (WIN_W - pw) // 2
        py    = (WIN_H - ph) // 2

        pygame.draw.rect(self.screen, C["sidebar"], (px, py, pw, ph), border_radius=12)

        t = self.ub.render("Promover peão para:", True, C["fg"])
        self.screen.blit(t, t.get_rect(center=(px + pw // 2, py + 18)))

        color  = self.game.board[self.promoting[0]][self.promoting[1]][0]
        labels = {'Q': 'Dama', 'R': 'Torre', 'B': 'Bispo', 'N': 'Cavalo'}
        for pt, rect in rects.items():
            pygame.draw.rect(self.screen,
                             C["neu_hov"] if rect.collidepoint(mouse) else C["neu"],
                             rect, border_radius=8)
            fill  = (255, 255, 255) if color == 'w' else (17, 17, 17)
            sym_s = self.pf.render(SYMS[(color, pt)], True, fill)
            self.screen.blit(sym_s, sym_s.get_rect(center=(rect.centerx, rect.centery - 8)))
            lbl_s = self.lf.render(labels[pt], True, C["hint"])
            self.screen.blit(lbl_s, lbl_s.get_rect(center=(rect.centerx, rect.bottom - 10)))

    def _btn(self, rect, text, mouse, bg, bg_hov, bold=False, radius=8):
        pygame.draw.rect(self.screen,
                         bg_hov if rect.collidepoint(mouse) else bg,
                         rect, border_radius=radius)
        s = (self.ub if bold else self.uf).render(text, True, C["fg"])
        self.screen.blit(s, s.get_rect(center=rect.center))


if __name__ == "__main__":
    App().run()
